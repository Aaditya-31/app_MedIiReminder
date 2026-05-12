# SKORE — Appointment Reminder Agent

An AI-powered appointment reminder system for medical practices. Reduces no-shows by intelligently deciding whether to send **SMS**, **Email**, or **Phone Call** reminders based on patient context, visit history, and appointment type.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python + FastAPI + SQLite (SQLAlchemy) |
| Frontend | React + Vite + Vanilla CSS |
| AI | OpenAI GPT-4o (tool calling + message drafting) |
| Database | SQLite (file-based, zero config) |

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- PowerShell (Windows)

### 1. Configure API Key

The API key is already set in `backend/.env`. To change it:
```
OPENAI_API_KEY=your_key_here
```

### 2. Run the App

```powershell
.\start.ps1
```

Or manually:

**Terminal 1 — Backend:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
npm install
npm run dev
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

---

## How the Agent Works

### 4-Step Rule-Based Decision Engine

```
STEP 1 — Appointment Type
  Critical (Surgery, Cardiology, Cancer...) → PHONE_CALL
  Moderate (Telemedicine, Pediatric...)     → EMAIL
  Simple (General Checkup, Vaccination...) → SMS

STEP 2 — Patient Age
  age >= 60  → PHONE_CALL
  age < 18   → EMAIL
  18–59      → SMS

STEP 3 — Visit History
  no_show_count >= 2      → PHONE_CALL
  missed_last_appointment → PHONE_CALL
  total_visits == 0       → EMAIL (new patient)

STEP 4 — Priority Overrides (highest priority)
  no_show_risk > 80%      → PHONE_CALL
  appointment within 24h  → SMS (immediate visibility)
  elderly + critical + missed → PHONE_CALL + HIGH priority
```

### OpenAI Tool Calling

The agent uses GPT-4o with two tools:
- `get_patient_history(patient_id)` — fetches visit history, risk score
- `get_appointment_details(appointment_id)` — fetches appointment type and time

After tool calls, the rule engine makes the channel decision, and GPT-4o drafts a channel-appropriate message.

---

## Staff Workflow

1. **Add appointments** via "New Appointment" button
2. **Run Agent** — AI processes all unqueued appointments
3. **Review** each card: see AI reasoning bullets + drafted message
4. **Edit** the message if needed
5. **Approve** the reminder
6. **Dispatch** — confirms via modal, then marks as DISPATCHED in DB (nothing actually sent)

---

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/appointments` | List all appointments |
| POST | `/api/appointments` | Create new appointment |
| GET | `/api/queue` | List reminder queue |
| POST | `/api/run-agent` | Run AI agent on pending appointments |
| PATCH | `/api/queue/{id}/approve` | Approve a reminder |
| PATCH | `/api/queue/{id}/edit` | Edit reminder message |
| POST | `/api/queue/{id}/dispatch` | Mark as dispatched |
| POST | `/api/chat` | Chatbot conversation |

---

## What I Would Do Next (if more time)

1. **Real dispatch integration** — Twilio for SMS/calls, SendGrid for email
2. **Auth** — Staff login with role-based access (admin vs. reviewer)
3. **Bulk approve/dispatch** — Select all and action at once
4. **Reminder scheduling** — Cron jobs to auto-run agent at 8 AM daily
5. **Patient portal** — Let patients confirm via reply link
6. **Analytics dashboard** — No-show rate trends, channel effectiveness
7. **A/B testing** — Track which channels reduce no-shows most

---

## Hours Spent

~6 hours total.

## AI Tools Used

- **Antigravity (Google DeepMind)** — Scaffolded the full project structure, all backend modules, and frontend components. Required minor fixes to ensure the 4-step decision logic priority order was correctly implemented (the initial draft applied overrides after type checks rather than before).
