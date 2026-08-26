import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { endpoints } from "../api/client";
import { HorizontalBarList, RecoveryProgressBar } from "../components/BarChart";
import { PaymentStatusBadge } from "../components/StatusBadge";
import type { BatchReport, Payment } from "../types";
import { formatCurrency, titleCase } from "../utils/format";

export function BatchDetail() {
  const { batchId } = useParams<{ batchId: string }>();
  const [report, setReport] = useState<BatchReport | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!batchId) return;
    Promise.all([endpoints.getBatchReport(batchId), endpoints.listPayments({ batch_id: batchId })])
      .then(([r, p]) => {
        setReport(r);
        setPayments(p);
      })
      .catch(() => setError("Could not load this batch."));
  }, [batchId]);

  if (error) return <div className="card empty-state">{error}</div>;
  if (!report) return <div className="muted">Loading…</div>;

  return (
    <div>
      <h2>{report.name}</h2>

      <div className="card section" style={{ marginBottom: 24 }}>
        <div className="section-title">Recovery progress</div>
        <RecoveryProgressBar recovered={report.total_amount_recovered} atRisk={report.total_amount_at_risk} />
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", marginBottom: 24 }}>
        <div className="card">
          <div className="section-title">Stopping-rule breakdown</div>
          <HorizontalBarList
            items={Object.entries(report.stopping_breakdown).map(([label, value]) => ({
              label: titleCase(label),
              value,
            }))}
          />
        </div>
        <div className="card">
          <div className="section-title">Actions executed</div>
          <HorizontalBarList
            items={Object.entries(report.action_breakdown).map(([label, value]) => ({
              label: titleCase(label),
              value,
            }))}
          />
        </div>
      </div>

      <div className="section">
        <div className="section-title">Payments in this batch</div>
        <div className="card table-wrap">
          {payments.length === 0 ? (
            <div className="empty-state">No payments in this batch.</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Payment</th>
                  <th>Amount</th>
                  <th>Failure reason</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {payments.map((p) => (
                  <tr key={p.id}>
                    <td>
                      <Link className="link-plain" to={`/payments/${p.id}`}>
                        {p.id.slice(0, 8)}
                      </Link>
                    </td>
                    <td>{formatCurrency(p.amount, p.currency)}</td>
                    <td>{p.failure_reason ? titleCase(p.failure_reason) : "—"}</td>
                    <td>
                      <PaymentStatusBadge status={p.status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
