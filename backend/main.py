from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.models.database import init_db
from backend.routers import patients, appointments, intake, followups, dashboard

# Ensure database tables are created
init_db()

app = FastAPI(
    title="Clinic Appointment & Intake Summary API",
    description="Backend API for managing clinical patients, bookings, intakes, and follow-ups with administrative AI summaries.",
    version="1.0.0"
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(patients.router)
app.include_router(appointments.router)
app.include_router(intake.router)
app.include_router(followups.router)
app.include_router(dashboard.router)

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "Clinic Appointment and Intake Summary API",
        "documentation": "/docs"
    }
