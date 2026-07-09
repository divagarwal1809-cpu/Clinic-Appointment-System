import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.models.database import get_db, Appointment, Patient, AuditLog, IntakeForm
from backend.schemas.schemas import AppointmentCreate, AppointmentResponse, AppointmentStatusUpdate, IntakeFormResponse, CombinedBookingRequest
import json

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(app_data: AppointmentCreate, db: Session = Depends(get_db)):
    # Verify patient exists
    patient = db.query(Patient).filter(Patient.patient_id == app_data.patient_id).first()
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found"
        )
        
    db_appointment = Appointment(
        patient_id=app_data.patient_id,
        clinician_name=app_data.clinician_name,
        department=app_data.department,
        appointment_date=app_data.appointment_date,
        appointment_time=app_data.appointment_time,
        reason_for_visit=app_data.reason_for_visit,
        status="requested"
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    # Log initial status
    log = AuditLog(
        appointment_id=db_appointment.appointment_id,
        action="status_change",
        old_status=None,
        new_status="requested",
        changed_by="patient"
    )
    db.add(log)
    db.commit()
    
    return db_appointment

@router.post("/book-with-intake", response_model=AppointmentResponse, status_code=status.HTTP_201_CREATED)
def book_appointment_with_intake(data: CombinedBookingRequest, db: Session = Depends(get_db)):
    # 1. Check if patient already exists by email or name + DOB
    patient = db.query(Patient).filter(
        (Patient.email == data.email) | 
        ((Patient.full_name == data.full_name) & (Patient.dob == data.dob))
    ).first()
    
    if not patient:
        # Create new patient
        patient = Patient(
            full_name=data.full_name,
            dob=data.dob,
            phone=data.phone,
            email=data.email,
            address="N/A", # Simplified details
            emergency_contact_name="N/A",
            emergency_contact_phone="N/A"
        )
        db.add(patient)
        db.commit()
        db.refresh(patient)
        
    # 2. Create appointment
    db_appointment = Appointment(
        patient_id=patient.patient_id,
        clinician_name=data.clinician_name or "To be assigned",
        department=data.department,
        appointment_date=data.appointment_date,
        appointment_time=data.appointment_time,
        reason_for_visit=data.symptoms_description,
        status="requested"
    )
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    # 3. Create AuditLog
    log = AuditLog(
        appointment_id=db_appointment.appointment_id,
        action="status_change",
        old_status=None,
        new_status="requested",
        changed_by="patient"
    )
    db.add(log)
    
    # 4. Check Intake Completeness
    required_keys = [
        "symptoms_description", 
        "current_medications", 
        "allergies", 
        "insurance_provider", 
        "insurance_id", 
        "preferred_language"
    ]
    missing = []
    filled_count = 0
    
    intake_dict = data.model_dump()
    for key in required_keys:
        val = intake_dict.get(key)
        if not val or (isinstance(val, str) and val.strip().lower() in ["", "none", "n/a"]):
            missing.append(key)
        else:
            filled_count += 1
            
    completeness = filled_count / len(required_keys)
    
    # 5. Create IntakeForm
    db_intake = IntakeForm(
        appointment_id=db_appointment.appointment_id,
        patient_id=patient.patient_id,
        symptoms_description=data.symptoms_description,
        current_medications=data.current_medications,
        allergies=data.allergies,
        insurance_provider=data.insurance_provider,
        insurance_id=data.insurance_id,
        preferred_language=data.preferred_language,
        consent_given=data.consent_given,
        completeness_score=completeness,
        missing_fields=json.dumps(missing),
        urgent_review_needed=False
    )
    db.add(db_intake)
    db.commit()
    
    db.refresh(db_appointment)
    return db_appointment

@router.get("", response_model=list[AppointmentResponse])
def get_appointments(
    status_filter: str = None, 
    date_filter: str = None, 
    db: Session = Depends(get_db)
):
    query = db.query(Appointment)
    if status_filter:
        query = query.filter(Appointment.status == status_filter)
    if date_filter:
        query = query.filter(Appointment.appointment_date == date_filter)
        
    return query.all()

@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    return appointment

@router.get("/{appointment_id}/intake", response_model=list[IntakeFormResponse])
def get_appointment_intake(appointment_id: str, db: Session = Depends(get_db)):
    """Return intake forms linked to this appointment."""
    forms = db.query(IntakeForm).filter(IntakeForm.appointment_id == appointment_id).all()
    result = []
    for f in forms:
        result.append(IntakeFormResponse(
            intake_id=f.intake_id,
            appointment_id=f.appointment_id,
            patient_id=f.patient_id,
            symptoms_description=f.symptoms_description,
            current_medications=f.current_medications,
            allergies=f.allergies,
            insurance_provider=f.insurance_provider,
            insurance_id=f.insurance_id,
            preferred_language=f.preferred_language,
            consent_given=f.consent_given,
            submitted_at=f.submitted_at,
            ai_summary=f.ai_summary,
            missing_fields=json.loads(f.missing_fields or "[]"),
            completeness_score=f.completeness_score,
            urgent_review_needed=f.urgent_review_needed
        ))
    return result

@router.patch("/{appointment_id}/status", response_model=AppointmentResponse)
def update_appointment_status(
    appointment_id: str,
    status_data: AppointmentStatusUpdate,
    db: Session = Depends(get_db)
):
    appointment = db.query(Appointment).filter(Appointment.appointment_id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
        
    old_status = appointment.status
    new_status = status_data.status
    
    valid_statuses = ["requested", "confirmed", "checked_in", "completed", "cancelled", "no_show"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of {valid_statuses}"
        )
        
    appointment.status = new_status
    appointment.updated_at = datetime.datetime.utcnow()
    
    # Write audit log
    log = AuditLog(
        appointment_id=appointment.appointment_id,
        action="status_change",
        old_status=old_status,
        new_status=new_status,
        changed_by=status_data.changed_by or "staff"
    )
    db.add(log)
    db.commit()
    db.refresh(appointment)
    
    return appointment
