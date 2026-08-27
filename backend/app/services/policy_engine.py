"""Policy Engine: a pure, deterministic function with veto power over the AI.

Given (recommended_action, customer, payment, attempt_history) it returns
(allowed, final_action, reason). It never calls the LLM and has no side effects,
which is what makes it unit-testable and auditable — the same inputs always
produce the same decision.
"""

from dataclasses import dataclass
from datetime import datetime, time,UTC

from app.config import get_settings
from app.models.recovery_attempt import RecommendedAction
from app.models.stopping_event import StoppingReason

settings = get_settings()

CONTACT_ACTIONS = {
    RecommendedAction.SEND_EMAIL,
    RecommendedAction.SEND_LINK,
    RecommendedAction.ESCALATE_MANUAL,
}

CHANNEL_FOR_ACTION = {
    RecommendedAction.SEND_EMAIL: "email",
    RecommendedAction.SEND_LINK: "email",  # V1: retry link delivered via email
    RecommendedAction.RETRY_PAYMENT: "payment_link",
    RecommendedAction.ESCALATE_MANUAL: "manual",
}


@dataclass
class PolicyResult:
    allowed: bool
    final_action: RecommendedAction
    reason: str
    stopping_reason: StoppingReason | None = None


def _in_quiet_hours(quiet_hours: dict, now: datetime) -> bool:
    try:
        start = time.fromisoformat(quiet_hours["start"])
        end = time.fromisoformat(quiet_hours["end"])
    except (KeyError, ValueError):
        return False

    current = now.time()
    if start <= end:
        return start <= current < end
    # Window wraps past midnight, e.g. 21:00 -> 09:00
    return current >= start or current < end


def evaluate_policy(
    recommended_action: RecommendedAction,
    customer: dict,
    payment: dict,
    attempt_history: dict,
    now: datetime | None = None,
) -> PolicyResult:
    now = now or datetime.now(UTC)()

    # 1. Already resolved via another channel (reconciliation).
    if payment.get("status") == "recovered":
        return PolicyResult(
            allowed=False,
            final_action=RecommendedAction.STOP,
            reason="Payment already recovered via another channel.",
            stopping_reason=StoppingReason.ALREADY_PAID,
        )

    # 2. Dispute / chargeback filed — never contact, hand to human process.
    if payment.get("status") == "disputed":
        return PolicyResult(
            allowed=False,
            final_action=RecommendedAction.STOP,
            reason="Payment is under dispute/chargeback — recovery contact halted.",
            stopping_reason=StoppingReason.DISPUTE,
        )

    # 3. Customer opted out / revoked consent entirely.
    if customer.get("opted_out"):
        return PolicyResult(
            allowed=False,
            final_action=RecommendedAction.STOP,
            reason="Customer has opted out of contact.",
            stopping_reason=StoppingReason.OPT_OUT,
        )

    # 4. Max attempts reached.
    attempt_count = attempt_history.get("attempt_count", 0)
    if attempt_count >= settings.max_recovery_attempts:
        return PolicyResult(
            allowed=False,
            final_action=RecommendedAction.STOP,
            reason=f"Max recovery attempts ({settings.max_recovery_attempts}) reached.",
            stopping_reason=StoppingReason.MAX_ATTEMPTS,
        )

    # 5. Amount below cost-to-recover threshold.
    if payment.get("amount", 0) < settings.cost_to_recover_threshold:
        return PolicyResult(
            allowed=False,
            final_action=RecommendedAction.STOP,
            reason=(
                f"Amount ({payment.get('amount')}) is below the cost-to-recover "
                f"threshold ({settings.cost_to_recover_threshold})."
            ),
            stopping_reason=StoppingReason.UNECONOMICAL,
        )

    # From here, the AI's recommendation may proceed — but only if it clears
    # channel-level consent and quiet-hours checks.
    if recommended_action == RecommendedAction.STOP:
        return PolicyResult(
            allowed=True,
            final_action=RecommendedAction.STOP,
            reason="AI recommended stopping and no policy override applies.",
        )

    channel = CHANNEL_FOR_ACTION.get(recommended_action)

    if recommended_action in CONTACT_ACTIONS:
        consent = customer.get("contact_consent", {})
        if not consent.get("email", False):
            return PolicyResult(
                allowed=False,
                final_action=RecommendedAction.STOP,
                reason="Customer has not consented to email contact.",
                stopping_reason=StoppingReason.OPT_OUT,
            )

        quiet_hours = customer.get("contact_quiet_hours", {})
        if _in_quiet_hours(quiet_hours, now):
            return PolicyResult(
                allowed=False,
                final_action=recommended_action,
                reason=(
                    f"Blocked: current time falls within the customer's quiet "
                    f"hours ({quiet_hours.get('start')}-{quiet_hours.get('end')})."
                ),
            )

    return PolicyResult(
        allowed=True,
        final_action=recommended_action,
        reason="AI recommendation cleared all policy checks.",
    )
