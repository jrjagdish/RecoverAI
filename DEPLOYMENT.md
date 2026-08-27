# Deploying RecoverAI

Vercel doesn't run arbitrary Docker containers — it builds static/frontend
frameworks (Vite, Next.js, ...) and runs short-lived serverless functions. It
also can't host a persistent process, a SQLite file, or a Celery worker. So
this is a **split deploy**: frontend on Vercel, backend on a host that runs
Docker images.

## Frontend -> Vercel

No Docker involved — Vercel builds `frontend/` directly.

1. Import the repo in the Vercel dashboard.
2. Set the project's **Root Directory** to `frontend`.
3. Framework preset: Vite (auto-detected). Build command `npm run build`,
   output directory `dist` (also auto-detected).
4. Set the environment variable `VITE_API_URL` to your deployed backend's
   URL + `/api` (e.g. `https://recoverai-backend.up.railway.app/api`).
5. Deploy. `frontend/vercel.json` handles the SPA rewrite so client-side
   routes (`/batches/:id`, `/payments/:id`) don't 404 on refresh.

`frontend/Dockerfile` is unused by Vercel — it's there only if you want to
self-host the frontend as a static container somewhere else instead.

## Backend -> any Docker-friendly host

`backend/Dockerfile` is built and tested (see below) — deploy it to
Railway, Render, Fly.io, or Cloud Run. All four detect a Dockerfile
automatically and need no other config to get running. Pick one:

- **Railway**: New Project -> Deploy from repo -> set root directory to
  `backend` -> it builds the Dockerfile automatically. Add a Redis plugin if
  you want Celery background jobs.
- **Render**: New -> Web Service -> point at the repo, root directory
  `backend`, runtime "Docker". Add a Render Redis instance for Celery.
- **Fly.io**: `fly launch` from inside `backend/` (it finds the Dockerfile),
  then `fly deploy`.
- **Google Cloud Run**: `gcloud run deploy --source backend`.

### Required environment variables on the backend host

Same as `backend/.env.example`. At minimum for a working demo:

```
DATABASE_URL=<see note below>
RAZORPAY_KEY_ID=...
RAZORPAY_KEY_SECRET=...
RAZORPAY_WEBHOOK_SECRET=...
GROQ_API_KEY=...
FRONTEND_ORIGIN=https://<your-vercel-app>.vercel.app
```

### Database: switch off SQLite for real deployments

SQLite works for local dev and the seed script, but most of these hosts run
an ephemeral or read-only filesystem and won't reliably persist a `.db` file
across deploys or multiple instances. Use a managed Postgres instead (Railway
Postgres, Render Postgres, Neon, Supabase — any of them) and point
`DATABASE_URL` at it, e.g.:

```
DATABASE_URL=postgresql://user:password@host:5432/recoverai
```

Add `psycopg[binary]` to `backend/requirements.txt` when you do — the code
itself needs no changes, SQLAlchemy picks the right dialect from the URL.

### Webhook URL

Once deployed, point your Razorpay webhook (Dashboard -> Settings ->
Webhooks) at `https://<your-backend-host>/api/webhooks/razorpay` instead of
the ngrok tunnel used for local testing, and copy the webhook secret it
issues into `RAZORPAY_WEBHOOK_SECRET`.

## Local Docker (dev/staging parity)

```bash
docker compose up --build
```

Runs the backend + a Redis instance + a Celery worker, backed by a named
volume for the SQLite file (`docker-compose.yml` at the repo root). The
frontend isn't in `docker-compose.yml` — run it with `npm run dev` in
`frontend/` against the composed backend at `http://localhost:8000/api`, or
build `frontend/Dockerfile` separately if you want it containerized too.

Both `backend/Dockerfile` and `frontend/Dockerfile` have been built and
smoke-tested (`docker build` + a running container hit against `/health`,
`/api/dashboard/kpis`, and the frontend's SPA fallback routing).
