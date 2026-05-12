"""
AI Agent — uses Groq/OpenAI tool calling to fetch patient data,
runs rule-based logic, then drafts reminder message via LLM.
"""
import json
import datetime
import re
from sqlalchemy.orm import Session

from reminder_logic import decide_channel
from models import Patient, PatientHistory, Appointment, ReminderQueue

# ─── Utils ───────────────────────────────────────────────────────────────────

def clean_message_text(text: str) -> str:
    """Removes <think> blocks, markdown asterisks, and brackets from AI output."""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Remove markdown bold/italic
    text = text.replace('**', '').replace('*', '')
    # Remove any remaining brackets that might contain placeholders
    text = re.sub(r'\[.*?\]', '', text)
    return text.strip()

# ─── Tool definitions ────────────────────────────────────────────────────────

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_patient_history",
            "description": "Fetch a patient's visit history, no-show record, and risk score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "patient_id": {
                        "type": "integer",
                        "description": "The unique ID of the patient."
                    }
                },
                "required": ["patient_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_appointment_details",
            "description": "Fetch details about a specific appointment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "integer",
                        "description": "The unique ID of the appointment."
                    }
                },
                "required": ["appointment_id"]
            }
        }
    }
]


def get_patient_history_tool(patient_id: int, db: Session) -> dict:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    history = db.query(PatientHistory).filter(PatientHistory.patient_id == patient_id).first()
    if not patient:
        return {"error": "Patient not found"}
    return {
        "patient_id": patient.id,
        "name": patient.name,
        "age": patient.age,
        "total_visits": history.total_visits if history else 0,
        "no_show_count": history.no_show_count if history else 0,
        "missed_last_appointment": history.missed_last_appointment if history else False,
        "no_show_risk": history.no_show_risk if history else 0.0,
    }


def get_appointment_details_tool(appointment_id: int, db: Session) -> dict:
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        return {"error": "Appointment not found"}
    return {
        "appointment_id": appt.id,
        "patient_id": appt.patient_id,
        "appointment_type": appt.appointment_type,
        "appointment_datetime": appt.appointment_datetime.isoformat(),
        "status": appt.status,
    }


def draft_template_message(channel: str, patient_name: str, patient_age: int,
                            appointment_type: str, appt_time: str) -> str:
    if channel == "SMS":
        return f"Reminder: Hi {patient_name}, your {appointment_type} is scheduled for {appt_time}. Please confirm or call us to reschedule."
    elif channel == "EMAIL":
        return f"Subject: Appointment Reminder — {appointment_type}\n\nDear {patient_name},\n\nFriendly reminder for your {appointment_type} on {appt_time}."
    else:
        return f"Hello {patient_name}, calling to confirm your {appointment_type} on {appt_time}."


def run_agent_for_appointment(appointment_id: int, db: Session, client, model: str) -> dict:
    # ─── Data fetch ───
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
    history = db.query(PatientHistory).filter(PatientHistory.patient_id == patient.id).first()

    # ─── Decision logic ───
    rule_result = decide_channel(
        patient_age=patient.age,
        appointment_type=appt.appointment_type,
        appointment_datetime=appt.appointment_datetime,
        total_visits=history.total_visits if history else 0,
        no_show_count=history.no_show_count if history else 0,
        missed_last_appointment=history.missed_last_appointment if history else False,
        no_show_risk=history.no_show_risk if history else 0.0,
    )

    channel = rule_result["channel"]
    reasoning = rule_result["reasoning"]
    priority = rule_result["priority"]
    appt_time = appt.appointment_datetime.strftime("%A, %B %d at %I:%M %p")

    # ─── LLM Inference (Groq) ───
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a professional medical assistant representing 'Medi Clinic'.\n\nRULES:\n1. Draft a warm, concise reminder message.\n2. Do NOT use ANY placeholders (like [Name], [Clinic], etc.). Use 'Medi Clinic' as the clinic name, and '1-800-555-0199' as the contact number.\n3. Always sign off EXACTLY as: 'From the Medi Clinic team'.\n4. Do NOT use markdown formatting (no asterisks, no bold text).\n5. Never include <think> tags."},
                {"role": "user", "content": f"Draft a {channel} reminder for {patient.name} for their {appt.appointment_type} on {appt_time}."}
            ],
            temperature=0.7,
        )
        message_text = clean_message_text(response.choices[0].message.content)
        used_llm = True
    except Exception as e:
        print(f"DEBUG: Groq Error: {str(e)}")
        message_text = draft_template_message(channel, patient.name, patient.age, appt.appointment_type, appt_time)
        used_llm = False

    return {
        "channel": channel,
        "message": message_text,
        "reasoning": reasoning,
        "priority": priority,
        "used_llm": used_llm,
    }


def process_all_appointments(db: Session, client, model: str) -> list:
    appointments = db.query(Appointment).filter(Appointment.status == "SCHEDULED").all()
    results = []
    for appt in appointments:
        existing = db.query(ReminderQueue).filter(ReminderQueue.appointment_id == appt.id).first()
        if existing: continue
        try:
            result = run_agent_for_appointment(appt.id, db, client, model)
            reminder = ReminderQueue(
                appointment_id=appt.id, channel=result["channel"],
                message=result["message"], reasoning=json.dumps(result["reasoning"]),
                status="PENDING",
            )
            db.add(reminder)
            db.commit()
            results.append({"appointment_id": appt.id, "status": "created", "channel": result["channel"]})
        except Exception as e:
            results.append({"appointment_id": appt.id, "status": "error", "error": str(e)})
    return results
