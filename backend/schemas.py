from pydantic import BaseModel
from typing import Optional, List
import datetime


class PatientOut(BaseModel):
    id: int
    name: str
    age: int
    phone: str
    email: str

    class Config:
        from_attributes = True


class PatientHistoryOut(BaseModel):
    total_visits: int
    no_show_count: int
    missed_last_appointment: bool
    no_show_risk: float

    class Config:
        from_attributes = True


class AppointmentCreate(BaseModel):
    patient_name: str
    patient_age: int
    patient_phone: str = ""
    patient_email: str = ""
    appointment_type: str
    appointment_datetime: datetime.datetime
    total_visits: int = 0
    no_show_count: int = 0


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    appointment_type: str
    appointment_datetime: datetime.datetime
    status: str
    patient: PatientOut

    class Config:
        from_attributes = True


class ReminderQueueOut(BaseModel):
    id: int
    appointment_id: int
    channel: str
    message: str
    edited_message: str
    reasoning: str   # JSON string
    status: str
    created_at: datetime.datetime
    dispatched_at: Optional[datetime.datetime]
    appointment: AppointmentOut

    class Config:
        from_attributes = True


class EditReminderRequest(BaseModel):
    edited_message: str




class AppointmentStatusUpdate(BaseModel):
    status: str
