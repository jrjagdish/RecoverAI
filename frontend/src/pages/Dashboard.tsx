import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { endpoints } from "../api/client";
import { HorizontalBarList } from "../components/BarChart";
import { PaymentStatusBadge } from "../components/StatusBadge";
import { StatTile } from "../components/StatTile";
import type { AnalyticsResponse, DashboardKpis, Payment } from "../types";
import { formatCurrency, formatDateTime, formatPercent, titleCase } from "../utils/format";

export function Dashboard() {
  const [kpis, setKpis] = useState<DashboardKpis | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [failedPayments, setFailedPayments] = useState<Payment[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([endpoints.kpis(), endpoints.analytics(), endpoints.failedPayments()])
      .then(([k, a, p]) => {
        // A misconfigured API base URL can make requests resolve to the
        // frontend's own index.html (200 OK, wrong content) instead of a
        // real 404 — guard against that shape mismatch rather than crashing
        // on .map() over a non-array.
        if (!Array.isArray(a.by_failure_reason) || !Array.isArray(a.by_action_type) || !Array.isArray(p)) {
          throw new Error("Unexpected response shape from API");
        }
        setKpis(k);
        setAnalytics(a);
        setFailedPayments(p);
      })
      .catch(() =>
        setError("Could not reach the RecoverAI API. Check that VITE_API_URL points at the backend (with /api)."),
      );
  }, []);

  if (error) {
    return (
      <div>
        <h2>Dashboard</h2>
        <div className="card empty-state">{error}</div>
      </div>
    );
  }

  return (
    <div>
      <h2>Dashboard</h2>

      <div className="grid kpi-grid">
        <StatTile label="Total at risk" value={kpis ? formatCurrency(kpis.total_amount_at_risk) : "…"} />
        <StatTile label="Total recovered" value={kpis ? formatCurrency(kpis.total_amount_recovered) : "…"} />
        <StatTile
          label="Recovery rate"
          value={kpis ? formatPercent(kpis.recovery_rate) : "…"}
          sub={kpis ? `${kpis.recovered_payments} of ${kpis.total_payments} payments` : undefined}
        />
        <StatTile label="Active batches" value={kpis ? String(kpis.active_batches) : "…"} />
      </div>

      <div className="grid" style={{ gridTemplateColumns: "1fr 1fr", marginBottom: 24 }}>
        <div className="card">
          <div className="section-title">Recovery rate by failure reason</div>
          {analytics && (
            <HorizontalBarList
              items={analytics.by_failure_reason.map((r) => ({
                label: titleCase(r.failure_reason),
                value: r.recovery_rate,
              }))}
              formatValue={formatPercent}
            />
          )}
        </div>
        <div className="card">
          <div className="section-title">Actions taken</div>
          {analytics && (
            <HorizontalBarList
              items={analytics.by_action_type.map((a) => ({ label: titleCase(a.action), value: a.count }))}
            />
          )}
        </div>
      </div>

      <div className="section">
        <div className="section-title">Failed payments needing attention</div>
        <div className="card table-wrap">
          {failedPayments.length === 0 ? (
            <div className="empty-state">No payments at risk right now.</div>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Payment</th>
                  <th>Amount</th>
                  <th>Failure reason</th>
                  <th>Status</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {failedPayments.map((p) => (
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
                    <td>{formatDateTime(p.created_at)}</td>
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
