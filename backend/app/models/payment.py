import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PaymentStatus(str, enum.Enum):
    FAILED = "failed"
    RETRYING = "retrying"
    RECOVERED = "recovered"
    STOPPED = "stopped"
    DISPUTED = "disputed"


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id: Mapped[str] = mapped_column(ForeignKey("customers.id"), index=True)
    batch_id: Mapped[str | None] = mapped_column(ForeignKey("recovery_batches.id"), nullable=True, index=True)

    amount: Mapped[float] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus), default=PaymentStatus.FAILED, index=True)

    razorpay_payment_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    recovered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    customer = relationship("Customer", back_populates="payments")
    batch = relationship("RecoveryBatch", back_populates="payments")
    attempts = relationship("RecoveryAttempt", back_populates="payment")
