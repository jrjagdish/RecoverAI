from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.payment import Payment, PaymentStatus
from app.models.recovery_attempt import RecoveryAttempt
from app.models.recovery_batch import BatchStatus, RecoveryBatch
from app.models.stopping_event import StoppingEvent
from app.schemas.dashboard import (
    ActionBreakdown,
    AnalyticsResponse,
    DashboardKpis,
    FailureReasonBreakdown,
)
from app.schemas.payment import PaymentRead

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/kpis", response_model=DashboardKpis)
def get_kpis(db: Session = Depends(get_db)):
    total_at_risk = db.query(func.coalesce(func.sum(RecoveryBatch.total_amount_at_risk), 0.0)).scalar()
    total_recovered = db.query(func.coalesce(func.sum(RecoveryBatch.total_amount_recovered), 0.0)).scalar()
    active_batches = db.query(func.count(RecoveryBatch.id)).filter(RecoveryBatch.status == BatchStatus.RUNNING).scalar()
    total_payments = db.query(func.count(Payment.id)).scalar()
    recovered_payments = db.query(func.count(Payment.id)).filter(Payment.status == PaymentStatus.RECOVERED).scalar()

    return DashboardKpis(
        total_amount_at_risk=total_at_risk,
        total_amount_recovered=total_recovered,
        recovery_rate=(total_recovered / total_at_risk) if total_at_risk else 0.0,
        active_batches=active_batches,
        total_payments=total_payments,
        recovered_payments=recovered_payments,
    )


@router.get("/failed-payments", response_model=list[PaymentRead])
def get_failed_payments(db: Session = Depends(get_db)):
    return (
        db.query(Payment)
        .filter(Payment.status.in_([PaymentStatus.FAILED, PaymentStatus.RETRYING]))
        .order_by(Payment.created_at.desc())
        .all()
    )


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    reason_rows = (
        db.query(
            func.coalesce(Payment.failure_reason, "unknown"),
            func.sum(Payment.amount),
            func.sum(func.case((Payment.status == PaymentStatus.RECOVERED, Payment.amount), else_=0)),
        )
        .group_by(func.coalesce(Payment.failure_reason, "unknown"))
        .all()
    )
    by_failure_reason = [
        FailureReasonBreakdown(
            failure_reason=reason,
            at_risk=at_risk or 0.0,
            recovered=recovered or 0.0,
            recovery_rate=(recovered / at_risk) if at_risk else 0.0,
        )
        for reason, at_risk, recovered in reason_rows
    ]

    action_rows = (
        db.query(RecoveryAttempt.executed_action, func.count(RecoveryAttempt.id))
        .filter(RecoveryAttempt.executed_action.is_not(None))
        .group_by(RecoveryAttempt.executed_action)
        .all()
    )
    by_action_type = [ActionBreakdown(action=action.value, count=count) for action, count in action_rows]

    stopping_rows = db.query(StoppingEvent.reason, func.count(StoppingEvent.id)).group_by(StoppingEvent.reason).all()
    stopping_breakdown = {reason.value: count for reason, count in stopping_rows}

    return AnalyticsResponse(
        by_failure_reason=by_failure_reason,
        by_action_type=by_action_type,
        stopping_breakdown=stopping_breakdown,
    )
