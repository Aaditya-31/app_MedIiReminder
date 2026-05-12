import os
import json
import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

from database import engine, SessionLocal, get_db, seed_data, Base
import models
from models import Patient, PatientHistory, Appointment, ReminderQueue
from schemas import (
    AppointmentCreate, AppointmentOut, ReminderQueueOut,
    EditReminderRequest, AppointmentStatusUpdate
)
from agent import process_all_appointments
from chatbot import chat as ai_chat

# ─── Init DB ─────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_data(db)
    finally:
        db.close()
    yield

# ─── AI Clients ──────────────────────────────────────────────────────────────
groq_api_key = os.getenv("GROQ_API_KEY", "")
llm_model = os.getenv("LLM_MODEL", "qwen/qwen3-32b")
ai_client = Groq(api_key=groq_api_key) if groq_api_key else None

# ─── App ─────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MediReminder AI Reminder Platform", 
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Appointments ─────────────────────────────────────────────────────────────

@app.get("/api/appointments")
def list_appointments(db: Session = Depends(get_db)):
    appointments = db.query(Appointment).all()
    result = []
    for appt in appointments:
        patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
        if not patient:
            continue # Skip or handle orphaned appointments
        history = db.query(PatientHistory).filter(PatientHistory.patient_id == patient.id).first()
        result.append({
            "id": appt.id,
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "phone": patient.phone,
                "email": patient.email,
            },
            "appointment_type": appt.appointment_type,
            "appointment_datetime": appt.appointment_datetime.isoformat(),
            "status": appt.status,
            "history": {
                "total_visits": history.total_visits if history else 0,
                "no_show_count": history.no_show_count if history else 0,
                "missed_last_appointment": history.missed_last_appointment if history else False,
                "no_show_risk": history.no_show_risk if history else 0.0,
            } if history else None,
        })
    return result


@app.post("/api/appointments", status_code=201)
def create_appointment(payload: AppointmentCreate, db: Session = Depends(get_db)):
    print(f"DEBUG: Received appointment creation payload: {payload.dict()}")
    # Create patient
    patient = Patient(
        name=payload.patient_name,
        age=payload.patient_age,
        phone=payload.patient_phone,
        email=payload.patient_email,
    )
    db.add(patient)
    db.flush()

    # Calculate initial risk for new patients based on age and appointment type
    initial_risk = 20.0
    if payload.patient_age >= 65:
        initial_risk += 28.0
    
    # Critical types that increase initial risk
    high_stakes = ["Surgery Consultation", "Cancer Treatment", "Cardiology Visit", "Mental Health Session"]
    if payload.appointment_type in high_stakes:
        initial_risk += 40.0

    history = PatientHistory(
        patient_id=patient.id,
        total_visits=payload.total_visits,
        no_show_count=payload.no_show_count,
        missed_last_appointment=False,
        no_show_risk=initial_risk,
    )
    db.add(history)

    # Create appointment
    appt = Appointment(
        patient_id=patient.id,
        appointment_type=payload.appointment_type,
        appointment_datetime=payload.appointment_datetime,
        status="SCHEDULED",
    )
    db.add(appt)

    db.commit()
    db.refresh(appt)

    return {"id": appt.id, "patient_id": patient.id, "message": "Appointment created successfully"}


@app.patch("/api/appointments/{appointment_id}/status")
def update_appointment_status(appointment_id: int, payload: AppointmentStatusUpdate, db: Session = Depends(get_db)):
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appt.status != "SCHEDULED":
        raise HTTPException(status_code=400, detail=f"Cannot update status of appointment already in {appt.status} state")

    new_status = payload.status.upper()
    if new_status not in ["COMPLETED", "NO_SHOW", "CANCELLED"]:
        raise HTTPException(status_code=400, detail="Invalid status. Use COMPLETED, NO_SHOW, or CANCELLED")

    appt.status = new_status
    
    # Update patient history
    history = db.query(PatientHistory).filter(PatientHistory.patient_id == appt.patient_id).first()
    if history:
        if new_status == "COMPLETED":
            history.total_visits += 1
            history.missed_last_appointment = False
        elif new_status == "NO_SHOW":
            history.no_show_count += 1
            history.missed_last_appointment = True
            
        # Optional: Recalculate risk (internal only)
        # We'll just keep the existing risk logic or simplify it
        # Since the user wants to remove it from frontend, we don't strictly need to update it here
        # but it's good for the AI's internal state.

    db.commit()
    return {"id": appointment_id, "status": new_status}


@app.delete("/api/appointments/{appointment_id}")
def delete_appointment(appointment_id: int, db: Session = Depends(get_db)):
    print(f"DEBUG: Attempting to delete appointment {appointment_id}")
    appt = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appt:
        print(f"DEBUG: Appointment {appointment_id} not found")
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    try:
        # Manually delete associated reminders if they exist
        reminder = db.query(ReminderQueue).filter(ReminderQueue.appointment_id == appointment_id).first()
        if reminder:
            db.delete(reminder)
            print(f"DEBUG: Associated reminder for appointment {appointment_id} deleted")
            
        db.delete(appt)
        db.commit()
        print(f"DEBUG: Appointment {appointment_id} deleted successfully")
    except Exception as e:
        db.rollback()
        print(f"DEBUG: Error deleting appointment {appointment_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"id": appointment_id, "message": "Appointment deleted successfully"}


# ─── Reminder Queue ───────────────────────────────────────────────────────────

@app.get("/api/queue")
def get_queue(db: Session = Depends(get_db)):
    reminders = db.query(ReminderQueue).all()
    result = []
    for r in reminders:
        appt = db.query(Appointment).filter(Appointment.id == r.appointment_id).first()
        patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
        history = db.query(PatientHistory).filter(PatientHistory.patient_id == patient.id).first()

        try:
            reasoning_list = json.loads(r.reasoning) if r.reasoning else []
        except Exception:
            reasoning_list = [r.reasoning]

        result.append({
            "id": r.id,
            "appointment_id": r.appointment_id,
            "channel": r.channel,
            "message": r.message,
            "edited_message": r.edited_message,
            "reasoning": reasoning_list,
            "status": r.status,
            "created_at": r.created_at.isoformat(),
            "dispatched_at": r.dispatched_at.isoformat() if r.dispatched_at else None,
            "appointment": {
                "id": appt.id,
                "appointment_type": appt.appointment_type,
                "appointment_datetime": appt.appointment_datetime.isoformat(),
                "status": appt.status,
            },
            "patient": {
                "id": patient.id,
                "name": patient.name,
                "age": patient.age,
                "phone": patient.phone,
                "email": patient.email,
            },
            "history": {
                "total_visits": history.total_visits if history else 0,
                "no_show_count": history.no_show_count if history else 0,
                "missed_last_appointment": history.missed_last_appointment if history else False,
                "no_show_risk": history.no_show_risk if history else 0.0,
            } if history else None,
        })
    return result


@app.post("/api/run-agent")
def run_agent(db: Session = Depends(get_db)):
    if not ai_client:
        raise HTTPException(status_code=500, detail="Groq API key not configured")
    
    results = process_all_appointments(db, ai_client, llm_model)
    return {"processed": len(results), "results": results}


@app.patch("/api/queue/{reminder_id}/approve")
def approve_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(ReminderQueue).filter(ReminderQueue.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.status == "DISPATCHED":
        raise HTTPException(status_code=400, detail="Already dispatched")
    reminder.status = "APPROVED"
    db.commit()
    return {"id": reminder_id, "status": "APPROVED"}


@app.patch("/api/queue/{reminder_id}/edit")
def edit_reminder(reminder_id: int, payload: EditReminderRequest, db: Session = Depends(get_db)):
    reminder = db.query(ReminderQueue).filter(ReminderQueue.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.status == "DISPATCHED":
        raise HTTPException(status_code=400, detail="Cannot edit a dispatched reminder")
    reminder.edited_message = payload.edited_message
    db.commit()
    return {"id": reminder_id, "edited_message": payload.edited_message}


@app.post("/api/queue/{reminder_id}/dispatch")
def dispatch_reminder(reminder_id: int, db: Session = Depends(get_db)):
    reminder = db.query(ReminderQueue).filter(ReminderQueue.id == reminder_id).first()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    if reminder.status == "DISPATCHED":
        raise HTTPException(status_code=400, detail="Already dispatched")
    reminder.status = "DISPATCHED"
    reminder.dispatched_at = datetime.datetime.utcnow()
    db.commit()
    return {"id": reminder_id, "status": "DISPATCHED", "dispatched_at": reminder.dispatched_at.isoformat()}


# ─── Chatbot ──────────────────────────────────────────────────────────────────

@app.post("/api/chat")
async def chat_endpoint(payload: dict, db: Session = Depends(get_db)):
    if not ai_client:
        raise HTTPException(status_code=500, detail="Groq API key not configured")
    
    messages = payload.get("messages", [])
    reply = ai_chat(messages, db, ai_client, llm_model)
    return {"reply": reply}


# ─── Health ───────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "ai_configured": bool(groq_api_key),
        "model": llm_model,
        "timestamp": datetime.datetime.utcnow().isoformat()
    }
