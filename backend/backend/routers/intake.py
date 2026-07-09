import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.models.database import get_db, IntakeForm, Appointment, Patient, FollowUp
from backend.schemas.schemas import IntakeFormCreate, IntakeFormResponse
from backend.services.ai_summarizer import summarize_intake

router = APIRouter(prefix="/intake-forms", tags=["intake"])

@router.get("", response_model=list[IntakeFormResponse])
def list_intake_forms(db: Session = Depends(get_db)):
    intakes = db.query(IntakeForm).all()
    result = []
    for intake in intakes:
        result.append(IntakeFormResponse(
            intake_id=intake.intake_id,
            appointment_id=intake.appointment_id,
            patient_id=intake.patient_id,
            symptoms_description=intake.symptoms_description,
            current_medications=intake.current_medications,
            allergies=intake.allergies,
            insurance_provider=intake.insurance_provider,
            insurance_id=intake.insurance_id,
            preferred_language=intake.preferred_language,
            consent_given=intake.consent_given,
            submitted_at=intake.submitted_at,
            ai_summary=intake.ai_summary,
            missing_fields=json.loads(intake.missing_fields or "[]"),
            completeness_score=intake.completeness_score,
            urgent_review_needed=intake.urgent_review_needed
        ))
    return result

@router.post("", response_model=IntakeFormResponse, status_code=status.HTTP_201_CREATED)
def submit_intake_form(intake_data: IntakeFormCreate, db: Session = Depends(get_db)):
    # Verify appointment exists
    appointment = db.query(Appointment).filter(Appointment.appointment_id == intake_data.appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appointment not found"
        )
        
    # Check if consent is given
    if not intake_data.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Consent is required to submit intake form"
        )
        
    # Deterministic completeness check
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
    
    # We convert fields to dictionary to check them
    intake_dict = intake_data.model_dump()
    for key in required_keys:
        val = intake_dict.get(key)
        if not val or (isinstance(val, str) and val.strip().lower() in ["", "none", "n/a"]):
            missing.append(key)
        else:
            filled_count += 1
            
    completeness = filled_count / len(required_keys)
    
    db_intake = IntakeForm(
        appointment_id=intake_data.appointment_id,
        patient_id=intake_data.patient_id,
        symptoms_description=intake_data.symptoms_description,
        current_medications=intake_data.current_medications,
        allergies=intake_data.allergies,
        insurance_provider=intake_data.insurance_provider,
        insurance_id=intake_data.insurance_id,
        preferred_language=intake_data.preferred_language,
        consent_given=intake_data.consent_given,
        completeness_score=completeness,
        missing_fields=json.dumps(missing),
        urgent_review_needed=False  # Determined during summarization
    )
    
    db.add(db_intake)
    db.commit()
    db.refresh(db_intake)
    
    return IntakeFormResponse(
        intake_id=db_intake.intake_id,
        appointment_id=db_intake.appointment_id,
        patient_id=db_intake.patient_id,
        symptoms_description=db_intake.symptoms_description,
        current_medications=db_intake.current_medications,
        allergies=db_intake.allergies,
        insurance_provider=db_intake.insurance_provider,
        insurance_id=db_intake.insurance_id,
        preferred_language=db_intake.preferred_language,
        consent_given=db_intake.consent_given,
        submitted_at=db_intake.submitted_at,
        ai_summary=db_intake.ai_summary,
        missing_fields=json.loads(db_intake.missing_fields),
        completeness_score=db_intake.completeness_score,
        urgent_review_needed=db_intake.urgent_review_needed
    )

@router.post("/{intake_id}/summarize", response_model=IntakeFormResponse)
def summarize_intake_route(intake_id: str, db: Session = Depends(get_db)):
    intake = db.query(IntakeForm).filter(IntakeForm.intake_id == intake_id).first()
    if not intake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake form not found"
        )
        
    if not intake.consent_given:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot run AI summarization without patient consent"
        )
        
    # Trigger summarizer (uses Claude or falls back to rule-based mock)
    ai_result = summarize_intake(
        symptoms=intake.symptoms_description,
        medications=intake.current_medications,
        allergies=intake.allergies,
        preferred_language=intake.preferred_language,
        consent_given=intake.consent_given
    )
    
    # Update intake record
    intake.ai_summary = ai_result.get("summary")
    intake.urgent_review_needed = ai_result.get("urgent_review_needed", False)
    db.commit()
    db.refresh(intake)
    
    # Generate/Update followup draft message in DB if AI provides follow_up_draft
    draft_msg = ai_result.get("follow_up_draft")
    if draft_msg:
        # Determine followup type
        missing = json.loads(intake.missing_fields)
        f_type = "missing_info_request" if len(missing) > 0 else "appointment_reminder"
        if intake.urgent_review_needed:
            f_type = "post_visit_check"  # Safety check-in
            
        # Check if followup already exists for this appointment
        existing_followup = db.query(FollowUp).filter(FollowUp.appointment_id == intake.appointment_id).first()
        if existing_followup:
            existing_followup.message_draft = draft_msg
            existing_followup.followup_type = f_type
        else:
            new_followup = FollowUp(
                appointment_id=intake.appointment_id,
                patient_id=intake.patient_id,
                followup_type=f_type,
                message_draft=draft_msg,
                status="draft"
            )
            db.add(new_followup)
        db.commit()
        
    return IntakeFormResponse(
        intake_id=intake.intake_id,
        appointment_id=intake.appointment_id,
        patient_id=intake.patient_id,
        symptoms_description=intake.symptoms_description,
        current_medications=intake.current_medications,
        allergies=intake.allergies,
        insurance_provider=intake.insurance_provider,
        insurance_id=intake.insurance_id,
        preferred_language=intake.preferred_language,
        consent_given=intake.consent_given,
        submitted_at=intake.submitted_at,
        ai_summary=intake.ai_summary,
        missing_fields=json.loads(intake.missing_fields),
        completeness_score=intake.completeness_score,
        urgent_review_needed=intake.urgent_review_needed
    )

@router.get("/{intake_id}", response_model=IntakeFormResponse)
def get_intake_form(intake_id: str, db: Session = Depends(get_db)):
    intake = db.query(IntakeForm).filter(IntakeForm.intake_id == intake_id).first()
    if not intake:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intake form not found"
        )
        
    return IntakeFormResponse(
        intake_id=intake.intake_id,
        appointment_id=intake.appointment_id,
        patient_id=intake.patient_id,
        symptoms_description=intake.symptoms_description,
        current_medications=intake.current_medications,
        allergies=intake.allergies,
        insurance_provider=intake.insurance_provider,
        insurance_id=intake.insurance_id,
        preferred_language=intake.preferred_language,
        consent_given=intake.consent_given,
        submitted_at=intake.submitted_at,
        ai_summary=intake.ai_summary,
        missing_fields=json.loads(intake.missing_fields),
        completeness_score=intake.completeness_score,
        urgent_review_needed=intake.urgent_review_needed
    )
