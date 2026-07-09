import os
import logging
from anthropic import Anthropic

logger = logging.getLogger(__name__)

# System prompt for draft generation
SYSTEM_PROMPT = """You are an administrative assistant for clinic front-desk staff.
Your job is to write a draft communication to a patient.
Maintain a warm, polite, professional, and reassuring tone.
CRITICAL SAFETY RULE: You must never diagnose, suggest treatment, or provide clinical guidance.
Only draft administrative notifications.
"""

def generate_draft_template(followup_type: str, patient_name: str, details: dict) -> str:
    """Fallback template generator for follow-up message drafts."""
    if followup_type == "missing_info_request":
        fields = details.get("missing_fields", [])
        fields_str = ", ".join([f.replace("_", " ") for f in fields])
        return (
            f"Dear {patient_name},\n\n"
            f"Thank you for submitting your clinic intake form. We noticed that some required information "
            f"was not completed: {fields_str}.\n\n"
            f"To help us prepare for your visit, please contact our office or submit this information "
            f"prior to your appointment. Thank you!\n\n"
            f"Best regards,\n"
            f"Clinic Front Desk"
        )
    elif followup_type == "appointment_reminder":
        date = details.get("date", "your scheduled date")
        time = details.get("time", "your scheduled time")
        clinician = details.get("clinician", "your clinician")
        return (
            f"Dear {patient_name},\n\n"
            f"This is a friendly reminder of your upcoming appointment with {clinician} on {date} at {time}.\n\n"
            f"If you need to reschedule or cancel, please let us know at least 24 hours in advance. "
            f"Please remember to bring your insurance card and arrive 10 minutes early.\n\n"
            f"We look forward to seeing you!\n\n"
            f"Best regards,\n"
            f"Clinic Front Desk"
        )
    elif followup_type == "post_visit_check":
        clinician = details.get("clinician", "your clinician")
        return (
            f"Dear {patient_name},\n\n"
            f"Thank you for visiting us today. We hope you had a comfortable experience with {clinician}.\n\n"
            f"If you have any administrative questions or need assistance scheduling a follow-up, "
            f"please do not hesitate to contact our front desk.\n\n"
            f"Wishing you a pleasant day,\n"
            f"Clinic Front Desk"
        )
    else:
        return f"Hello {patient_name}, this is a message from the clinic regarding your appointment. Please contact us for details."


def generate_ai_draft(followup_type: str, patient_name: str, details: dict) -> str:
    """Generates an AI-drafted message with the Claude API or falls back to templates."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set. Using template for followup draft.")
        return generate_draft_template(followup_type, patient_name, details)
        
    try:
        client = Anthropic(api_key=api_key)
        
        if followup_type == "missing_info_request":
            fields = details.get("missing_fields", [])
            prompt = f"Draft a polite email to {patient_name} asking them to provide the following missing fields from their intake form: {', '.join(fields)}."
        elif followup_type == "appointment_reminder":
            prompt = f"Draft an appointment reminder to {patient_name} for their visit with {details.get('clinician')} on {details.get('date')} at {details.get('time')}."
        elif followup_type == "post_visit_check":
            prompt = f"Draft a follow-up check-in to {patient_name} thanking them for their visit with {details.get('clinician')} today."
        else:
            prompt = f"Draft an administrative update email to patient {patient_name}."
            
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        return message.content[0].text.strip()
        
    except Exception as e:
        logger.error(f"Failed to generate draft with Claude: {e}. Falling back to template.")
        return generate_draft_template(followup_type, patient_name, details)
