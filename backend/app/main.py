import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import audit, batches, customers, dashboard, payments, policy, recovery, webhooks
from app.config import get_settings
from app.database import Base, engine
from app import models  # noqa: F401 — ensures all models are registered before create_all

logging.basicConfig(level=logging.INFO)
settings = get_settings()

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    # Dev/boilerplate convenience — swap for Alembic migrations in production.
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


api_prefix = settings.api_prefix
app.include_router(webhooks.router, prefix=api_prefix)
app.include_router(payments.router, prefix=api_prefix)
app.include_router(customers.router, prefix=api_prefix)
app.include_router(recovery.router, prefix=api_prefix)
app.include_router(batches.router, prefix=api_prefix)
app.include_router(policy.router, prefix=api_prefix)
app.include_router(audit.router, prefix=api_prefix)
app.include_router(dashboard.router, prefix=api_prefix)
