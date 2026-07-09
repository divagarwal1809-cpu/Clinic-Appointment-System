import os
from src.preprocessing import generate_synthetic_data, import_csv_to_db

def main():
    print("Initializing Clinic Appointment and Intake Summary System Database...")
    # Check if data CSVs exist, if not generate them
    if not os.path.exists("data/patients.csv") or not os.path.exists("clinic.db"):
        print("CSV files or database missing. Generating synthetic clinical data...")
        generate_synthetic_data(50)
        import_csv_to_db()
    else:
        print("Database and CSV files already exist. Seeding fresh database...")
        import_csv_to_db()
    print("Database seeding completed.")

if __name__ == "__main__":
    main()
