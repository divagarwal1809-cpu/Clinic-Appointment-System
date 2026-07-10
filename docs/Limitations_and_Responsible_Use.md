# Limitations and Responsible Use — ClinicFlow

**Project:** Clinic Appointment and Intake Summary System
**Live Demo:** https://clinicappointment23.netlify.app/

---

## What This System Is

ClinicFlow is a **healthcare administration** tool. It helps patients book appointments and complete intake forms, and helps staff review that intake data faster by generating summaries, flagging missing information, and drafting follow-up reminders.

## What This System Is Not

- It is **not** a diagnostic tool. It does not interpret symptoms or suggest what condition a patient might have.
- It does **not** recommend treatment, medication, or any clinical course of action.
- It is **not** a replacement for a clinician's judgment. Every AI-generated output is a draft for a human to review, not a decision.

This boundary is enforced in the product itself: every AI summary in the UI is labeled **"AI summaries are administrative drafts only — not medical advice."**

---

## Known Limitations

1. **AI output quality depends on input quality.** If a patient's intake answers are vague or very short, the generated summary will be similarly vague. Staff should treat every summary as a starting point, not a final read of the patient's situation.
2. **Missing-field detection is rule/field-based, not clinical.** It checks whether required fields were filled in — it does not judge whether an answer is medically adequate or complete.
3. **All data used in development is synthetic.** Patient records, appointments, and intake forms used for building and testing this project are fictional test data — no real patient information was used. **[Confirm this is true for your build, and note the number of synthetic records used per file.]**
4. **No authentication/role separation yet.** The Patient Portal and Staff Portal are not currently gated behind separate logins — this would need to be added before any real-world deployment. **[Confirm current auth status of your build.]**


---

## Responsible Use Guidelines

- Staff should **always read and confirm** an AI-generated summary before acting on it — never act on the summary alone.
- The system should **never be presented to patients** as offering medical advice, diagnosis, or treatment guidance.
- Any real deployment (beyond a class project/prototype) would require: proper authentication, encrypted storage of patient data, compliance review (e.g., HIPAA or local equivalent depending on jurisdiction), and a human-in-the-loop process for every AI-generated output.
- This project is a **prototype built for a learning exercise** and has not undergone the security, privacy, or compliance review that a real clinical deployment would require.

---

## Summary Statement (for README / report / demo video)

> ClinicFlow is an administrative support tool for clinic appointment and intake workflows. It does not diagnose conditions or recommend treatment. All AI-generated content is clearly labeled as a draft for staff review, and all data used in this project is synthetic test data, not real patient information.
