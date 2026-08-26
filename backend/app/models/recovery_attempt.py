import enum
import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class RecommendedAction(str, enum.Enum):
    RETRY_PAYMENT = "retry_payment"
    SEND_EMAIL = "send_email"
    SEND_LINK = "send_link"
    ESCALATE_MANUAL = "escalate_manual"
    STOP = "stop"


class PolicyDecision(str, enum.Enum):
    ALLOWED = "allowed"
    BLOCKED = "blocked"


class AttemptOutcome(str, enum.Enum):
    PENDING = "pending"
    RECOVERED = "recovered"
    FAILED = "failed"
    NO_RESPONSE = "no_response"
    OPTED_OUT = "opted_out"


class RecoveryAttempt(Base):
    __tablename__ = "recovery_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), index=True)
    batch_id: Mapped[str | None] = mapped_column(ForeignKey("recovery_batches.id"), nullable=True, index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)

    # What the AI recommended (structured, enum-constrained).
    ai_recommended_action: Mapped[RecommendedAction] = mapped_column(Enum(RecommendedAction))
    ai_confidence: Mapped[float | None] = mapped_column(nullable=True)
    ai_reason: Mapped[dict] = mapped_column(JSON, default=dict)

    # What the policy engine decided, and why.
    policy_decision: Mapped[PolicyDecision] = mapped_column(Enum(PolicyDecision))
    policy_reason: Mapped[str] = mapped_column(String(500))
    # The action the policy engine actually cleared for execution — may differ
    # from ai_recommended_action (e.g. forced to STOP).
    final_action: Mapped[RecommendedAction] = mapped_column(Enum(RecommendedAction))

    # What actually happened.
    executed_action: Mapped[RecommendedAction | None] = mapped_column(Enum(RecommendedAction), nullable=True)
    channel: Mapped[str | None] = mapped_column(String(32), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    outcome: Mapped[AttemptOutcome] = mapped_column(Enum(AttemptOutcome), default=AttemptOutcome.PENDING)
    outcome_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    payment = relationship("Payment", back_populates="attempts")
    batch = relationship("RecoveryBatch", back_populates="attempts")
