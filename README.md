# ClinicFlow — Clinic Appointment and Intake Summary System

> A clinic appointment booking and AI-assisted intake management system for patients and front-desk staff.

**Live Demo:** https://clinicappointment23.netlify.app/
**Track:** SDAI (HIMSHIKHAR 2026, July Cohort) — Project 03
**Domain:** Healthcare administration (not diagnosis)

---

## 1. Problem Statement

Front-desk clinic staff routinely juggle appointment scheduling and patient intake forms manually, which leads to missed information, slow follow-ups, and no easy way to spot which patients need attention before their visit.

**ClinicFlow** solves this by giving patients a simple way to book appointments and complete an intake form online, while giving staff a dashboard that:
- Shows all appointments and patient records in one place
- Uses an AI model to summarize each patient's intake form into a short, readable draft for staff
- Flags missing or incomplete fields in intake forms automatically
- Tracks follow-ups that still need to be completed

The system explicitly does **not** diagnose conditions or recommend treatment — it only supports the administrative workflow around a visit.

---

## 2. Dataset / Reference Source

Following the project's starter-data guidance, the system uses its own generated records rather than a public medical dataset (appropriate, since patient data is sensitive):

| File | Purpose |
|---|---|
| `patients.csv` | Patient records (name, contact info, history flags) |
| `appointments.csv` | Booked appointment slots, date/time, status |
| `intake_forms.csv` | Submitted intake form responses per patient |
| `followups.csv` | Follow-up items flagged by staff or by the AI module |

**[Add: how many records you generated for each file, and whether they're synthetic/fictional test data — this matters for the "responsible use" section since no real patient data should be used.]**

---

## 3. Tools Used

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | **[Add: e.g., Node.js/Express, Flask, FastAPI — whichever you used]** |
| Database | **[Add: e.g., SQLite, PostgreSQL, MySQL]** |
| AI / LLM | **[Add: which LLM API — e.g., OpenAI GPT-4o-mini, Anthropic Claude, etc.]** |
| Hosting | Netlify (frontend) |
| Version Control | GitHub |

---

## 4. Project Workflow

1. **Patient books an appointment** through the Patient Portal and fills out the intake form.
2. **Backend API** receives the booking and intake data and stores it in the database.
3. **AI module** is called with the intake form content. It:
   - Generates a short administrative summary of the patient's stated concerns
   - Flags any required fields that were left blank or incomplete
   - Drafts a suggested follow-up reminder where needed
4. **Staff Portal Dashboard** displays appointments, patients, and the AI-generated summaries, with a live Follow-ups counter for anything still needing action.
5. Staff review the AI draft (clearly labeled as **not medical advice**) and take the appropriate next step manually.

```
Patient → Frontend (Book + Intake Form) → Backend API → Database
                                              ↓
                                          AI Module → Summary + Missing-field flags
                                              ↓
                                   Staff Dashboard (Appointments, Patients, Follow-ups)
```

---

## 5. AI / Software Component

The AI component is the core innovation of this project:

- **Intake summarization** — condenses a patient's free-text and structured intake responses into a short draft for staff, so they don't have to read the raw form before every visit.
- **Missing-field detection** — checks the submitted intake form against required fields and flags what's missing, reducing back-and-forth at check-in.
- **Follow-up reminder drafts** — generates a short suggested follow-up note (e.g., "confirm insurance details before next visit") that staff can edit or dismiss.

**Why AI helps here:** these are exactly the kind of repetitive, judgment-light administrative tasks (summarizing, checking for gaps, drafting reminders) that an LLM handles reliably, while the actual clinical judgment stays entirely with staff. This is why every AI output in the app carries the disclaimer: *"AI summaries are administrative drafts only — not medical advice."*

**[Add: a short note on your prompt design — what you told the model to do/not do, and any guardrails you added, e.g. instructing it never to suggest a diagnosis.]**

---

## 6. How to Run the Project

**[Fill in with your actual setup steps, for example:]**

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd clinic_appointment_and_intake_summary_system

# 2. Install backend dependencies
cd backend
npm install        # or: pip install -r requirements.txt

# 3. Add your AI API key
echo "AI_API_KEY=your_key_here" > .env

# 4. Start the backend
npm start          # or: python app.py

# 5. Open the frontend
# Open index.html in a browser, or serve the /frontend folder
```

Live version (frontend only, connected to hosted backend): https://clinicappointment23.netlify.app/

---

## 7. Demo Screenshots

**[Add screenshots here — Dashboard, Book Appointment, Intake Form, AI Summary view, Follow-ups list]**

Example placeholders:
- `screenshots/dashboard.png`
- `screenshots/book-appointment.png`
- `screenshots/ai-summary.png`
- `screenshots/followups.png`

---

## 8. Results and Insights

**[Fill in with your actual numbers/observations, for example:]**
- Number of test appointments booked during testing: **[ ]**
- Number of intake forms processed by the AI module: **[ ]**
- Example: "AI correctly flagged missing fields in X out of Y test intake forms"
- Any noticeable pattern in follow-ups generated (e.g., insurance info most commonly missing)

---

## 9. Limitations

- The AI module produces **administrative drafts only** — it does not diagnose, and staff must review every summary before acting on it.
- AI summaries are only as good as the intake form content; ambiguous or very short patient input can produce a vague summary.
- The dataset used is synthetic/test data, not real patient records — real-world clinic data would include more edge cases (multiple languages, incomplete histories, etc.).
- **[Add: any known bugs, edge cases the system doesn't handle yet, or scale limitations.]**

---

## 10. Future Improvements

- Add authentication/role-based access so the Patient Portal and Staff Portal are properly separated by login.
- Add multi-language intake form support.
- Add analytics on follow-up completion rates over time.
- Allow staff to give feedback on AI summaries to improve prompt quality over time.

---

## 11. Responsible Use Note

This system is an **administrative support tool only**. It does not diagnose conditions, does not recommend treatment, and should not be used as a substitute for clinical judgment. All AI-generated content is explicitly labeled as a draft for staff review. No real patient data was used during development — only synthetic/test records.

---

## 12. Team Members

**[Add team member name(s) here]**

