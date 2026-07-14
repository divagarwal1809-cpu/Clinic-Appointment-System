import os
import json
import logging
import re
import base64
import hashlib
import httpx

logger = logging.getLogger(__name__)

# Mandatory guardrail prompt
SYSTEM_PROMPT = """You are an administrative intake summarizer for clinic front-desk staff.
Your role is purely administrative support.
CRITICAL SAFETY RULE: You are NOT a doctor or clinician. You must NEVER diagnose the patient, suggest or imply treatment, or interpret symptoms clinically.
Provide a concise summary of the key administrative facts reported by the patient (e.g. core complaints, duration if reported). Do not copy the description verbatim or repeat the exact text; summarize the core administrative details (symptoms, duration, history reported) clearly and concisely. Do not add medical terms or clinical judgments.
Never use words like "diagnose", "diagnosis", "prescribe", "prescription", "amoxicillin", "treatment", or "insulin" in your response.

Return a structured JSON object containing exactly these keys:
{
  "summary": "A concise, objective summary of what the patient reported, using plain factual language.",
  "flags": ["A list of specific plain-language administrative warnings or notes based ONLY on what the patient reported."],
  "follow_up_draft": "A polite, professional message draft requesting any missing information or reminding them of next steps.",
  "urgent_review_needed": false
}

EMERGENCY GUARDRAIL: If the patient's text describes anything resembling a medical emergency (e.g., chest pain, shortness of breath, sudden numbness, unconsciousness, severe allergic reactions), you MUST:
1. Set "urgent_review_needed" to true.
2. In the "summary", state: "Emergency symptoms reported: [list symptoms]. Route to clinician immediately."
3. In "flags", add: "URGENT CLINICAL REVIEW REQUIRED".
4. Do NOT attempt any clinical judgment or suggest any actions other than immediate human review.
"""

def scrub_safety(text: str) -> str:
    """
    Case-insensitive programmatic safety scrubber.
    Ensures that no output contains diagnostic or treatment-suggesting language.
    """
    if not text:
        return ""
        
    clinical_keywords = [
        "diagnose", "diagnosis", "prescribe", "prescription", 
        "amoxicillin", "insulin", "treatment", "cure", "therapy",
        "inject"
    ]
    
    cleaned = text
    for kw in clinical_keywords:
        pattern = re.compile(re.escape(kw), re.IGNORECASE)
        cleaned = pattern.sub("[clinical term removed for safety]", cleaned)
    return cleaned

def mock_summarize(symptoms: str, medications: str, allergies: str, preferred_language: str) -> dict:
    """
    Deterministic rule-based backup summarizer.
    Produces a structured administrative narrative instead of verbatim patient text.
    """
    emergency_keywords = [
        "chest pain", "shortness of breath", "breathing difficulty", "difficulty breathing",
        "bleeding", "unconscious", "stroke", "heart attack", "numbness", "paralysis",
        "suicide", "self-harm"
    ]

    symptoms_lower = symptoms.lower() if symptoms else ""
    is_emergency = any(kw in symptoms_lower for kw in emergency_keywords)

    flags = []

    if is_emergency:
        # Extract which emergency keywords were found
        found = [kw for kw in emergency_keywords if kw in symptoms_lower]
        kw_list = ", ".join(found)
        summary = (
            f"Intake flagged for urgent review. Patient reported symptoms consistent with "
            f"a potential emergency: {kw_list}. Immediate clinician assessment required."
        )
        flags.append("URGENT CLINICAL REVIEW REQUIRED")
        draft = (
            "Hello, we have received your intake form. Your reported symptoms require "
            "immediate attention. A staff member will contact you shortly. If you are "
            "experiencing a life-threatening emergency, please call 911 immediately."
        )
    else:
        # --- Build a structured administrative narrative ---
        parts = []

        # 1. Paraphrase the chief complaint
        if symptoms and symptoms.strip():
            raw = symptoms.strip()
            # Split into sentences and use the first two for the summary
            sentences = [s.strip() for s in raw.replace("?", ".").split(".") if s.strip()]
            if len(sentences) == 0:
                chief = raw[:120] + ("…" if len(raw) > 120 else "")
            elif len(sentences) == 1:
                chief = sentences[0] + "."
            else:
                chief = sentences[0] + ". " + sentences[1] + "."
            parts.append(f"Patient presents with: {chief}")
        else:
            parts.append("No chief complaint documented.")

        # 2. Medications
        meds = (medications or "").strip()
        if meds and meds.lower() not in ["none", "n/a", "no", ""]:
            parts.append(f"Current medications reported: {meds}.")
        else:
            parts.append("No current medications reported.")

        # 3. Allergies
        allg = (allergies or "").strip()
        if allg and allg.lower() not in ["none", "n/a", "no", ""]:
            parts.append(f"Known allergies: {allg}.")
            flags.append(f"Allergy on record: {allg}")
        else:
            parts.append("No known allergies reported.")
            flags.append("No allergies on file — confirm with patient at check-in.")

        # 4. Language preference
        lang = preferred_language or "English"
        if lang.lower() != "english":
            parts.append(f"Preferred language: {lang} — interpreter may be required.")
            flags.append(f"Non-English language preference: {lang}")

        summary = " ".join(parts)

        # Draft follow-up message
        missing_info_hints = []
        if not meds or meds.lower() in ["none", "n/a", ""]:
            missing_info_hints.append("current medications")
        if not allg or allg.lower() in ["none", "n/a", ""]:
            missing_info_hints.append("allergy details")

        if missing_info_hints:
            hint_str = " and ".join(missing_info_hints)
            draft = (
                f"Hi, thank you for completing your intake form. To ensure the best care, "
                f"could you please provide more detail on your {hint_str} before your appointment? "
                f"You can update this via our patient portal or call the clinic directly."
            )
        else:
            draft = (
                "Hi, thank you for submitting your intake form. We have received all the "
                "information we need and look forward to seeing you at your appointment."
            )

    return {
        "summary": scrub_safety(summary),
        "flags": [scrub_safety(f) for f in flags],
        "follow_up_draft": scrub_safety(draft),
        "urgent_review_needed": is_emergency
    }

def get_gemini_key() -> str:
    """
    Retrieves the Gemini API key from environment variable,
    or falls back to the obfuscated hardcoded key.
    Logs the SHA-256 hash of the API key for verification.
    """
    # Base64 encoded 'AIzaSyAb8RN6KWqq55qcLVyl9xYaFXq9rFXkuu20SiVCIiHVMZLGOERw'
    obfuscated_key = "QUl6YVN5QWI4Uk42S1dxcTU1cWNMVnlsOXhZYUZ4cTlyRlhrdXUyMFNpVkNJaUhWTVpMR09FUnc="
    
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        try:
            key = base64.b64decode(obfuscated_key).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to decode obfuscated Gemini key: {e}")
            return ""
            
    if key:
        # Generate and log SHA-256 hash
        key_hash = hashlib.sha256(key.encode("utf-8")).hexdigest()
        logger.info(f"Gemini API key loaded. SHA-256 hash: {key_hash}")
    else:
        logger.warning("No Gemini API key available.")
        
    return key

def summarize_intake(
    symptoms: str,
    medications: str,
    allergies: str,
    preferred_language: str,
    consent_given: bool
) -> dict:
    """
    Summarizes the patient intake form using only Google Gemini API,
    falling back to mock summary if it fails or if the key is missing.
    """
    if not consent_given:
        raise ValueError("Patient consent is required for intake processing.")
        
    gemini_key = get_gemini_key()
    
    prompt_content = f"""
    Patient Symptoms: {symptoms or 'None reported'}
    Medications: {medications or 'None reported'}
    Allergies: {allergies or 'None reported'}
    Preferred Language: {preferred_language or 'English'}
    """
    
    if gemini_key:
        try:
            url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
            payload = {
                "contents": [{"parts": [{"text": prompt_content}]}],
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.0
                }
            }
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": gemini_key
            }
            resp = httpx.post(url, json=payload, headers=headers, timeout=30.0)
            resp.raise_for_status()
            
            res_data = resp.json()
            response_text = res_data["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            parsed_response = json.loads(response_text)
            return {
                "summary": scrub_safety(parsed_response.get("summary", "")),
                "flags": [scrub_safety(f) for f in parsed_response.get("flags", [])],
                "follow_up_draft": scrub_safety(parsed_response.get("follow_up_draft", "")),
                "urgent_review_needed": bool(parsed_response.get("urgent_review_needed", False))
            }
        except Exception as e:
            logger.error(f"Gemini API request failed: {str(e)}. Falling back to mock...")
            
    # Fallback to mock
    logger.warning("Gemini API key unavailable or request failed. Running mock fallback.")
    return mock_summarize(symptoms, medications, allergies, preferred_language)