import os
import json
import logging
import re
from anthropic import Anthropic
import httpx

logger = logging.getLogger(__name__)

# Mandatory guardrail prompt
SYSTEM_PROMPT = """You are an administrative intake summarizer for clinic front-desk staff.
Your role is purely administrative support.
CRITICAL SAFETY RULE: You are NOT a doctor or clinician. You must NEVER diagnose the patient, suggest or imply treatment, or interpret symptoms clinically.
Only restate, in plain factual language, what the patient reported. Do not add medical terms or clinical judgments.
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
    Ensures that the app functions correctly even if the Claude API key is missing or fails.
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
        summary = f"Emergency symptoms reported: '{symptoms}'. Route to clinician immediately."
        flags.append("URGENT CLINICAL REVIEW REQUIRED")
        draft = "Hello, we noticed your intake form indicates severe symptoms. A staff member will contact you immediately, or please call 911 if this is a life-threatening emergency."
    else:
        summary = f"Patient reports reason for visit: '{symptoms}'."
        if medications and medications.lower() != "none":
            summary += f" Medications: {medications}."
        if allergies and allergies.lower() != "none":
            summary += f" Allergies: {allergies}."
            
        if not allergies or allergies.lower() in ["none", "n/a", "no"]:
            flags.append("No allergies reported")
        else:
            flags.append(f"Patient reported allergy: {allergies}")
            
        draft = f"Hi, thank you for submitting your intake form. We have successfully received it and look forward to your visit. Preferred language: {preferred_language}."
        
    # Apply safety scrubbing to all text outputs
    return {
        "summary": scrub_safety(summary),
        "flags": [scrub_safety(f) for f in flags],
        "follow_up_draft": scrub_safety(draft),
        "urgent_review_needed": is_emergency
    }

def summarize_intake(
    symptoms: str,
    medications: str,
    allergies: str,
    preferred_language: str,
    consent_given: bool
) -> dict:
    """
    Summarizes the patient intake form.
    Calls Nvidia (Gemma), Gemini API, Anthropic Claude API, or uses mock fallback.
    """
    if not consent_given:
        raise ValueError("Patient consent is required for intake processing.")
        
    nvidia_key = os.environ.get("NVIDIA_API_KEY") or "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"
    nvidia_base_url = os.environ.get("NVIDIA_BASE_URL") or "https://integrate.api.nvidia.com/v1"
    nvidia_model = os.environ.get("NVIDIA_MODEL") or "google/gemma-2-2b-it"
    
    gemini_key = os.environ.get("GEMINI_API_KEY")
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    
    prompt_content = f"""
    Patient Symptoms: {symptoms or 'None reported'}
    Medications: {medications or 'None reported'}
    Allergies: {allergies or 'None reported'}
    Preferred Language: {preferred_language or 'English'}
    """
    
    # 1. Try Nvidia (Gemma 2b) API
    if nvidia_key:
        try:
            url = f"{nvidia_base_url.rstrip('/')}/chat/completions"
            payload = {
                "model": nvidia_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt_content}
                ],
                "temperature": 0.0,
                "max_tokens": 1000
            }
            headers = {
                "Authorization": f"Bearer {nvidia_key}",
                "Content-Type": "application/json"
            }
            resp = httpx.post(url, json=payload, headers=headers, timeout=30.0)
            resp.raise_for_status()
            
            res_data = resp.json()
            response_text = res_data["choices"][0]["message"]["content"].strip()
            
            # Clean up markdown fences if model outputs them
            if response_text.startswith("```"):
                lines = response_text.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                response_text = "\n".join(lines).strip()
                
            parsed_response = json.loads(response_text)
            return {
                "summary": scrub_safety(parsed_response.get("summary", "")),
                "flags": [scrub_safety(f) for f in parsed_response.get("flags", [])],
                "follow_up_draft": scrub_safety(parsed_response.get("follow_up_draft", "")),
                "urgent_review_needed": bool(parsed_response.get("urgent_review_needed", False))
            }
        except Exception as e:
            logger.error(f"Nvidia/Gemma API request failed: {str(e)}. Trying Gemini, Claude or mock fallback...")
            
    # 2. Try Google Gemini API
    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={AQ.Ab8RN6KWqq55qcLVyl9xYaFXq9rFXkuu20SiVCIiHVMZLGOERw}"
            payload = {
                "contents": [{"parts": [{"text": prompt_content}]}],
                "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.0
                }
            }
            headers = {"Content-Type": "application/json"}
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
            logger.error(f"Gemini API request failed: {str(e)}. Trying Anthropic or mock fallback...")
            
    # 3. Try Anthropic Claude API
    if anthropic_key:
        try:
            client = Anthropic(api_key=anthropic_key)
            message = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": prompt_content}
                ],
                temperature=0.0
            )
            response_text = message.content[0].text.strip()
            parsed_response = json.loads(response_text)
            return {
                "summary": scrub_safety(parsed_response.get("summary", "")),
                "flags": [scrub_safety(f) for f in parsed_response.get("flags", [])],
                "follow_up_draft": scrub_safety(parsed_response.get("follow_up_draft", "")),
                "urgent_review_needed": bool(parsed_response.get("urgent_review_needed", False))
            }
        except Exception as e:
            logger.error(f"Claude API request failed: {str(e)}. Falling back to mock...")
            
    # 4. Fallback to mock
    logger.warning("No functional API keys (NVIDIA_API_KEY, GEMINI_API_KEY or ANTHROPIC_API_KEY) available. Running mock fallback.")
    return mock_summarize(symptoms, medications, allergies, preferred_language)
