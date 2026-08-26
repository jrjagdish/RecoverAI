import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

DEFAULT_CONSENT = {"email": True, "sms": False, "call": False}
DEFAULT_QUIET_HOURS = {"start": "21:00", "end": "09:00", "timezone": "Asia/Kolkata"}


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Compliance: which channels the customer has consented to be contacted on.
    contact_consent: Mapped[dict] = mapped_column(JSON, default=lambda: dict(DEFAULT_CONSENT))
    # Compliance: window during which the customer may legally be contacted.
    contact_quiet_hours: Mapped[dict] = mapped_column(JSON, default=lambda: dict(DEFAULT_QUIET_HOURS))
    opted_out: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    payments = relationship("Payment", back_populates="customer")
