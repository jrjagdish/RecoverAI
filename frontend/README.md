# RecoverAI frontend (React + Vite + TypeScript)

## Setup

```bash
cd frontend
npm install
copy .env.example .env
```

## Run

```bash
npm run dev
```

Opens at http://localhost:5173. Expects the backend running at
http://localhost:8000 (set `VITE_API_URL` in `.env` to override).

## Structure

```
src/
  api/client.ts       axios instance + typed endpoint calls
  types/index.ts       types mirroring the backend Pydantic schemas
  components/          Layout, StatTile, StatusBadge, BarChart (hand-rolled, no chart lib)
  pages/
    Dashboard.tsx       KPIs, recovery rate by failure reason, actions taken, at-risk payments
    Batches.tsx         list + start a new recovery batch
    BatchDetail.tsx     batch report: recovered vs at-risk, stopping/action breakdowns
    Payments.tsx        filterable payments table
    PaymentDetail.tsx   attempts (AI recommendation, policy decision + reason, execute action),
                        full audit timeline
```

Run `npm run build` to typecheck + produce a production build.
