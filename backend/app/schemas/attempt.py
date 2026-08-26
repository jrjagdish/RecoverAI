from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.recovery_attempt import AttemptOutcome, PolicyDecision, RecommendedAction


class RecoveryAttemptRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    payment_id: str
    batch_id: str | None
    attempt_number: int
    ai_recommended_action: RecommendedAction
    ai_confidence: float | None
    ai_reason: dict
    policy_decision: PolicyDecision
    policy_reason: str
    executed_action: RecommendedAction | None
    channel: str | None
    sent_at: datetime | None
    outcome: AttemptOutcome
    outcome_at: datetime | None
    created_at: datetime


class EvaluateRequest(BaseModel):
    force: bool = False


class ExecuteRequest(BaseModel):
    channel: str | None = None
