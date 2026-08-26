import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { endpoints } from "../api/client";
import { PaymentStatusBadge } from "../components/StatusBadge";
import type { Payment, PaymentStatus } from "../types";
import { formatCurrency, formatDateTime, titleCase } from "../utils/format";

const STATUS_OPTIONS: PaymentStatus[] = ["failed", "retrying", "recovered", "stopped", "disputed"];

export function Payments() {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [status, setStatus] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    endpoints
      .listPayments(status ? { status } : undefined)
      .then(setPayments)
      .catch(() => setError("Could not load payments."));
  }, [status]);

  return (
    <div>
      <h2>Payments</h2>

      <div className="form-row">
        <select
          value={status}
          onChange={(e) => setStatus(e.target.value)}
          style={{
            padding: "8px 10px",
            borderRadius: 7,
            border: "1px solid var(--border)",
            background: "var(--surface-1)",
            color: "var(--text-primary)",
            fontSize: 13,
          }}
        >
          <option value="">All statuses</option>
          {STATUS_OPTIONS.map((s) => (
            <option key={s} value={s}>
              {titleCase(s)}
            </option>
          ))}
        </select>
      </div>

      {error && <div className="card empty-state">{error}</div>}

      <div className="card table-wrap">
        {payments.length === 0 ? (
          <div className="empty-state">No payments found.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Payment</th>
                <th>Amount</th>
                <th>Failure reason</th>
                <th>Status</th>
                <th>Batch</th>
                <th>Created</th>
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
                  <td>
                    {p.batch_id ? (
                      <Link className="link-plain" to={`/batches/${p.batch_id}`}>
                        {p.batch_id.slice(0, 8)}
                      </Link>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>{formatDateTime(p.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
