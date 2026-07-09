"""
Data loader: seeds the database from the sample CSV files in /data.
Run once before starting the server: python -m src.load_data
"""
import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.models.database import SessionLocal, Patient, Appointment, IntakeForm, FollowUp, init_db

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


def load_csv(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def seed():
    init_db()
    db = SessionLocal()

    try:
        # --- Patients ---
        if db.query(Patient).count() == 0:
            rows = load_csv("patients.csv")
            for r in rows:
                db.add(Patient(
                    patient_id=r["patient_id"],
                    full_name=r["full_name"],
                    dob=r["dob"],
                    gender=r.get("gender"),
                    phone=r["phone"],
                    email=r["email"],
                    address=r["address"],
                    emergency_contact_name=r["emergency_contact_name"],
                    emergency_contact_phone=r["emergency_contact_phone"],
                ))
            db.commit()
            print(f"  Loaded {len(rows)} patients.")
        else:
            print("  Patients already loaded, skipping.")

        # --- Appointments ---
        if db.query(Appointment).count() == 0:
            rows = load_csv("appointments.csv")
            for r in rows:
                db.add(Appointment(
                    appointment_id=r["appointment_id"],
                    patient_id=r["patient_id"],
                    clinician_name=r["clinician_name"],
                    department=r["department"],
                    appointment_date=r["appointment_date"],
                    appointment_time=r["appointment_time"],
                    status=r.get("status", "requested"),
                    reason_for_visit=r["reason_for_visit"],
                ))
            db.commit()
            print(f"  Loaded {len(rows)} appointments.")
        else:
            print("  Appointments already loaded, skipping.")

        # --- Intake Forms ---
        if db.query(IntakeForm).count() == 0:
            import json
            rows = load_csv("intake_forms.csv")
            for r in rows:
                missing = []
                required_keys = ["symptoms_description", "current_medications", "allergies",
                                 "insurance_provider", "insurance_id", "preferred_language"]
                filled = 0
                for key in required_keys:
                    val = r.get(key, "").strip()
                    if not val or val.lower() in ["none", "n/a"]:
                        missing.append(key)
                    else:
                        filled += 1
                score = filled / len(required_keys)

                db.add(IntakeForm(
                    intake_id=r["intake_id"],
                    appointment_id=r["appointment_id"],
                    patient_id=r["patient_id"],
                    symptoms_description=r.get("symptoms_description"),
                    current_medications=r.get("current_medications"),
                    allergies=r.get("allergies"),
                    insurance_provider=r.get("insurance_provider"),
                    insurance_id=r.get("insurance_id"),
                    preferred_language=r.get("preferred_language", "English"),
                    consent_given=r.get("consent_given", "true").lower() == "true",
                    ai_summary=r.get("ai_summary") or None,
                    missing_fields=json.dumps(missing),
                    completeness_score=score,
                    urgent_review_needed=r.get("urgent_review_needed", "false").lower() == "true",
                ))
            db.commit()
            print(f"  Loaded {len(rows)} intake forms.")
        else:
            print("  Intake forms already loaded, skipping.")

        # --- Follow-ups ---
        if db.query(FollowUp).count() == 0:
            rows = load_csv("followups.csv")
            for r in rows:
                db.add(FollowUp(
                    followup_id=r["followup_id"],
                    appointment_id=r["appointment_id"],
                    patient_id=r["patient_id"],
                    followup_type=r["followup_type"],
                    message_draft=r.get("message_draft"),
                    status=r.get("status", "draft"),
                ))
            db.commit()
            print(f"  Loaded {len(rows)} follow-ups.")
        else:
            print("  Follow-ups already loaded, skipping.")

        print("\nDatabase seeded successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("Seeding database from CSV files...")
    seed()
