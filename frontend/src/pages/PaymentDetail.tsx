import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { endpoints } from "../api/client";
import { OutcomeBadge, PaymentStatusBadge, PolicyBadge } from "../components/StatusBadge";
import type { AuditLogEntry, Payment, RecoveryAttempt } from "../types";
import { formatCurrency, formatDateTime, titleCase } from "../utils/format";

export function PaymentDetail() {
  const { paymentId } = useParams<{ paymentId: string }>();
  const [payment, setPayment] = useState<Payment | null>(null);
  const [attempts, setAttempts] = useState<RecoveryAttempt[]>([]);
  const [audit, setAudit] = useState<AuditLogEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    if (!paymentId) return;
    const [p, a, log] = await Promise.all([
      endpoints.getPayment(paymentId),
      endpoints.getPaymentAttempts(paymentId),
      endpoints.paymentAudit(paymentId),
    ]);
    setPayment(p);
    setAttempts(a);
    setAudit(log);
  };

  useEffect(() => {
    load().catch(() => setError("Could not load this payment."));
  }, [paymentId]);

  const handleEvaluate = async () => {
    if (!paymentId) return;
    setBusy(true);
    setError(null);
    try {
      await endpoints.evaluatePayment(paymentId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Evaluation failed.");
    } finally {
      setBusy(false);
    }
  };

  const handleExecute = async (attemptId: string) => {
    setBusy(true);
    setError(null);
    try {
      await endpoints.executeAttempt(attemptId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Execution failed.");
    } finally {
      setBusy(false);
    }
  };

  if (error && !payment) return <div className="card empty-state">{error}</div>;
  if (!payment) return <div className="muted">Loading…</div>;

  return (
    <div>
      <h2>Payment {payment.id.slice(0, 8)}</h2>

      <div className="card section" style={{ marginBottom: 24, display: "flex", gap: 32, flexWrap: "wrap" }}>
        <div>
          <div className="label" style={{ fontSize: 12, color: "var(--text-secondary)" }}>
            Amount
          </div>
          <div style={{ fontSize: 20, fontWeight: 600 }}>{formatCurrency(payment.amount, payment.currency)}</div>
        </div>
        <div>
          <div className="label" style={{ fontSize: 12, color: "var(--text-secondary)" }}>
            Status
          </div>
          <div style={{ marginTop: 4 }}>
            <PaymentStatusBadge status={payment.status} />
          </div>
        </div>
        <div>
          <div className="label" style={{ fontSize: 12, color: "var(--text-secondary)" }}>
            Failure reason
          </div>
          <div>{payment.failure_reason ? titleCase(payment.failure_reason) : "—"}</div>
        </div>
        <div>
          <div className="label" style={{ fontSize: 12, color: "var(--text-secondary)" }}>
            Created
          </div>
          <div>{formatDateTime(payment.created_at)}</div>
        </div>
        <div style={{ marginLeft: "auto", alignSelf: "center" }}>
          <button className="button" onClick={handleEvaluate} disabled={busy}>
            {busy ? "Working…" : "Run recovery evaluation"}
          </button>
        </div>
      </div>

      {error && <p style={{ color: "var(--status-critical)", fontSize: 13 }}>{error}</p>}

      <div className="section">
        <div className="section-title">Recovery attempts</div>
        <div className="card table-wrap">
          {attempts.length === 0 ? (
            <div className="empty-state">No recovery attempts yet — run an evaluation above.</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>#</th>
                  <th>AI recommended</th>
                  <th>Policy</th>
                  <th>Reason</th>
                  <th>Executed action</th>
                  <th>Outcome</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {attempts.map((a) => (
                  <tr key={a.id}>
                    <td>{a.attempt_number}</td>
                    <td>{titleCase(a.ai_recommended_action)}</td>
                    <td>
                      <PolicyBadge decision={a.policy_decision} />
                    </td>
                    <td style={{ maxWidth: 260 }}>{a.policy_reason}</td>
                    <td>{a.executed_action ? titleCase(a.executed_action) : "—"}</td>
                    <td>
                      <OutcomeBadge outcome={a.outcome} />
                    </td>
                    <td>
                      {a.policy_decision === "allowed" && !a.executed_action && (
                        <button className="button button-secondary" onClick={() => handleExecute(a.id)} disabled={busy}>
                          Execute
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      <div className="section">
        <div className="section-title">Audit timeline</div>
        <div className="card">
          {audit.length === 0 ? (
            <div className="empty-state">No audit events yet.</div>
          ) : (
            <div className="timeline">
              {audit.map((e) => (
                <div key={e.id} className="timeline-item">
                  <div className="timeline-dot" />
                  <div className="timeline-body" style={{ flex: 1 }}>
                    <div className="event">{titleCase(e.event_type)}</div>
                    <div className="meta">
                      {formatDateTime(e.created_at)} · actor: {e.actor}
                    </div>
                    <pre>{JSON.stringify(e.payload_json, null, 2)}</pre>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
