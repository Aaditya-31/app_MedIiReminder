# MediReminder — AI Appointment Reminder Platform

An AI-powered appointment reminder system and clinical decision engine for medical practices. Reduces no-shows by intelligently deciding whether to send **SMS**, **Email**, or **Phone Call** reminders based on patient risk metrics, age, visit history, and clinical urgency.

---

## Tech Stack

| Layer | Technology | Description |
|-------|-----------|-------------|
| **Backend** | Python + FastAPI | High-performance asynchronous API server |
| **Database** | SQLite + SQLAlchemy | Zero-config file-based storage (`reminders.db`) with automatic data seeding |
| **Frontend** | React + Vite + Vanilla CSS | Responsive SPA using the premium **Professional Slate** medical aesthetic |
| **AI Inference**| Groq API (`qwen/qwen3-32b`) | High-speed LLM inference for drafting tailored reminder messages and answering staff chat queries |

---

## Core Features & Workflow

### 1. The 4-Step Rule-Based Decision Engine
To ensure clinical accuracy and avoid inappropriate automated outreach, channel assignment strictly adheres to a hierarchical, priority-ordered decision engine:

```
STEP 4 — Priority Overrides (Evaluated First)
  • No-show risk > 80%      → PHONE_CALL (High Priority)
  • Appointment within 24h  → SMS (Ensures immediate patient visibility)
  • Elderly + Critical + Missed → PHONE_CALL (High Priority escalation)

STEP 1 — Appointment Type Urgency
  • Critical (Surgery, Cardiology, Cancer...) → PHONE_CALL
  • Moderate (Telemedicine, Pediatric...)     → EMAIL (For instruction delivery)
  • Simple (General Checkup, Vaccination...) → SMS

STEP 2 — Patient Visit History
  • Prior No-Shows >= 2     → PHONE_CALL (High Priority)
  • Missed Last Visit       → PHONE_CALL
  • New Patient (Visits=0)  → EMAIL (Detailed onboarding and directions)

STEP 3 — Demographics & Age Tiers
  • Age >= 60               → PHONE_CALL (Prioritizes direct auditory verification)
  • Age < 18                → EMAIL (Aimed at parents/guardians)
  • Age 18–59               → SMS
```

### 2. High-Speed AI Message Drafting
Once the decision engine computes the target channel and reasoning checkpoints, the local context is passed to the **Groq LLM** to draft a highly professional, clinical-appropriate message. 
* **Strict Constraints**: Output is post-processed to remove unnecessary `<think>` blocks, markdown formatting, or template placeholders, outputting directly under the reliable **Medi Clinic** brand signature.

### 3. Integrated AI Assistant Chatbot
A robust conversational assistant is permanently docked in the bottom-right corner of the interface. Staff can ask natural language questions regarding scheduled loads, specific patient histories, or queue summaries. Responses are cleanly formatted using a native **Markdown Renderer**.

### 4. Staff Management Dashboard
* **Manual Entry & Creation**: Easily add appointments with full historical context inputs (past visits, past no-shows).
* **Cascading Deletions**: Seamlessly delete canceled or invalid appointments with fully synchronized removal of associated reminder queue items.
* **Review & Dispatch**: Review detailed AI reasoning point-by-point, edit drafted output directly in the card view, approve, and execute simulated dispatches complete with execution timestamps and confirmation modals.

---

## Quick Start

### Prerequisites
- **Python** 3.10+
- **Node.js** 18+
- **PowerShell** (Windows environment)

### 1. Configure API Keys
Set up your high-speed Groq API credentials in `backend/.env`:
```env
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=qwen/qwen3-32b
```

### 2. Launch the Application
Run the automated unified launcher script to activate the virtual environment, verify packages, and concurrently spin up both client and server nodes:

```powershell
.\start.ps1
```

#### Manual Startup Alternative:

**Terminal 1 — Backend API:**
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Terminal 2 — Frontend Client:**
```powershell
cd frontend
npm install
npm run dev
```

### Access URLs
- **Frontend Dashboard**: [http://localhost:5173](http://localhost:5173)
- **Backend API Base**: [http://localhost:8000](http://localhost:8000)
- **Interactive Swagger API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API Endpoints Reference

| Method | Route | Scope | Description |
|--------|-------|-------|-------------|
| **GET** | `/api/appointments` | Appointments | Lists all active patient appointments and underlying risk models |
| **POST** | `/api/appointments` | Appointments | Registers a new appointment and calculates baseline initial risk |
| **DELETE**| `/api/appointments/{id}`| Appointments | Deletes an appointment and cascades reminder removal |
| **GET** | `/api/queue` | Reminder Queue | Lists all AI-drafted reminders awaiting or completing review |
| **POST** | `/api/run-agent` | Reminder Queue | Instructs the decision engine and LLM to process unqueued appointments |
| **PATCH**| `/api/queue/{id}/approve`| Reminder Queue | Marks a specific draft reminder as staff-approved |
| **PATCH**| `/api/queue/{id}/edit` | Reminder Queue | Persists custom textual edits to the drafted message |
| **POST** | `/api/queue/{id}/dispatch`| Reminder Queue | Triggers zero-send simulated dispatching and logs timestamps |
| **POST** | `/api/chat` | AI Chatbot | Streams contextual prompt context to the assistant for staff triage |

---

## Clinical Impact & Future Enhancements (What I Would Do Next)

### 1. Real SMS & Email Integration
Currently, reminder dispatches are simulated within the dashboard.
- **Future Work**: Send real SMS using **Twilio** and real emails using **SendGrid**.
- **Why it's easy**: The integration APIs are very simple. We just need to replace the simulated dispatch logging with actual API calls.

### 2. Appointment Confirmation Button
Enable patients to respond directly to incoming reminder messages.
- **Future Work**: Add **“Confirm Appointment”** and **“Cancel Appointment”** actions inside reminder messages (e.g., instructing the patient to *"Reply YES to confirm"*).
- **Why it's easy**: We simply update the appointment status directly in the database based on the reply. No advanced AI analysis is needed for this workflow.

### 3. Multi-Language Reminder Messages
Support diverse patient demographics by automatically generating localized reminders.
- **Future Work**: Add support for **English**, **Tamil**, and **Hindi**.
- **Why it's easy**: Can be implemented straightforwardly using translation APIs or simple predefined message templates.

---

## Project Submission & Details

### Time Budget & Hours Spent
- **Total Time Spent**: ~5 hours total.

### AI Coding Agents Used & Corrections Required
- **Primary Agent**: **Antigravity (Google DeepMind)**
- **Scope of Usage**: Scaffolded the full application structure, FastAPI backend endpoints, database seed scripts, React components, and integration pipelines.
- **What the Agent Got Wrong & Manual Fixes Required**:
  1. **Missing Fallback Handling**: If the Groq API failed or timed out, reminder generation completely broke. **Fix**: Added deterministic fallback reminder templates and timeout-safe response handling so that even if the AI endpoint fails, the reminder dispatch system still operates reliably.
  2. **Weak Clinical Formatting**: The generated reminders sometimes sounded too casual, used inconsistent formatting, and lacked a proper clinic signature. **Fix**: Enforced a professional healthcare tone, uniform formatting rules, and a branded clinic signature to maximize readability, professionalism, and patient trust.

