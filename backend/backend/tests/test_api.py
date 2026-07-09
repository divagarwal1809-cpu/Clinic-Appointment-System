import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models.database import Base, get_db
from backend.main import app

# Create a clean database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_clinic.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency override
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def test_create_patient():
    patient_payload = {
        "full_name": "Test Jane",
        "dob": "1990-05-15",
        "gender": "Female",
        "phone": "555-0199",
        "email": "jane.test@example.com",
        "address": "456 Test Lane, Testville",
        "emergency_contact_name": "Bob Test",
        "emergency_contact_phone": "555-0198"
    }
    
    response = client.post("/patients", json=patient_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Test Jane"
    assert "patient_id" in data

def test_book_appointment_and_update_status():
    # 1. Create a patient first
    patient_payload = {
        "full_name": "John Booking",
        "dob": "1985-10-10",
        "gender": "Male",
        "phone": "555-0233",
        "email": "john.booking@example.com",
        "address": "123 Main St",
        "emergency_contact_name": "Mary Booking",
        "emergency_contact_phone": "555-0234"
    }
    patient_res = client.post("/patients", json=patient_payload)
    patient_id = patient_res.json()["patient_id"]
    
    # 2. Book appointment
    app_payload = {
        "patient_id": patient_id,
        "clinician_name": "Dr. Sarah Jenkins",
        "department": "Pediatrics",
        "appointment_date": "2026-07-10",
        "appointment_time": "10:30",
        "reason_for_visit": "Annual checkup for child."
    }
    
    app_res = client.post("/appointments", json=app_payload)
    assert app_res.status_code == 201
    app_data = app_res.json()
    assert app_data["status"] == "requested"
    app_id = app_data["appointment_id"]
    
    # 3. Patch status to confirmed
    patch_res = client.patch(f"/appointments/{app_id}/status", json={"status": "confirmed", "changed_by": "staff"})
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "confirmed"

def test_submit_intake_completeness_and_summarize():
    # Create patient
    p_res = client.post("/patients", json={
        "full_name": "Intake Patient",
        "dob": "1978-12-01",
        "gender": "Male",
        "phone": "555-9090",
        "email": "intake@example.com",
        "address": "909 Road Dr",
        "emergency_contact_name": "Helper Contact",
        "emergency_contact_phone": "555-9091"
    })
    p_id = p_res.json()["patient_id"]
    
    # Create appointment
    a_res = client.post("/appointments", json={
        "patient_id": p_id,
        "clinician_name": "Dr. Angela Osei",
        "department": "General Practice",
        "appointment_date": "2026-07-15",
        "appointment_time": "14:00",
        "reason_for_visit": "Persistent headache."
    })
    a_id = a_res.json()["appointment_id"]
    
    # Submit intake (some fields empty to test completeness calculation)
    intake_payload = {
        "appointment_id": a_id,
        "patient_id": p_id,
        "symptoms_description": "Frequent headaches in the afternoon.",
        "current_medications": "",  # missing
        "allergies": "None",        # counts as missing because it's 'none' in parsing
        "insurance_provider": "Aetna",
        "insurance_id": "",         # missing
        "preferred_language": "English",
        "consent_given": True
    }
    
    intake_res = client.post("/intake-forms", json=intake_payload)
    assert intake_res.status_code == 201
    intake_data = intake_res.json()
    
    # Required keys: symptoms_description, current_medications, allergies, insurance_provider, insurance_id, preferred_language (total 6)
    # Filled: symptoms_description (headaches), insurance_provider (Aetna), preferred_language (English) -> 3 filled
    # Score should be 3/6 = 0.5
    assert intake_data["completeness_score"] == 0.5
    assert "current_medications" in intake_data["missing_fields"]
    assert "allergies" in intake_data["missing_fields"]
    assert "insurance_id" in intake_data["missing_fields"]
    intake_id = intake_data["intake_id"]
    
    # Summarize intake
    sum_res = client.post(f"/intake-forms/{intake_id}/summarize")
    assert sum_res.status_code == 200
    sum_data = sum_res.json()
    assert sum_data["ai_summary"] is not None
    assert sum_data["urgent_review_needed"] is False
    
    # Verify dashboard summary
    dash_res = client.get("/dashboard/summary")
    assert dash_res.status_code == 200
    dash_data = dash_res.json()
    assert dash_data["incomplete_intakes_count"] > 0
