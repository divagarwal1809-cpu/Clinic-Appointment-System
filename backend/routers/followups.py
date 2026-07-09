import datetime
import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.models.database import get_db, FollowUp, Patient, Appointment, IntakeForm
from backend.schemas.schemas import FollowUpResponse, FollowUpStatusUpdate
from backend.services.followup_drafts import generate_ai_draft

router = APIRouter(prefix="/followups", tags=["followups"])

@router.get("", response_model=list[FollowUpResponse])
def list_followups(db: Session = Depends(get_db)):
    from sqlalchemy.orm import joinedload
    return db.query(FollowUp).options(joinedload(FollowUp.patient)).all()

@router.post("/{followup_id}/generate-draft", response_model=FollowUpResponse)
def generate_followup_draft(followup_id: str, db: Session = Depends(get_db)):
    followup = db.query(FollowUp).filter(FollowUp.followup_id == followup_id).first()
    if not followup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up record not found"
        )
        
    patient = db.query(Patient).filter(Patient.patient_id == followup.patient_id).first()
    appointment = db.query(Appointment).filter(Appointment.appointment_id == followup.appointment_id).first()
    intake = db.query(IntakeForm).filter(IntakeForm.appointment_id == followup.appointment_id).first()
    
    # Collect details for AI drafting
    details = {
        "date": appointment.appointment_date if appointment else "unknown",
        "time": appointment.appointment_time if appointment else "unknown",
        "clinician": appointment.clinician_name if appointment else "unknown",
        "missing_fields": []
    }
    
    if intake:
        try:
            details["missing_fields"] = json.loads(intake.missing_fields)
        except Exception:
            details["missing_fields"] = []
            
    # Generate draft using service
    draft = generate_ai_draft(
        followup_type=followup.followup_type,
        patient_name=patient.full_name if patient else "Patient",
        details=details
    )
    
    followup.message_draft = draft
    db.commit()
    db.refresh(followup)
    
    return followup

@router.patch("/{followup_id}/status", response_model=FollowUpResponse)
def update_followup_status(
    followup_id: str,
    status_data: FollowUpStatusUpdate,
    db: Session = Depends(get_db)
):
    followup = db.query(FollowUp).filter(FollowUp.followup_id == followup_id).first()
    if not followup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Follow-up record not found"
        )
        
    valid_statuses = ["draft", "approved", "sent", "acknowledged"]
    if status_data.status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be one of {valid_statuses}"
        )
        
    # Human-in-the-loop: transition from draft can only occur via explicit action
    # If the message draft text is edited, save it
    if status_data.message_draft is not None:
        followup.message_draft = status_data.message_draft
        
    old_status = followup.status
    new_status = status_data.status
    
    followup.status = new_status
    
    # Set sent_at timestamp when changing to sent
    if new_status == "sent" and old_status != "sent":
        followup.sent_at = datetime.datetime.utcnow()
        
    db.commit()
    db.refresh(followup)
    
    return followup
