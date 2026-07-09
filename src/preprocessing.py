import os
import csv
import json
import random
import uuid
import datetime
from sqlalchemy.orm import Session
from backend.models.database import SessionLocal, init_db, Patient, Appointment, IntakeForm, FollowUp

# Lists of synthetic data components
FIRST_NAMES = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", "William", "Elizabeth",
               "David", "Barbara", "Richard", "Susan", "Joseph", "Jessica", "Thomas", "Sarah", "Charles", "Karen",
               "Christopher", "Nancy", "Daniel", "Lisa", "Matthew", "Betty", "Anthony", "Margaret", "Mark", "Sandra"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
              "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
              "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson"]
DEPARTMENTS = ["General Practice", "Pediatrics", "Dental", "Cardiology", "Dermatology", "Orthopedics"]
CLINICIANS = {
    "General Practice": ["Dr. Angela Osei", "Dr. John Cooper"],
    "Pediatrics": ["Dr. Sarah Jenkins", "Dr. Amit Patel"],
    "Dental": ["Dr. Emily Vance", "Dr. Lisa Wong"],
    "Cardiology": ["Dr. Robert Vance", "Dr. Marcus Sterling"],
    "Dermatology": ["Dr. Helen Carter"],
    "Orthopedics": ["Dr. David Miller", "Dr. Rachel Green"]
}
SYMPTOMS_POOL = [
    "Mild seasonal allergies, sneezing and runny nose.",
    "Persistent low back pain after lifting boxes two days ago.",
    "Routine physical exam and checkup.",
    "Annual dental cleaning and mild tooth sensitivity.",
    "Dry cough and congestion for the last three days. No fever.",
    "Sore throat, difficulty swallowing, fatigue.",
    "Minor skin rash on the left forearm, slightly itchy.",
    "Follow-up for high blood pressure monitoring.",
    "Sprained ankle from running on a trail. Mild swelling.",
    "Frequent headaches in the afternoon, eye strain."
]
EMERGENCY_SYMPTOMS_POOL = [
    "Sudden onset of severe chest pain and left arm numbness.",
    "Difficulty breathing, shortness of breath, tightness in chest.",
    "Heavy bleeding from a deep laceration on the thigh.",
    "Sudden weakness on one side of the body, difficulty speaking.",
    "Severe allergic reaction after eating peanuts, swollen lips and throat."
]
MEDICATIONS_POOL = ["Lisinopril 10mg", "Metformin 500mg", "Atorvastatin 20mg", "Albuterol inhaler", "Amoxicillin 500mg", "None"]
ALLERGIES_POOL = ["Penicillin", "Sulfa drugs", "Peanuts", "Aspirin", "Tree nuts", "Shellfish", "None", "None", "None"]
INSURANCE_PROVIDERS = ["Blue Cross Blue Shield", "Aetna", "Cigna", "UnitedHealthcare", "Humana"]
LANGUAGES = ["English", "Spanish", "Mandarin", "French", "Vietnamese"]

def generate_synthetic_data(count=50):
    os.makedirs("data", exist_ok=True)
    
    # Paths
    patients_csv = "data/patients.csv"
    appointments_csv = "data/appointments.csv"
    intake_csv = "data/intake_forms.csv"
    followups_csv = "data/followups.csv"
    
    # 1. Generate Patients
    patients = []
    patient_ids = []
    
    for i in range(count):
        p_id = str(uuid.uuid4())
        patient_ids.append(p_id)
        name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        dob = (datetime.date(1950, 1, 1) + datetime.timedelta(days=random.randint(0, 25000))).isoformat()
        gender = random.choice(["Male", "Female", "Other", "Prefer not to say"])
        phone = f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        email = f"{name.lower().replace(' ', '.')}@example.com"
        address = f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Pine Rd', 'Elm St', 'Maple Blvd'])}, Cityville"
        e_name = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        e_phone = f"555-{random.randint(100, 999)}-{random.randint(1000, 9999)}"
        created_at = (datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(30, 365))).isoformat()
        
        patients.append({
            "patient_id": p_id,
            "full_name": name,
            "dob": dob,
            "gender": gender,
            "phone": phone,
            "email": email,
            "address": address,
            "emergency_contact_name": e_name,
            "emergency_contact_phone": e_phone,
            "created_at": created_at
        })
        
    with open(patients_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=patients[0].keys())
        writer.writeheader()
        writer.writerows(patients)
        
    # 2. Generate Appointments
    appointments = []
    appointment_ids = []
    statuses = ["requested", "confirmed", "checked_in", "completed", "cancelled", "no_show"]
    
    # Distribute appointments across past, today, and future
    base_date = datetime.date.today()
    
    for i in range(count):
        app_id = str(uuid.uuid4())
        appointment_ids.append(app_id)
        p_id = random.choice(patient_ids)
        dept = random.choice(DEPARTMENTS)
        clinician = random.choice(CLINICIANS[dept])
        
        # Date distribution: 40% past, 20% today, 40% future
        rand_pct = random.random()
        if rand_pct < 0.4:
            app_date = base_date - datetime.timedelta(days=random.randint(1, 30))
            status = random.choice(["completed", "cancelled", "no_show"])
        elif rand_pct < 0.6:
            app_date = base_date
            status = random.choice(["confirmed", "checked_in", "requested"])
        else:
            app_date = base_date + datetime.timedelta(days=random.randint(1, 14))
            status = random.choice(["confirmed", "requested"])
            
        app_time = f"{random.randint(8, 16):02d}:{random.choice([0, 15, 30, 45]):02d}"
        
        # Reason for visit matches department/symptoms
        reason = random.choice(SYMPTOMS_POOL)
        
        created_at = (datetime.datetime.utcnow() - datetime.timedelta(days=random.randint(15, 45))).isoformat()
        updated_at = datetime.datetime.utcnow().isoformat()
        
        appointments.append({
            "appointment_id": app_id,
            "patient_id": p_id,
            "clinician_name": clinician,
            "department": dept,
            "appointment_date": app_date.isoformat(),
            "appointment_time": app_time,
            "status": status,
            "reason_for_visit": reason,
            "created_at": created_at,
            "updated_at": updated_at
        })
        
    with open(appointments_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=appointments[0].keys())
        writer.writeheader()
        writer.writerows(appointments)
        
    # 3. Generate Intake Forms
    intake_forms = []
    # Fill intakes for all checked_in/completed and some confirmed/requested
    for app in appointments:
        if app["status"] in ["checked_in", "completed", "confirmed"] or random.random() < 0.5:
            # 10% chance of emergency symptoms for safety testing simulation
            is_emergency = random.random() < 0.1
            symptoms = random.choice(EMERGENCY_SYMPTOMS_POOL) if is_emergency else app["reason_for_visit"]
            
            meds = random.choice(MEDICATIONS_POOL)
            allergies = random.choice(ALLERGIES_POOL)
            
            # Simulate incomplete form fields (blank values)
            ins_provider = random.choice(INSURANCE_PROVIDERS) if random.random() > 0.15 else ""
            ins_id = f"INS-{random.randint(10000, 99999)}" if ins_provider and random.random() > 0.15 else ""
            
            pref_lang = random.choice(LANGUAGES)
            consent = True
            
            # Deterministic missing fields check
            req_fields = {
                "symptoms_description": symptoms,
                "current_medications": meds,
                "allergies": allergies,
                "insurance_provider": ins_provider,
                "insurance_id": ins_id,
                "preferred_language": pref_lang
            }
            missing = [k for k, v in req_fields.items() if not v or v.lower() == "none"]
            filled_count = sum(1 for k, v in req_fields.items() if v and v.lower() != "none")
            completeness = filled_count / len(req_fields)
            
            # Mock AI Summary (or empty to let the summarize endpoint populate it)
            ai_sum = ""
            urgent_needed = is_emergency
            
            if random.random() > 0.3:  # 70% already summarized in sample data
                if is_emergency:
                    ai_sum = f"Emergency symptoms reported: '{symptoms}'. Route to clinician immediately."
                else:
                    ai_sum = f"Patient reports reason for visit as: '{symptoms}'. Currently on {meds or 'no medications'}. Allergies: {allergies or 'none'}."
            
            submitted_at = (datetime.datetime.fromisoformat(app["appointment_date"]) - datetime.timedelta(days=random.randint(0, 2))).isoformat()
            
            intake_forms.append({
                "intake_id": str(uuid.uuid4()),
                "appointment_id": app["appointment_id"],
                "patient_id": app["patient_id"],
                "symptoms_description": symptoms,
                "current_medications": meds,
                "allergies": allergies,
                "insurance_provider": ins_provider,
                "insurance_id": ins_id,
                "preferred_language": pref_lang,
                "consent_given": consent,
                "submitted_at": submitted_at,
                "ai_summary": ai_sum,
                "missing_fields": json.dumps(missing),
                "completeness_score": completeness,
                "urgent_review_needed": urgent_needed
            })
            
    with open(intake_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=intake_forms[0].keys())
        writer.writeheader()
        writer.writerows(intake_forms)
        
    # 4. Generate Follow-Ups
    followups = []
    followup_types = ["missing_info_request", "appointment_reminder", "post_visit_check"]
    followup_statuses = ["draft", "approved", "sent", "acknowledged"]
    
    # Generate followups for some appointments
    for intake in intake_forms:
        app = next(a for a in appointments if a["appointment_id"] == intake["appointment_id"])
        
        # If there are missing fields, generate missing_info_request
        missing = json.loads(intake["missing_fields"])
        if len(missing) > 0 and random.random() > 0.3:
            f_type = "missing_info_request"
            f_status = random.choice(["draft", "approved"])
            draft = f"Dear patient, we are preparing for your upcoming appointment. Please update your missing intake information: {', '.join(missing)}."
            
            followups.append({
                "followup_id": str(uuid.uuid4()),
                "appointment_id": intake["appointment_id"],
                "patient_id": intake["patient_id"],
                "followup_type": f_type,
                "message_draft": draft,
                "status": f_status,
                "scheduled_send_at": (datetime.datetime.utcnow() + datetime.timedelta(days=1)).isoformat(),
                "sent_at": ""
            })
            
    with open(followups_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=followups[0].keys())
        writer.writeheader()
        writer.writerows(followups)
        
    print(f"Generated synthetic CSVs in data/ folder ({count} records).")


def import_csv_to_db():
    init_db()
    db = SessionLocal()
    
    try:
        # Clear existing tables (safe for local development initialization)
        db.query(FollowUp).delete()
        db.query(IntakeForm).delete()
        db.query(Appointment).delete()
        db.query(Patient).delete()
        db.commit()
        
        # Import Patients
        with open("data/patients.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p = Patient(
                    patient_id=row["patient_id"],
                    full_name=row["full_name"],
                    dob=row["dob"],
                    gender=row["gender"],
                    phone=row["phone"],
                    email=row["email"],
                    address=row["address"],
                    emergency_contact_name=row["emergency_contact_name"],
                    emergency_contact_phone=row["emergency_contact_phone"],
                    created_at=datetime.datetime.fromisoformat(row["created_at"])
                )
                db.add(p)
        db.commit()
        
        # Import Appointments
        with open("data/appointments.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                app = Appointment(
                    appointment_id=row["appointment_id"],
                    patient_id=row["patient_id"],
                    clinician_name=row["clinician_name"],
                    department=row["department"],
                    appointment_date=row["appointment_date"],
                    appointment_time=row["appointment_time"],
                    status=row["status"],
                    reason_for_visit=row["reason_for_visit"],
                    created_at=datetime.datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.datetime.fromisoformat(row["updated_at"])
                )
                db.add(app)
        db.commit()
        
        # Import Intake Forms
        with open("data/intake_forms.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ai_summary_val = row["ai_summary"] if row["ai_summary"] else None
                intake = IntakeForm(
                    intake_id=row["intake_id"],
                    appointment_id=row["appointment_id"],
                    patient_id=row["patient_id"],
                    symptoms_description=row["symptoms_description"],
                    current_medications=row["current_medications"],
                    allergies=row["allergies"],
                    insurance_provider=row["insurance_provider"],
                    insurance_id=row["insurance_id"],
                    preferred_language=row["preferred_language"],
                    consent_given=row["consent_given"] == 'True',
                    submitted_at=datetime.datetime.fromisoformat(row["submitted_at"]),
                    ai_summary=ai_summary_val,
                    missing_fields=row["missing_fields"],
                    completeness_score=float(row["completeness_score"]),
                    urgent_review_needed=row["urgent_review_needed"] == 'True'
                )
                db.add(intake)
        db.commit()
        
        # Import FollowUps
        with open("data/followups.csv", mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                scheduled_send = datetime.datetime.fromisoformat(row["scheduled_send_at"]) if row["scheduled_send_at"] else None
                sent = datetime.datetime.fromisoformat(row["sent_at"]) if row["sent_at"] else None
                follow = FollowUp(
                    followup_id=row["followup_id"],
                    appointment_id=row["appointment_id"],
                    patient_id=row["patient_id"],
                    followup_type=row["followup_type"],
                    message_draft=row["message_draft"],
                    status=row["status"],
                    scheduled_send_at=scheduled_send,
                    sent_at=sent
                )
                db.add(follow)
        db.commit()
        
        print("Fictional synthetic data successfully loaded into SQLite database.")
        
    except Exception as e:
        db.rollback()
        print(f"Error importing CSV to DB: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    generate_synthetic_data(50)
    import_csv_to_db()
