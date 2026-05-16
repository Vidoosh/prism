# Production deployment

Prism is **three deployable surfaces**, each with its own hosting story. **You cannot deploy the entire stack as a single Vercel project** because the backend is Python/FastAPI with Playwright, disk-backed pipeline storage, and long-running background jobs—none of which fit Vercel’s serverless model.

| Surface | Recommended host | Notes |
|--------|------------------|--------|
| **Next.js frontend** | [Vercel](https://vercel.com) | Next.js 15; root directory `prism/frontend` |
| **FastAPI backend** | Railway, Render, Fly.io, Cloud Run, etc. | Deploy via [`backend/Dockerfile`](backend/Dockerfile); attach persistent disk/volume for `storage/` and `failed_writes/` |
| **Sanity Studio** | Sanity-hosted (`sanity deploy`) | CMS UI + schemas in [`sanity/`](sanity/) |

---

## 1. Frontend (Vercel)

1. Create a Vercel project and set **Root Directory** to **`prism/frontend`** (or connect the repo and adjust in Project Settings → General).
2. Framework preset should detect **Next.js**. Builds automatically omit `output: "standalone"` when `VERCEL` is set ([`frontend/next.config.ts`](frontend/next.config.ts)).
3. Add **Environment Variables** (Production / Preview as needed):

   | Variable | Value |
   |----------|--------|
   | `NEXT_PUBLIC_API_URL` | Public HTTPS URL of your deployed API (no trailing slash), e.g. `https://your-api.example.com` |
   | `INTERNAL_API_URL` | Same as `NEXT_PUBLIC_API_URL` unless you split internal traffic (split setups are uncommon on Vercel) |
   | `NEXT_PUBLIC_SANITY_PROJECT_ID` | Same as `SANITY_PROJECT_ID` / Sanity dashboard |
   | `NEXT_PUBLIC_SANITY_DATASET` | Usually `production` |
   | `SANITY_API_READ_TOKEN` | Optional; GROQ read token with read scope |
   | `LANDING_PAGE_SECRET` | Optional; server-only HMAC secret for `/lp/*` |

4. Deploy. After the backend URL exists, update **`FRONTEND_URL`** on the backend (see below) and redeploy or restart the API so CORS allows your Vercel domain.

---

## 2. Backend (container platform)

Use any host that runs **Docker** with enough RAM for Chromium when Playwright runs.

### Image

- Context: [`backend/`](backend/)
- Dockerfile: [`backend/Dockerfile`](backend/Dockerfile)
- Command: `uvicorn main:app --host 0.0.0.0 --port 8000` (already in Dockerfile)

### Persistent disk (required for correctness)

The API persists pipeline runs under **`storage/`** (see [`backend/pipeline/storage.py`](backend/pipeline/storage.py)) and dead-letter payloads under **`failed_writes/`**. On ephemeral filesystems (default containers), data is lost when the instance restarts.

- Mount a volume/disk so **`STORAGE_DIR`** and **`FAILED_WRITES_DIR`** resolve to persistent paths (defaults: `storage` and `failed_writes` relative to the app working directory, typically `/app`).
- Example (conceptually): mount volume → `/app/storage` and `/app/failed_writes`, **or** mount one volume at `/app/data` and set `STORAGE_DIR=/app/data/storage` and `FAILED_WRITES_DIR=/app/data/failed_writes`.

Long term, migrating JSON-on-disk to a database is recommended for multi-instance setups.

### Environment variables

Copy from [`.env.example`](.env.example). Critical production mappings:

| Variable | Purpose |
|----------|---------|
| `FRONTEND_URL` | Your Vercel site origin, e.g. `https://your-app.vercel.app` — used for **CORS** ([`backend/main.py`](backend/main.py)) |
| `GEMINI_API_KEY` | Gemini calls |
| `SANITY_*` / `HUBSPOT_*` | Integrations per `.env.example` |
| `BACKEND_URL` | Public URL of this API (used where documented in integrations) |

Ensure outbound HTTPS works from the container (Gemini, Sanity, HubSpot, optional Apify).

---

## 3. Sanity Studio (`sanity deploy`)

From [`sanity/`](sanity/):

```bash
cd sanity
npm install
npx sanity login   # once
npx sanity deploy  # hosts Studio at https://<hostname>.sanity.studio
```

Set **`SANITY_STUDIO_PROJECT_ID`** and **`SANITY_STUDIO_DATASET`** (or reuse `SANITY_PROJECT_ID` / `SANITY_DATASET`) so the Studio targets the correct project.

Alternatively you can host the Studio build as a **second Vercel project** (`sanity build` → static output); `sanity deploy` is usually simpler.

---

## Split origins and CORS

The browser calls **`NEXT_PUBLIC_API_URL`** directly for dashboard/API routes from the client. The backend must list your frontend origin in **`FRONTEND_URL`** (and thus `allow_origins` in FastAPI CORS).

---

## Quick checklist

- [ ] Backend deployed with **persistent disk** for `storage/` + `failed_writes/` (or equivalent env paths)
- [ ] `FRONTEND_URL` on backend matches Vercel URL
- [ ] `NEXT_PUBLIC_API_URL` + `INTERNAL_API_URL` on Vercel match backend public URL
- [ ] Sanity IDs/tokens set on frontend + backend as in `.env.example`
- [ ] Studio deployed (`sanity deploy`) or hosted elsewhere for editors
