import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import get_settings
from app.core.security import verify_razorpay_signature
from app.models.customer import Customer
from app.models.payment import Payment, PaymentStatus
from app.models.recovery_attempt import PolicyDecision
from app.services import recovery_engine
from app.services.recovery_engine import log_audit

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger("recoverai.webhooks")
settings = get_settings()


@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str | None = Header(default=None),
):
    raw_body = await request.body()

    if settings.razorpay_webhook_secret:
        if not verify_razorpay_signature(raw_body, x_razorpay_signature or "", settings.razorpay_webhook_secret):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")

    payload = await request.json()
    event = payload.get("event")
    entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    razorpay_payment_id = entity.get("id")

    if event != "payment.failed":
        db.commit()
        return {"status": "ignored", "event": event}

    # Idempotency: Razorpay retries webhooks — never double-process the same payment id.
    existing = db.query(Payment).filter(Payment.razorpay_payment_id == razorpay_payment_id).first()
    if existing is not None:
        db.commit()
        return {"status": "duplicate_ignored", "payment_id": existing.id}

    customer_email = entity.get("email") or "unknown@example.com"
    customer_contact = entity.get("contact")
    customer = db.query(Customer).filter(Customer.email == customer_email).first()
    if customer is None:
        customer = Customer(name=customer_email.split("@")[0], email=customer_email, phone=customer_contact)
        db.add(customer)
        db.flush()

    payment = Payment(
        customer_id=customer.id,
        amount=(entity.get("amount", 0) or 0) / 100,  # Razorpay amounts are in paise
        currency=entity.get("currency", "INR"),
        status=PaymentStatus.FAILED,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_order_id=entity.get("order_id"),
        failure_reason=entity.get("error_description") or entity.get("error_reason"),
    )
    db.add(payment)
    db.flush()

    # Logged against the internal payment id (not the raw Razorpay id) so it
    # shows up in that payment's /audit/payment/{id} timeline alongside every
    # later event.
    log_audit(
        db,
        entity_type="payment",
        entity_id=payment.id,
        event_type="webhook_received",
        actor="system",
        payload={"event": event, "razorpay_payment_id": razorpay_payment_id},
    )

    # Immediately run it through the recovery pipeline: context -> AI -> policy
    # -> (if allowed) action. Keeps the dashboard live off real webhook traffic
    # without needing a background worker running.
    attempt = recovery_engine.evaluate(db, payment)
    if attempt.policy_decision == PolicyDecision.ALLOWED:
        recovery_engine.execute(db, attempt)

    db.commit()
    db.refresh(payment)

    return {"status": "recorded", "payment_id": payment.id, "attempt_id": attempt.id}


@router.get("/razorpay/verify")
def verify_signature(body: str, signature: str):
    """Utility endpoint for testing HMAC signature verification against a raw body string."""
    valid = verify_razorpay_signature(body.encode("utf-8"), signature, settings.razorpay_webhook_secret)
    return {"valid": valid}
