from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_or_404
from app.models.payment import Payment, PaymentStatus
from app.models.recovery_attempt import RecoveryAttempt
from app.schemas.attempt import RecoveryAttemptRead
from app.schemas.payment import PaymentRead

router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("", response_model=list[PaymentRead])
def list_payments(
    status: PaymentStatus | None = None,
    batch_id: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Payment)
    if status is not None:
        query = query.filter(Payment.status == status)
    if batch_id is not None:
        query = query.filter(Payment.batch_id == batch_id)
    return query.order_by(Payment.created_at.desc()).all()


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, Payment, payment_id, "payment")


@router.get("/{payment_id}/attempts", response_model=list[RecoveryAttemptRead])
def get_payment_attempts(payment_id: str, db: Session = Depends(get_db)):
    get_or_404(db, Payment, payment_id, "payment")
    return (
        db.query(RecoveryAttempt)
        .filter(RecoveryAttempt.payment_id == payment_id)
        .order_by(RecoveryAttempt.attempt_number)
        .all()
    )
