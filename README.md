# LockIn — Cash-Flow Optimization MVP

[Read the full product details here](https://docs.google.com/document/d/1PG0GcXqwu7BQtJ332-JaB9uxEqcglK2c7zkYeLpSkO4/edit)

**LockIn** is a zero-storage personal cash-flow optimization web app. Instead of requiring bank logins via Plaid, LockIn connects via read-only email OAuth (Gmail / Outlook), audits recent receipts and subscription bills strictly in memory, flags recurring bloat and silent price creep, and models 5- and 10-year compound wealth projections.

## Core Principles

- **Zero Bank Credentials:** Uses short-lived, read-only OAuth scopes (`gmail.readonly` / `Mail.Read`).
- **Zero-Storage Privacy:** Email fetching and regex PII sanitization happen strictly in RAM—no database persistence, no logged email bodies or tokens.
- **Deterministic Financial Math:** Gemini extracts structured receipt data via strict JSON schemas, while Python (`Decimal`) computes recurring totals, price increases, and compound return projections.

---

## Architecture & Pipeline

1. **Frontend (`frontend/`):** React + JavaScript (Vite) single-page app that initiates OAuth, posts the short-lived access token to the backend, renders the audit dashboard, and exports results to CSV in the browser.
2. **Backend (`backend/`):** Stateless Python (FastAPI) service exposing `POST /api/audit`:
   - **Targeted Email Fetch:** Pulls up to 200 receipt/invoice/subscription/statement emails from the last 365 days.
   - **In-Memory PII Sanitization:** Strips names, street addresses, phone numbers, email addresses, and account/card digits before LLM processing.
   - **Structured LLM Extraction:** Batch-parses anonymized snippets with **Gemini 2.5 Flash** (Google AI Studio Free Tier) into a strict JSON schema.
   - **Deterministic Optimization Engine:** Flags recurring spend, duplicate categories, and price creep, and computes 5- and 10-year compound growth (~7% annual benchmark).
   - **Ephemeral Cleanup:** Returns the audit JSON and discards all in-memory session data.

---

## Repository Structure

```text
LockIn/
├── .env.example          # Template for required environment variables
├── .gitignore            # Protects .env secrets, build artifacts, and virtualenvs
├── README.md             # Project overview and local setup guide
├── backend/              # Stateless Python (FastAPI) service
│   ├── app/
│   │   ├── api/          # HTTP endpoints (POST /api/audit, GET /health)
│   │   ├── fixtures/     # Mock receipt snippets for zero-quota local testing
│   │   ├── schemas/      # Pydantic models & Gemini structured JSON schemas
│   │   └── services/     # Email ingestion, PII redactor, LLM client, financial math
│   └── tests/            # Unit tests for PII sanitization and deterministic math
└── frontend/             # React + JavaScript (Vite) single-page web app
    ├── public/           # Static assets and Privacy Policy page
    └── src/
        ├── components/   # OAuth connect controls, bloat alerts, projection cards (.jsx)
        └── services/     # Backend API client, OAuth helper, compound math & CSV export (.js)
```

---

## Environment Setup

1. Copy `.env.example` to `.env` in the repository root and populate your keys:

   ```bash
   cp .env.example .env
   ```

2. Required variables in `.env`:
   - `OAUTH_CLIENT_ID`: OAuth 2.0 Web Client ID (Google Cloud Console, `gmail.readonly` scope in Testing mode).
   - `OAUTH_CLIENT_SECRET`: OAuth 2.0 Client Secret (if using backend authorization-code exchange; never exposed to the browser).
   - `GEMINI_API_KEY`: Google AI Studio Free Tier API key (created on an unbilled GCP project).

---

## Running Locally (Once Scaffolded)

### 1. Backend (`localhost:8000`)

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (`localhost:5173`)

```bash
cd frontend
npm install
npm run dev
```

