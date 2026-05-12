from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
import datetime


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    phone = Column(String, default="")
    email = Column(String, default="")

    appointments = relationship("Appointment", back_populates="patient")
    history = relationship("PatientHistory", back_populates="patient", uselist=False)


class PatientHistory(Base):
    __tablename__ = "patient_history"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), unique=True)
    total_visits = Column(Integer, default=0)
    no_show_count = Column(Integer, default=0)
    missed_last_appointment = Column(Boolean, default=False)
    no_show_risk = Column(Float, default=0.0)  # 0-100

    patient = relationship("Patient", back_populates="history")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    appointment_type = Column(String, nullable=False)
    appointment_datetime = Column(DateTime, nullable=False)
    status = Column(String, default="SCHEDULED")  # SCHEDULED, COMPLETED, CANCELLED
    notes = Column(Text, default="")

    patient = relationship("Patient", back_populates="appointments")
    reminder = relationship("ReminderQueue", back_populates="appointment", uselist=False, cascade="all, delete-orphan")


class ReminderQueue(Base):
    __tablename__ = "reminder_queue"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), unique=True)
    channel = Column(String, nullable=False)   # SMS, EMAIL, PHONE_CALL
    message = Column(Text, nullable=False)
    edited_message = Column(Text, default="")
    reasoning = Column(Text, default="")       # JSON array of reason strings
    status = Column(String, default="PENDING") # PENDING, APPROVED, DISPATCHED
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    dispatched_at = Column(DateTime, nullable=True)

    appointment = relationship("Appointment", back_populates="reminder")
