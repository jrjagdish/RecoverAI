from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.payment import PaymentStatus


class PaymentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    customer_id: str
    batch_id: str | None
    amount: float
    currency: str
    status: PaymentStatus
    razorpay_payment_id: str | None
    razorpay_order_id: str | None
    failure_reason: str | None
    created_at: datetime
    recovered_at: datetime | None
