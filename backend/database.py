from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import datetime, os

DATABASE_URL = "sqlite:///./reminders.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def seed_data(db):
    from models import Patient, PatientHistory, Appointment

    if db.query(Patient).count() > 0:
        return  # Already seeded

    now = datetime.datetime.utcnow()

    patients_data = [
        {"name": "Margaret Ellis",   "age": 72, "phone": "+1-555-0101", "email": "m.ellis@email.com"},
        {"name": "Carlos Rivera",    "age": 34, "phone": "+1-555-0102", "email": "c.rivera@email.com"},
        {"name": "Lily Nguyen",      "age": 15, "phone": "+1-555-0103", "email": "nguyen.family@email.com"},
        {"name": "David Okafor",     "age": 58, "phone": "+1-555-0104", "email": "d.okafor@email.com"},
        {"name": "Sarah Thompson",   "age": 41, "phone": "+1-555-0105", "email": "s.thompson@email.com"},
        {"name": "James Whitfield",  "age": 65, "phone": "+1-555-0106", "email": "j.whitfield@email.com"},
        {"name": "Priya Sharma",     "age": 29, "phone": "+1-555-0107", "email": "p.sharma@email.com"},
        {"name": "Robert Chen",      "age": 82, "phone": "+1-555-0108", "email": "r.chen@email.com"},
    ]

    histories_data = [
        {"total_visits": 12, "no_show_count": 1, "missed_last_appointment": True,  "no_show_risk": 75.0},
        {"total_visits": 5,  "no_show_count": 0, "missed_last_appointment": False, "no_show_risk": 10.0},
        {"total_visits": 0,  "no_show_count": 0, "missed_last_appointment": False, "no_show_risk": 20.0},
        {"total_visits": 8,  "no_show_count": 3, "missed_last_appointment": True,  "no_show_risk": 88.0},
        {"total_visits": 3,  "no_show_count": 0, "missed_last_appointment": False, "no_show_risk": 15.0},
        {"total_visits": 20, "no_show_count": 2, "missed_last_appointment": False, "no_show_risk": 60.0},
        {"total_visits": 1,  "no_show_count": 0, "missed_last_appointment": False, "no_show_risk": 5.0},
        {"total_visits": 15, "no_show_count": 4, "missed_last_appointment": True,  "no_show_risk": 92.0},
    ]

    appointments_data = [
        {"type": "Cardiology Visit",        "days": 1},
        {"type": "General Checkup",         "days": 3},
        {"type": "Pediatric Visit",         "days": 2},
        {"type": "Surgery Consultation",    "days": 5},
        {"type": "Routine Follow-up",       "days": 2},
        {"type": "Mental Health Session",   "days": 4},
        {"type": "Telemedicine",            "days": 7},
        {"type": "Cancer Treatment",        "days": 1},
    ]

    patients = []
    for p in patients_data:
        patient = Patient(**p)
        db.add(patient)
        patients.append(patient)
    db.flush()

    for i, h in enumerate(histories_data):
        history = PatientHistory(patient_id=patients[i].id, **h)
        db.add(history)

    for i, a in enumerate(appointments_data):
        appt_dt = now + datetime.timedelta(days=a["days"])
        appointment = Appointment(
            patient_id=patients[i].id,
            appointment_type=a["type"],
            appointment_datetime=appt_dt,
            status="SCHEDULED",
        )
        db.add(appointment)

    db.commit()
