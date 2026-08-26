import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { endpoints } from "../api/client";
import type { RecoveryBatch } from "../types";
import { formatCurrency, formatDateTime, formatPercent } from "../utils/format";

export function Batches() {
  const [batches, setBatches] = useState<RecoveryBatch[]>([]);
  const [name, setName] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = () => endpoints.listBatches().then(setBatches).catch(() => setError("Could not load batches."));

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async () => {
    if (!name.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await endpoints.createBatch(name.trim());
      setName("");
      await load();
    } catch {
      setError("Could not create batch — are there any failed payments not already in a batch?");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <h2>Recovery batches</h2>

      <div className="form-row">
        <input
          type="text"
          placeholder="Batch name (e.g. Aug week 4 failed payments)"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <button className="button" onClick={handleCreate} disabled={creating || !name.trim()}>
          {creating ? "Creating…" : "Start new batch"}
        </button>
      </div>
      {error && <p style={{ color: "var(--status-critical)", fontSize: 13 }}>{error}</p>}

      <div className="card table-wrap">
        {batches.length === 0 ? (
          <div className="empty-state">No batches yet — start one above, or run backend/seed.py for demo data.</div>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Status</th>
                <th>At risk</th>
                <th>Recovered</th>
                <th>Recovery rate</th>
                <th>Payments</th>
                <th>Started</th>
              </tr>
            </thead>
            <tbody>
              {batches.map((b) => (
                <tr key={b.id}>
                  <td>
                    <Link className="link-plain" to={`/batches/${b.id}`}>
                      {b.name}
                    </Link>
                  </td>
                  <td>{b.status}</td>
                  <td>{formatCurrency(b.total_amount_at_risk)}</td>
                  <td>{formatCurrency(b.total_amount_recovered)}</td>
                  <td>
                    {formatPercent(b.total_amount_at_risk ? b.total_amount_recovered / b.total_amount_at_risk : 0)}
                  </td>
                  <td>
                    {b.recovered_count}/{b.total_payments_count}
                  </td>
                  <td>{formatDateTime(b.started_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
