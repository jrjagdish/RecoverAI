import type { AttemptOutcome, PaymentStatus, PolicyDecisionValue } from "../types";

const PAYMENT_STATUS_CLASS: Record<PaymentStatus, string> = {
  recovered: "badge-good",
  disputed: "badge-critical",
  failed: "badge-serious",
  stopped: "badge-warning",
  retrying: "badge-neutral",
};

const OUTCOME_CLASS: Record<AttemptOutcome, string> = {
  recovered: "badge-good",
  failed: "badge-critical",
  opted_out: "badge-warning",
  no_response: "badge-neutral",
  pending: "badge-neutral",
};

export function PaymentStatusBadge({ status }: { status: PaymentStatus }) {
  return <span className={`badge ${PAYMENT_STATUS_CLASS[status]}`}>{status.replace("_", " ")}</span>;
}

export function OutcomeBadge({ outcome }: { outcome: AttemptOutcome }) {
  return <span className={`badge ${OUTCOME_CLASS[outcome]}`}>{outcome.replace("_", " ")}</span>;
}

export function PolicyBadge({ decision }: { decision: PolicyDecisionValue }) {
  return (
    <span className={`badge ${decision === "allowed" ? "badge-good" : "badge-critical"}`}>
      {decision === "allowed" ? "✓ allowed" : "✕ blocked"}
    </span>
  );
}
