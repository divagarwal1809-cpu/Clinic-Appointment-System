import datetime
import uuid
from sqlalchemy import create_engine, Column, String, Date, Time, DateTime, Boolean, Float, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

import os

DATABASE_URL = os.environ.get("DATABASE_URL") or "postgresql://neondb_owner:npg_s5BOH4vuNAWZ@ep-dawn-art-aosh50nx.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require"

# Neon/Render URLs might start with postgres://, SQLAlchemy requires postgresql://
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())

class Patient(Base):
    __tablename__ = "patients"

    patient_id = Column(String, primary_key=True, default=generate_uuid)
    full_name = Column(String, nullable=False)
    dob = Column(String, nullable=False)  # Stored as YYYY-MM-DD
    gender = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    email = Column(String, nullable=False)
    address = Column(String, nullable=False)
    emergency_contact_name = Column(String, nullable=False)
    emergency_contact_phone = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    appointments = relationship("Appointment", back_populates="patient", cascade="all, delete-orphan")
    intake_forms = relationship("IntakeForm", back_populates="patient", cascade="all, delete-orphan")
    followups = relationship("FollowUp", back_populates="patient", cascade="all, delete-orphan")

class Appointment(Base):
    __tablename__ = "appointments"

    appointment_id = Column(String, primary_key=True, default=generate_uuid)
    patient_id = Column(String, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    clinician_name = Column(String, nullable=False)
    department = Column(String, nullable=False)
    appointment_date = Column(String, nullable=False)  # YYYY-MM-DD
    appointment_time = Column(String, nullable=False)  # HH:MM
    status = Column(String, default="requested")  # requested/confirmed/checked_in/completed/cancelled/no_show
    reason_for_visit = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    patient = relationship("Patient", back_populates="appointments")
    intake_forms = relationship("IntakeForm", back_populates="appointment", cascade="all, delete-orphan")
    followups = relationship("FollowUp", back_populates="appointment", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="appointment", cascade="all, delete-orphan")

class IntakeForm(Base):
    __tablename__ = "intake_forms"

    intake_id = Column(String, primary_key=True, default=generate_uuid)
    appointment_id = Column(String, ForeignKey("appointments.appointment_id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    symptoms_description = Column(Text, nullable=True)
    current_medications = Column(Text, nullable=True)
    allergies = Column(Text, nullable=True)
    insurance_provider = Column(String, nullable=True)
    insurance_id = Column(String, nullable=True)
    preferred_language = Column(String, nullable=True)
    consent_given = Column(Boolean, default=False)
    submitted_at = Column(DateTime, default=datetime.datetime.utcnow)
    ai_summary = Column(Text, nullable=True)
    missing_fields = Column(Text, default="[]")  # JSON string array
    completeness_score = Column(Float, default=0.0)
    urgent_review_needed = Column(Boolean, default=False)

    appointment = relationship("Appointment", back_populates="intake_forms")
    patient = relationship("Patient", back_populates="intake_forms")

class FollowUp(Base):
    __tablename__ = "followups"

    followup_id = Column(String, primary_key=True, default=generate_uuid)
    appointment_id = Column(String, ForeignKey("appointments.appointment_id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(String, ForeignKey("patients.patient_id", ondelete="CASCADE"), nullable=False)
    followup_type = Column(String, nullable=False)  # missing_info_request/appointment_reminder/post_visit_check
    message_draft = Column(Text, nullable=True)
    status = Column(String, default="draft")  # draft/approved/sent/acknowledged
    scheduled_send_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    appointment = relationship("Appointment", back_populates="followups")
    patient = relationship("Patient", back_populates="followups")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(String, ForeignKey("appointments.appointment_id", ondelete="CASCADE"), nullable=False)
    action = Column(String, nullable=False)  # e.g., status_change
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    changed_by = Column(String, default="system")
    changed_at = Column(DateTime, default=datetime.datetime.utcnow)

    appointment = relationship("Appointment", back_populates="audit_logs")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
