"""Action Executor: the only component allowed to touch the outside world.

V1 supports two channels: email (retry link + nudge). Real SMTP/provider
integration is intentionally stubbed — swap `_send_email` for a real provider
(SES, Postmark, SendGrid...) when ready. Every call is logged so it always
shows up in the audit trail regardless of whether delivery is real.
"""

import logging
from dataclasses import dataclass
from datetime import datetime

from app.models.recovery_attempt import RecommendedAction

logger = logging.getLogger("recoverai.action_executor")


@dataclass
class ExecutionResult:
    success: bool
    channel: str | None
    sent_at: datetime | None
    detail: str


def _send_email(to_email: str, subject: str, body: str) -> ExecutionResult:
    # TODO: replace with a real provider integration.
    logger.info("Sending email to=%s subject=%r body=%r", to_email, subject, body)
    return ExecutionResult(success=True, channel="email", sent_at=datetime.utcnow(), detail=f"Email queued to {to_email}")


def execute_action(action: RecommendedAction, customer: dict, payment: dict) -> ExecutionResult:
    if action == RecommendedAction.STOP:
        return ExecutionResult(success=True, channel=None, sent_at=None, detail="No action executed (stop).")

    if action == RecommendedAction.RETRY_PAYMENT:
        link = f"https://pay.example.com/retry/{payment['id']}"
        return _send_email(
            customer["email"],
            subject="Complete your payment",
            body=f"Your payment of {payment['amount']} {payment.get('currency', 'INR')} didn't go through. Retry here: {link}",
        )

    if action == RecommendedAction.SEND_LINK:
        link = f"https://pay.example.com/retry/{payment['id']}"
        return _send_email(
            customer["email"],
            subject="Here's your payment link",
            body=f"Complete your payment of {payment['amount']} {payment.get('currency', 'INR')}: {link}",
        )

    if action == RecommendedAction.SEND_EMAIL:
        return _send_email(
            customer["email"],
            subject="We couldn't process your payment",
            body=f"Payment of {payment['amount']} {payment.get('currency', 'INR')} failed ({payment.get('failure_reason', 'unknown reason')}). Please update your payment method.",
        )

    if action == RecommendedAction.ESCALATE_MANUAL:
        logger.info("Escalating payment %s to manual follow-up queue", payment["id"])
        return ExecutionResult(success=True, channel="manual", sent_at=datetime.utcnow(), detail="Escalated to manual follow-up queue.")

    raise ValueError(f"Unhandled action: {action}")
