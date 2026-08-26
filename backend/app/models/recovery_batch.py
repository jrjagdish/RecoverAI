import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BatchStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"


class RecoveryBatch(Base):
    __tablename__ = "recovery_batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[BatchStatus] = mapped_column(Enum(BatchStatus), default=BatchStatus.PENDING)

    total_amount_at_risk: Mapped[float] = mapped_column(Float, default=0)
    total_amount_recovered: Mapped[float] = mapped_column(Float, default=0)
    total_payments_count: Mapped[int] = mapped_column(Integer, default=0)
    recovered_count: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    payments = relationship("Payment", back_populates="batch")
    attempts = relationship("RecoveryAttempt", back_populates="batch")
