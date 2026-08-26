"""Background jobs: same exponential-backoff muscle as a webhook retry gateway,
reused here for scheduled follow-ups on payments that haven't responded yet.
"""

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models.payment import Payment, PaymentStatus
from app.services import recovery_engine


@celery_app.task(name="recoverai.evaluate_payment")
def evaluate_payment_task(payment_id: str) -> str:
    db = SessionLocal()
    try:
        payment = db.get(Payment, payment_id)
        if payment is None:
            return "not_found"
        attempt = recovery_engine.evaluate(db, payment)
        db.commit()
        return attempt.id
    finally:
        db.close()


@celery_app.task(name="recoverai.follow_up_stale_attempts")
def follow_up_stale_attempts(max_age_hours: int = 48) -> int:
    """Scheduled (e.g. via celery beat) to re-evaluate payments stuck in RETRYING
    with no response after `max_age_hours`."""
    db = SessionLocal()
    try:
        stale_payments = db.query(Payment).filter(Payment.status == PaymentStatus.RETRYING).all()
        for payment in stale_payments:
            recovery_engine.evaluate(db, payment)
        db.commit()
        return len(stale_payments)
    finally:
        db.close()
