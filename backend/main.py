import os
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from backend.models.database import init_db
from backend.routers import patients, appointments, intake, followups, dashboard
from backend.middleware.rate_limiter import RateLimiterMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure database tables are created
init_db()

# ---------------------------------------------------------------------------
# Determine environment (set APP_ENV=development to enable /docs)
# ---------------------------------------------------------------------------
APP_ENV = os.environ.get("APP_ENV", "production").lower()
IS_DEV = APP_ENV == "development"

app = FastAPI(
    title="Clinic Appointment & Intake Summary API",
    description="Backend API for managing clinical patients, bookings, intakes, and follow-ups with administrative AI summaries.",
    version="1.0.0",
    # Disable interactive docs in production to reduce attack surface
    docs_url="/docs" if IS_DEV else None,
    redoc_url="/redoc" if IS_DEV else None,
    openapi_url="/openapi.json" if IS_DEV else None,
)

# ---------------------------------------------------------------------------
# Security Headers Middleware
# ---------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject defensive HTTP security headers on every response."""
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        # Only add HSTS on production (not on localhost)
        if not IS_DEV:
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response

# ---------------------------------------------------------------------------
# Middleware stack (order: outermost registered = outermost executed)
# Register from outermost to innermost.
# ---------------------------------------------------------------------------

# 1. Rate Limiter (outermost — blocks abusive clients before anything else runs)
app.add_middleware(RateLimiterMiddleware)

# 2. Security Headers
app.add_middleware(SecurityHeadersMiddleware)

# 3. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://clinicappointment23.netlify.app",
        "https://clinicappointment23.netlify.app/",
        "http://localhost:8080",
        "http://127.0.0.1:8080"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
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
        "version": "1.0.0"
    }
