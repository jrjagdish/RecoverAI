from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_or_404
from app.models.payment import Payment
from app.models.recovery_attempt import PolicyDecision, RecoveryAttempt
from app.schemas.attempt import RecoveryAttemptRead
from app.schemas.payment import PaymentRead
from app.services import recovery_engine

router = APIRouter(prefix="/recovery", tags=["recovery"])


@router.post("/evaluate/{payment_id}", response_model=RecoveryAttemptRead)
def evaluate_payment(payment_id: str, db: Session = Depends(get_db)):
    payment = get_or_404(db, Payment, payment_id, "payment")
    attempt = recovery_engine.evaluate(db, payment)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.get("/attempts/{attempt_id}", response_model=RecoveryAttemptRead)
def get_attempt(attempt_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, RecoveryAttempt, attempt_id, "recovery attempt")


@router.post("/attempts/{attempt_id}/execute", response_model=RecoveryAttemptRead)
def execute_attempt(attempt_id: str, db: Session = Depends(get_db)):
    attempt = get_or_404(db, RecoveryAttempt, attempt_id, "recovery attempt")
    if attempt.policy_decision == PolicyDecision.BLOCKED:
        raise HTTPException(status_code=409, detail=f"Attempt was blocked by policy: {attempt.policy_reason}")
    if attempt.executed_action is not None:
        raise HTTPException(status_code=409, detail="Attempt was already executed")

    attempt = recovery_engine.execute(db, attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


@router.post("/payments/{payment_id}/mark-recovered", response_model=PaymentRead)
def mark_payment_recovered(payment_id: str, db: Session = Depends(get_db)):
    """Manual reconciliation — the same effect a `payment.captured` webhook
    has, for cases it can't reach automatically (no matching order id, testing,
    or a channel outside Razorpay). Idempotent: re-marking an already-recovered
    payment is a no-op."""
    payment = get_or_404(db, Payment, payment_id, "payment")
    payment = recovery_engine.reconcile_recovered(db, payment, source="manual")
    db.commit()
    db.refresh(payment)
    return payment
