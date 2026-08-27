"""Recovery Engine: orchestrates context assembly -> AI -> policy -> action.

Two-step by design (mirrors the API surface):
  evaluate()  — load context, get the AI recommendation, run it through the
                policy engine, and persist a RecoveryAttempt + audit trail.
                No side effects on the outside world happen here.
  execute()   — takes an already-evaluated (and policy-allowed) attempt and
                calls the Action Executor, then records the outcome.
"""

from datetime import datetime,UTC

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.customer import Customer
from app.models.payment import Payment, PaymentStatus
from app.models.recovery_attempt import AttemptOutcome, PolicyDecision, RecoveryAttempt
from app.models.recovery_batch import RecoveryBatch
from app.models.stopping_event import StoppingEvent
from app.services import action_executor, ai_service, policy_engine


def log_audit(db: Session, *, entity_type: str, entity_id: str, event_type: str, actor: str, payload: dict) -> None:
    db.add(
        AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            actor=actor,
            payload_json=payload,
        )
    )


def build_context(db: Session, payment: Payment) -> dict:
    customer = payment.customer
    prior_attempts = (
        db.query(RecoveryAttempt)
        .filter(RecoveryAttempt.payment_id == payment.id)
        .order_by(RecoveryAttempt.attempt_number)
        .all()
    )

    return {
        "payment": {
            "id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "status": payment.status.value,
            "failure_reason": payment.failure_reason,
            "created_at": payment.created_at.isoformat(),
        },
        "customer": {
            "id": customer.id,
            "email": customer.email,
            "opted_out": customer.opted_out,
            "contact_consent": customer.contact_consent,
            "contact_quiet_hours": customer.contact_quiet_hours,
        },
        "attempt_history": {
            "attempt_count": len(prior_attempts),
            "prior_actions": [a.executed_action.value for a in prior_attempts if a.executed_action],
            "prior_outcomes": [a.outcome.value for a in prior_attempts],
        },
    }


def evaluate(db: Session, payment: Payment) -> RecoveryAttempt:
    context = build_context(db, payment)

    decision = ai_service.get_recommended_action(context)
    log_audit(
        db,
        entity_type="payment",
        entity_id=payment.id,
        event_type="ai_recommendation",
        actor="ai",
        payload=decision.to_json(),
    )

    result = policy_engine.evaluate_policy(
        recommended_action=decision.recommended_action,
        customer=context["customer"],
        payment=context["payment"],
        attempt_history=context["attempt_history"],
    )
    log_audit(
        db,
        entity_type="payment",
        entity_id=payment.id,
        event_type="policy_decision",
        actor="policy_engine",
        payload={
            "allowed": result.allowed,
            "final_action": result.final_action.value,
            "reason": result.reason,
        },
    )

    attempt = RecoveryAttempt(
        payment_id=payment.id,
        batch_id=payment.batch_id,
        attempt_number=context["attempt_history"]["attempt_count"] + 1,
        ai_recommended_action=decision.recommended_action,
        ai_confidence=decision.confidence,
        ai_reason=decision.to_json(),
        policy_decision=PolicyDecision.ALLOWED if result.allowed else PolicyDecision.BLOCKED,
        policy_reason=result.reason,
        final_action=result.final_action,
    )
    db.add(attempt)

    if result.stopping_reason is not None:
        db.add(StoppingEvent(payment_id=payment.id, reason=result.stopping_reason))
        payment.status = PaymentStatus.STOPPED

    db.flush()
    return attempt


def execute(db: Session, attempt: RecoveryAttempt) -> RecoveryAttempt:
    payment = attempt.payment
    customer = payment.customer
    action = attempt.final_action

    result = action_executor.execute_action(
        action,
        customer={"id": customer.id, "email": customer.email},
        payment={
            "id": payment.id,
            "amount": payment.amount,
            "currency": payment.currency,
            "failure_reason": payment.failure_reason,
        },
    )

    attempt.executed_action = action
    attempt.channel = result.channel
    attempt.sent_at = result.sent_at
    attempt.outcome = AttemptOutcome.PENDING if result.success else AttemptOutcome.FAILED

    log_audit(
        db,
        entity_type="payment",
        entity_id=payment.id,
        event_type="action_executed",
        actor="system",
        payload={"action": action.value, "success": result.success, "detail": result.detail},
    )

    if payment.status == PaymentStatus.FAILED:
        payment.status = PaymentStatus.RETRYING

    db.flush()
    return attempt


def mark_outcome(db: Session, attempt: RecoveryAttempt, outcome: AttemptOutcome) -> RecoveryAttempt:
    attempt.outcome = outcome
    attempt.outcome_at = datetime.now(UTC)()

    payment = attempt.payment
    if outcome == AttemptOutcome.RECOVERED:
        payment.status = PaymentStatus.RECOVERED
        payment.recovered_at = attempt.outcome_at
        if payment.batch is not None:
            batch: RecoveryBatch = payment.batch
            batch.total_amount_recovered += payment.amount
            batch.recovered_count += 1

    log_audit(
        db,
        entity_type="payment",
        entity_id=payment.id,
        event_type="outcome_recorded",
        actor="system",
        payload={"outcome": outcome.value},
    )
    db.flush()
    return attempt
