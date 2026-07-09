import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from backend.models.database import get_db, Appointment, IntakeForm, FollowUp, AuditLog
from backend.schemas.schemas import DashboardSummaryResponse

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary(db: Session = Depends(get_db)):
    # Today's date in YYYY-MM-DD format
    today_str = datetime.date.today().isoformat()
    
    # Eager load patient details for today's appointments
    today_appointments = db.query(Appointment)\
        .filter(Appointment.appointment_date == today_str)\
        .options(joinedload(Appointment.patient))\
        .all()
        
    # Incomplete intakes count
    incomplete_intakes_count = db.query(IntakeForm)\
        .filter(IntakeForm.completeness_score < 1.0)\
        .count()
        
    # Pending followups (draft state) count
    pending_followups_count = db.query(FollowUp)\
        .filter(FollowUp.status == "draft")\
        .count()
        
    # Pending followups list (including both draft and approved but not sent)
    pending_followups = db.query(FollowUp)\
        .filter(FollowUp.status.in_(["draft", "approved"]))\
        .options(joinedload(FollowUp.patient))\
        .all()
        
    # Recent audit logs for appointments status changes
    recent_audit_logs = db.query(AuditLog)\
        .options(joinedload(AuditLog.appointment))\
        .order_by(AuditLog.changed_at.desc())\
        .limit(10)\
        .all()
        
    return {
        "today_appointments": today_appointments,
        "incomplete_intakes_count": incomplete_intakes_count,
        "pending_followups_count": pending_followups_count,
        "pending_followups": pending_followups,
        "recent_audit_logs": recent_audit_logs
    }
