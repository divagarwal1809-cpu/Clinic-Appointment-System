from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

# Patient Schemas
class PatientBase(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    dob: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    gender: Optional[str] = Field(None, max_length=30)
    phone: str = Field(..., min_length=5, max_length=30)
    email: str = Field(..., min_length=5, max_length=150)
    address: str = Field(..., max_length=300)
    emergency_contact_name: str = Field(..., max_length=100)
    emergency_contact_phone: str = Field(..., max_length=30)

class PatientCreate(PatientBase):
    pass

class PatientResponse(PatientBase):
    patient_id: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

# Appointment Schemas
class AppointmentBase(BaseModel):
    clinician_name: str = Field(..., max_length=150)
    department: str = Field(..., max_length=100)
    appointment_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    appointment_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")         # HH:MM
    reason_for_visit: str = Field(..., max_length=500)

class AppointmentCreate(AppointmentBase):
    patient_id: str = Field(..., max_length=50)

class AppointmentResponse(AppointmentBase):
    appointment_id: str
    patient_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    patient: Optional[PatientResponse] = None

    model_config = {
        "from_attributes": True
    }

class AppointmentStatusUpdate(BaseModel):
    status: str = Field(..., max_length=30)
    changed_by: Optional[str] = Field("staff", max_length=100)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"requested", "confirmed", "checked_in", "completed", "cancelled", "no_show"}
        if v not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return v

# Intake Form Schemas
class IntakeFormCreate(BaseModel):
    appointment_id: str = Field(..., max_length=50)
    patient_id: str = Field(..., max_length=50)
    symptoms_description: str = Field(..., min_length=1, max_length=2000)
    current_medications: Optional[str] = Field("", max_length=500)
    allergies: Optional[str] = Field("", max_length=500)
    insurance_provider: Optional[str] = Field("", max_length=150)
    insurance_id: Optional[str] = Field("", max_length=100)
    preferred_language: Optional[str] = Field("English", max_length=50)
    consent_given: bool

class IntakeFormResponse(BaseModel):
    intake_id: str
    appointment_id: str
    patient_id: str
    symptoms_description: Optional[str] = None
    current_medications: Optional[str] = None
    allergies: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_id: Optional[str] = None
    preferred_language: Optional[str] = None
    consent_given: bool
    submitted_at: datetime
    ai_summary: Optional[str] = None
    missing_fields: List[str]
    completeness_score: float
    urgent_review_needed: bool

    model_config = {
        "from_attributes": True
    }

# FollowUp Schemas
class FollowUpBase(BaseModel):
    appointment_id: str = Field(..., max_length=50)
    patient_id: str = Field(..., max_length=50)
    followup_type: str = Field(..., max_length=60)  # missing_info_request/appointment_reminder/post_visit_check
    message_draft: Optional[str] = Field(None, max_length=3000)
    status: str = Field(..., max_length=30)          # draft/approved/sent/acknowledged
    scheduled_send_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

class FollowUpResponse(FollowUpBase):
    followup_id: str
    patient: Optional[PatientResponse] = None

    model_config = {
        "from_attributes": True
    }

class FollowUpStatusUpdate(BaseModel):
    status: str = Field(..., max_length=30)
    message_draft: Optional[str] = Field(None, max_length=3000)

# Audit Log Schema
class AuditLogResponse(BaseModel):
    log_id: int
    appointment_id: str
    action: str
    old_status: Optional[str] = None
    new_status: str
    changed_by: str
    changed_at: datetime

    model_config = {
        "from_attributes": True
    }

# Dashboard Summary Schema
class DashboardSummaryResponse(BaseModel):
    today_appointments: List[AppointmentResponse]
    incomplete_intakes_count: int
    pending_followups_count: int
    pending_followups: List[FollowUpResponse]
    recent_audit_logs: List[AuditLogResponse]

class CombinedBookingRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    dob: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    phone: str = Field(..., min_length=5, max_length=30)
    email: str = Field(..., min_length=5, max_length=150)
    department: str = Field(..., max_length=100)
    appointment_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    appointment_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")         # HH:MM
    clinician_name: Optional[str] = Field("To be assigned", max_length=150)
    symptoms_description: str = Field(..., min_length=1, max_length=2000)
    current_medications: Optional[str] = Field("", max_length=500)
    allergies: Optional[str] = Field("", max_length=500)
    insurance_provider: Optional[str] = Field("", max_length=150)
    insurance_id: Optional[str] = Field("", max_length=100)
    preferred_language: Optional[str] = Field("English", max_length=50)
    consent_given: bool
