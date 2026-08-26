from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_or_404
from app.config import get_settings
from app.models.recovery_attempt import RecoveryAttempt

router = APIRouter(prefix="/policy", tags=["policy"])
settings = get_settings()


@router.get("/rules")
def get_active_rules():
    return {
        "max_recovery_attempts": settings.max_recovery_attempts,
        "cost_to_recover_threshold": settings.cost_to_recover_threshold,
        "quiet_hours": {"start": settings.quiet_hours_start, "end": settings.quiet_hours_end},
        "contact_actions_require_consent": ["email"],
        "stopping_reasons": [
            "max_attempts",
            "dispute",
            "opt_out",
            "refunded",
            "uneconomical",
            "already_paid",
        ],
    }


@router.get("/decisions/{attempt_id}")
def get_policy_decision(attempt_id: str, db: Session = Depends(get_db)):
    attempt = get_or_404(db, RecoveryAttempt, attempt_id, "recovery attempt")
    return {
        "attempt_id": attempt.id,
        "ai_recommended_action": attempt.ai_recommended_action,
        "policy_decision": attempt.policy_decision,
        "final_action": attempt.final_action,
        "policy_reason": attempt.policy_reason,
    }
