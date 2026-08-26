import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class StoppingReason(str, enum.Enum):
    MAX_ATTEMPTS = "max_attempts"
    DISPUTE = "dispute"
    OPT_OUT = "opt_out"
    REFUNDED = "refunded"
    UNECONOMICAL = "uneconomical"
    ALREADY_PAID = "already_paid"


class StoppingEvent(Base):
    __tablename__ = "stopping_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"), index=True)
    reason: Mapped[StoppingReason] = mapped_column(Enum(StoppingReason))
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
