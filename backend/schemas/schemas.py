from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# Patient Schemas
class PatientBase(BaseModel):
    full_name: str
    dob: str  # YYYY-MM-DD
    gender: Optional[str] = None
    phone: str
    email: str
    address: str
    emergency_contact_name: str
    emergency_contact_phone: str

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
    clinician_name: str
    department: str
    appointment_date: str  # YYYY-MM-DD
    appointment_time: str  # HH:MM
    reason_for_visit: str

class AppointmentCreate(AppointmentBase):
    patient_id: str

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
    status: str
    changed_by: Optional[str] = "staff"

# Intake Form Schemas
class IntakeFormCreate(BaseModel):
    appointment_id: str
    patient_id: str
    symptoms_description: str
    current_medications: Optional[str] = ""
    allergies: Optional[str] = ""
    insurance_provider: Optional[str] = ""
    insurance_id: Optional[str] = ""
    preferred_language: Optional[str] = "English"
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
    appointment_id: str
    patient_id: str
    followup_type: str  # missing_info_request/appointment_reminder/post_visit_check
    message_draft: Optional[str] = None
    status: str  # draft/approved/sent/acknowledged
    scheduled_send_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None

class FollowUpResponse(FollowUpBase):
    followup_id: str
    patient: Optional[PatientResponse] = None

    model_config = {
        "from_attributes": True
    }

class FollowUpStatusUpdate(BaseModel):
    status: str
    message_draft: Optional[str] = None

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
    full_name: str
    dob: str  # YYYY-MM-DD
    phone: str
    email: str
    department: str
    appointment_date: str  # YYYY-MM-DD
    appointment_time: str  # HH:MM
    clinician_name: Optional[str] = "To be assigned"
    symptoms_description: str
    current_medications: Optional[str] = ""
    allergies: Optional[str] = ""
    insurance_provider: Optional[str] = ""
    insurance_id: Optional[str] = ""
    preferred_language: Optional[str] = "English"
    consent_given: bool

