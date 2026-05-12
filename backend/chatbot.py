"""
AI Chatbot — supports Groq and OpenAI.
"""
import datetime
import re
from sqlalchemy.orm import Session
from models import Patient, Appointment, ReminderQueue, PatientHistory


def clean_message_text(text: str) -> str:
    """Removes <think> blocks, markdown asterisks, and brackets from AI output."""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    return text.strip()


def build_system_context(db: Session) -> str:
    now = datetime.datetime.utcnow()
    appointments = db.query(Appointment).filter(Appointment.status == "SCHEDULED").all()
    context = [f"Today is {now.strftime('%A, %B %d, %Y')}. You are a medical assistant chatbot.", "=== DATA ==="]
    for appt in appointments:
        patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
        context.append(f"- {patient.name} (Age {patient.age}): {appt.appointment_type} on {appt.appointment_datetime.strftime('%b %d')}")
    return "\n".join(context)


def chat(messages: list, db: Session, client, model: str) -> str:
    system_context = build_system_context(db)
    full_messages = [{"role": "system", "content": system_context}] + messages

    try:
        response = client.chat.completions.create(
            model=model,
            messages=full_messages,
            temperature=0.5,
            max_tokens=800,
        )
        return clean_message_text(response.choices[0].message.content)
    except Exception as e:
        return f"⚠️ [AI Assistant] Groq Error: {str(e)}. Please check your API keys."
