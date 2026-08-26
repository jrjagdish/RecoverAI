from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.recovery_batch import BatchStatus


class BatchCreate(BaseModel):
    name: str
    payment_ids: list[str] | None = None  # if omitted, includes all currently-failed payments


class BatchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    status: BatchStatus
    total_amount_at_risk: float
    total_amount_recovered: float
    total_payments_count: int
    recovered_count: int
    started_at: datetime
    completed_at: datetime | None


class BatchReport(BatchRead):
    recovery_rate: float
    stopping_breakdown: dict[str, int]
    action_breakdown: dict[str, int]
