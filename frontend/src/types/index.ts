export type PaymentStatus = "failed" | "retrying" | "recovered" | "stopped" | "disputed";

export type RecommendedAction = "retry_payment" | "send_email" | "send_link" | "escalate_manual" | "stop";

export type PolicyDecisionValue = "allowed" | "blocked";

export type AttemptOutcome = "pending" | "recovered" | "failed" | "no_response" | "opted_out";

export type BatchStatus = "pending" | "running" | "completed";

export interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string | null;
  contact_consent: { email: boolean; sms: boolean; call: boolean };
  contact_quiet_hours: { start: string; end: string; timezone: string };
  opted_out: boolean;
  created_at: string;
}

export interface Payment {
  id: string;
  customer_id: string;
  batch_id: string | null;
  amount: number;
  currency: string;
  status: PaymentStatus;
  razorpay_payment_id: string | null;
  razorpay_order_id: string | null;
  failure_reason: string | null;
  created_at: string;
  recovered_at: string | null;
}

export interface RecoveryAttempt {
  id: string;
  payment_id: string;
  batch_id: string | null;
  attempt_number: number;
  ai_recommended_action: RecommendedAction;
  ai_confidence: number | null;
  ai_reason: { reason?: string; risk_flags?: string[] };
  policy_decision: PolicyDecisionValue;
  policy_reason: string;
  final_action?: RecommendedAction;
  executed_action: RecommendedAction | null;
  channel: string | null;
  sent_at: string | null;
  outcome: AttemptOutcome;
  outcome_at: string | null;
  created_at: string;
}

export interface RecoveryBatch {
  id: string;
  name: string;
  status: BatchStatus;
  total_amount_at_risk: number;
  total_amount_recovered: number;
  total_payments_count: number;
  recovered_count: number;
  started_at: string;
  completed_at: string | null;
}

export interface BatchReport extends RecoveryBatch {
  recovery_rate: number;
  stopping_breakdown: Record<string, number>;
  action_breakdown: Record<string, number>;
}

export interface AuditLogEntry {
  id: string;
  entity_type: string;
  entity_id: string;
  event_type: string;
  actor: string;
  payload_json: Record<string, unknown>;
  created_at: string;
}

export interface DashboardKpis {
  total_amount_at_risk: number;
  total_amount_recovered: number;
  recovery_rate: number;
  active_batches: number;
  total_payments: number;
  recovered_payments: number;
}

export interface FailureReasonBreakdown {
  failure_reason: string;
  at_risk: number;
  recovered: number;
  recovery_rate: number;
}

export interface ActionBreakdown {
  action: string;
  count: number;
}

export interface AnalyticsResponse {
  by_failure_reason: FailureReasonBreakdown[];
  by_action_type: ActionBreakdown[];
  stopping_breakdown: Record<string, number>;
}
