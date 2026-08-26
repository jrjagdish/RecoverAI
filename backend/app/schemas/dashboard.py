from pydantic import BaseModel


class DashboardKpis(BaseModel):
    total_amount_at_risk: float
    total_amount_recovered: float
    recovery_rate: float
    active_batches: int
    total_payments: int
    recovered_payments: int


class FailureReasonBreakdown(BaseModel):
    failure_reason: str
    at_risk: float
    recovered: float
    recovery_rate: float


class ActionBreakdown(BaseModel):
    action: str
    count: int


class AnalyticsResponse(BaseModel):
    by_failure_reason: list[FailureReasonBreakdown]
    by_action_type: list[ActionBreakdown]
    stopping_breakdown: dict[str, int]
