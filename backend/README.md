# RecoverAI backend (FastAPI)

## Setup

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env
```

## Run

```bash
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs
Health check: http://localhost:8000/health

SQLite is used by default (`recoverai.db`), created automatically on startup — no
external DB needed to get going. Swap `DATABASE_URL` in `.env` for Postgres when
ready.

## Seed demo data

Populates customers, a batch, and runs every payment through
AI -> policy -> action so the dashboard has data immediately (including one
policy-blocked attempt and one stopping-rule trigger):

```bash
python seed.py
```

## Background jobs (optional)

Only needed for async/scheduled evaluation — the synchronous API endpoints work
without it.

```bash
celery -A app.celery_app worker --loglevel=info
```

## Structure

```
app/
  models/       SQLAlchemy models (customers, payments, batches, attempts, audit_log, stopping_events)
  schemas/      Pydantic request/response models
  services/
    ai_service.py        the only place an LLM is called; structured JSON output
    policy_engine.py      pure, deterministic, unit-testable veto function
    action_executor.py    the only place side effects (sending email etc.) happen
    recovery_engine.py    orchestrates context -> AI -> policy -> action
  api/routes/    FastAPI routers, one per resource
  celery_app.py / tasks.py   background jobs
  main.py        app factory, router wiring, CORS, startup table creation
```

## Design notes

- The AI never acts directly — `ai_service.py` only returns a recommendation;
  `policy_engine.py` decides whether it's allowed to run.
- `policy_engine.evaluate_policy` takes plain dicts, not ORM objects, and has no
  side effects — write unit tests against it directly without a DB.
- Razorpay webhooks are verified via HMAC (`core/security.py`) and de-duplicated
  by `razorpay_payment_id` before processing (idempotent).
