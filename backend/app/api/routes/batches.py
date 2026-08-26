from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_or_404
from app.models.payment import Payment, PaymentStatus
from app.models.recovery_attempt import RecoveryAttempt
from app.models.recovery_batch import BatchStatus, RecoveryBatch
from app.models.stopping_event import StoppingEvent
from app.schemas.batch import BatchCreate, BatchRead, BatchReport

router = APIRouter(prefix="/batches", tags=["batches"])


@router.post("", response_model=BatchRead)
def create_batch(body: BatchCreate, db: Session = Depends(get_db)):
    query = db.query(Payment).filter(Payment.status == PaymentStatus.FAILED, Payment.batch_id.is_(None))
    if body.payment_ids:
        query = query.filter(Payment.id.in_(body.payment_ids))
    payments = query.all()

    if not payments:
        raise HTTPException(status_code=400, detail="No eligible failed payments found for this batch")

    batch = RecoveryBatch(
        name=body.name,
        status=BatchStatus.RUNNING,
        total_amount_at_risk=sum(p.amount for p in payments),
        total_payments_count=len(payments),
    )
    db.add(batch)
    db.flush()

    for payment in payments:
        payment.batch_id = batch.id

    db.commit()
    db.refresh(batch)
    return batch


@router.get("", response_model=list[BatchRead])
def list_batches(db: Session = Depends(get_db)):
    return db.query(RecoveryBatch).order_by(RecoveryBatch.started_at.desc()).all()


@router.get("/{batch_id}", response_model=BatchRead)
def get_batch(batch_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, RecoveryBatch, batch_id, "batch")


@router.get("/{batch_id}/report", response_model=BatchReport)
def get_batch_report(batch_id: str, db: Session = Depends(get_db)):
    batch = get_or_404(db, RecoveryBatch, batch_id, "batch")

    recovery_rate = (
        batch.total_amount_recovered / batch.total_amount_at_risk if batch.total_amount_at_risk else 0.0
    )

    stopping_rows = (
        db.query(StoppingEvent.reason, func.count(StoppingEvent.id))
        .join(Payment, Payment.id == StoppingEvent.payment_id)
        .filter(Payment.batch_id == batch_id)
        .group_by(StoppingEvent.reason)
        .all()
    )
    stopping_breakdown = {reason.value: count for reason, count in stopping_rows}

    action_rows = (
        db.query(RecoveryAttempt.executed_action, func.count(RecoveryAttempt.id))
        .filter(RecoveryAttempt.batch_id == batch_id, RecoveryAttempt.executed_action.is_not(None))
        .group_by(RecoveryAttempt.executed_action)
        .all()
    )
    action_breakdown = {action.value: count for action, count in action_rows}

    return BatchReport(
        **BatchRead.model_validate(batch).model_dump(),
        recovery_rate=recovery_rate,
        stopping_breakdown=stopping_breakdown,
        action_breakdown=action_breakdown,
    )
