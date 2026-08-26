const SERIES_COLORS = [
  "var(--series-1)",
  "var(--series-2)",
  "var(--series-3)",
  "var(--series-4)",
  "var(--series-5)",
];

interface BarItem {
  label: string;
  value: number;
}

interface Props {
  items: BarItem[];
  formatValue?: (v: number) => string;
}

/** A single-axis horizontal bar list — magnitude by category, thin rounded marks. */
export function HorizontalBarList({ items, formatValue }: Props) {
  if (items.length === 0) {
    return <div className="empty-state">No data yet.</div>;
  }
  const max = Math.max(...items.map((i) => i.value), 1);
  const fmt = formatValue ?? ((v: number) => String(v));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {items.map((item, i) => (
        <div key={item.label}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              fontSize: 12,
              marginBottom: 4,
              color: "var(--text-secondary)",
            }}
          >
            <span>{item.label}</span>
            <span style={{ fontVariantNumeric: "tabular-nums", color: "var(--text-primary)", fontWeight: 600 }}>
              {fmt(item.value)}
            </span>
          </div>
          <div
            style={{
              height: 8,
              background: "var(--gridline)",
              borderRadius: 4,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${(item.value / max) * 100}%`,
                background: SERIES_COLORS[i % SERIES_COLORS.length],
                borderRadius: 4,
                minWidth: item.value > 0 ? 4 : 0,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

interface ProgressProps {
  recovered: number;
  atRisk: number;
  currency?: string;
}

/** Recovered-vs-at-risk as one bar: recovered fill + remaining track, with a legend. */
export function RecoveryProgressBar({ recovered, atRisk, currency = "INR" }: ProgressProps) {
  const pct = atRisk > 0 ? Math.min((recovered / atRisk) * 100, 100) : 0;
  const fmt = (v: number) =>
    new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(v);

  return (
    <div>
      <div
        style={{
          height: 14,
          background: "var(--gridline)",
          borderRadius: 7,
          overflow: "hidden",
          border: "2px solid var(--surface-1)",
          outline: "1px solid var(--border)",
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${pct}%`,
            background: "var(--status-good)",
            borderRadius: 7,
            transition: "width 0.3s ease",
          }}
        />
      </div>
      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 10, fontSize: 13 }}>
        <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "var(--status-good)",
              display: "inline-block",
            }}
          />
          Recovered <strong>{fmt(recovered)}</strong>
        </span>
        <span style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--text-secondary)" }}>
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: "50%",
              background: "var(--gridline)",
              display: "inline-block",
            }}
          />
          At risk <strong>{fmt(atRisk)}</strong>
        </span>
        <span className="muted">{pct.toFixed(1)}% recovered</span>
      </div>
    </div>
  );
}
