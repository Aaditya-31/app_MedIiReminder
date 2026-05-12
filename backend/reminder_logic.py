"""
Appointment Reminder Channel Decision Engine
4-Step Rule-Based Logic (as specified in SKORE requirements)
"""

import datetime
from typing import Optional

CRITICAL_TYPES = [
    "Surgery Consultation",
    "Mental Health Session",
    "Cancer Treatment",
    "Cardiology Visit",
    "Emergency Follow-up",
]

MODERATE_TYPES = [
    "Specialist Consultation",
    "Telemedicine",
    "Pediatric Visit",
]

SIMPLE_TYPES = [
    "General Checkup",
    "Dental Cleaning",
    "Vaccination",
    "Physiotherapy",
    "Routine Follow-up",
]


def decide_channel(
    patient_age: int,
    appointment_type: str,
    appointment_datetime: datetime.datetime,
    total_visits: int,
    no_show_count: int,
    missed_last_appointment: bool,
    no_show_risk: float,
) -> dict:
    """
    Returns:
        {
            "channel": "SMS" | "EMAIL" | "PHONE_CALL",
            "reasoning": ["reason 1", "reason 2", ...],
            "priority": "NORMAL" | "HIGH"
        }
    """
    reasoning = []
    channel = "SMS"  # default fallback
    priority = "NORMAL"

    now = datetime.datetime.utcnow()
    hours_until_appt = (appointment_datetime - now).total_seconds() / 3600
    within_24h = 0 < hours_until_appt <= 24

    # ─── STEP 4 PRIORITY OVERRIDES (checked first) ───────────────────────────

    # Override: High no-show risk
    if no_show_risk > 80:
        channel = "PHONE_CALL"
        priority = "HIGH"
        reasoning.append(f"No-show risk score is critically high ({no_show_risk:.0f}/100) — phone call required")

    # Override: Appointment within 24 hours → SMS for immediate visibility
    if within_24h:
        channel = "SMS"
        reasoning.append(
            f"Appointment is within 24 hours ({hours_until_appt:.1f}h away) — SMS for immediate visibility"
        )

    # Override: Multiple high-risk flags → PHONE_CALL + HIGH
    elderly = patient_age >= 60
    critical_type = appointment_type in CRITICAL_TYPES
    missed = missed_last_appointment
    if elderly and critical_type and missed:
        channel = "PHONE_CALL"
        priority = "HIGH"
        reasoning.append("Multiple high-risk flags: elderly patient + critical appointment type + missed last appointment → HIGH priority phone call")
        return {"channel": channel, "reasoning": reasoning, "priority": priority}

    # ─── STEP 1 — Appointment Type (Priority 2) ──────────────────────────────────
    if channel != "PHONE_CALL":
        if appointment_type in CRITICAL_TYPES:
            channel = "PHONE_CALL"
            reasoning.append(f"Appointment type '{appointment_type}' is critical — Priority: Phone Call")
        elif appointment_type in MODERATE_TYPES:
            channel = "EMAIL"
            reasoning.append(f"Appointment type '{appointment_type}' requires detailed instructions — Priority: Email")
        elif appointment_type in SIMPLE_TYPES:
            channel = "SMS"
            reasoning.append(f"Appointment type '{appointment_type}' is routine — Priority: SMS")

    # ─── STEP 2 — Visit History (Priority 3) ─────────────────────────────────────
    if no_show_count >= 2:
        channel = "PHONE_CALL"
        priority = "HIGH"
        reasoning.append(f"Patient has {no_show_count} prior no-shows — Elevated priority: Phone Call")
    elif missed_last_appointment:
        if channel != "PHONE_CALL":
            channel = "PHONE_CALL"
        reasoning.append("Patient missed their last appointment — Increased no-show probability")
    elif total_visits == 0:
        if channel == "SMS":
            reasoning.append("Patient is new, but routine appointment type maintains SMS priority for convenience.")
        else:
            if channel != "PHONE_CALL":
                channel = "EMAIL"
            reasoning.append("New patient onboarding — Email preferred for clinic instructions")

    # ─── STEP 3 — Age (Priority 4) ──────────────────────────────────────────────
    if channel not in ["PHONE_CALL", "EMAIL"]: # Only if SMS or undecided
        if patient_age >= 60:
            channel = "PHONE_CALL"
            reasoning.append(f"Elderly patient ({patient_age}) — Phone call preferred for reliability")
        elif patient_age < 18:
            channel = "EMAIL"
            reasoning.append(f"Minor patient ({patient_age}) — Email preferred for guardian communication")
        else:
            reasoning.append(f"Adult patient ({patient_age}) — SMS remains the most responsive channel")
    else:
        if patient_age >= 60 and channel == "PHONE_CALL":
            reasoning.append(f"Age {patient_age} confirms Phone Call selection")
        elif patient_age < 18 and channel == "EMAIL":
            reasoning.append(f"Age {patient_age} confirms Email selection")

    return {
        "channel": channel,
        "reasoning": reasoning,
        "priority": priority,
    }

