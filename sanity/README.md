# Prism Sanity Studio

Schemas and Sanity Studio v3 config for Prism (`accountResearchProfile`, `productPageContent`, `enrichmentVersion`, etc.).

## Local development

From repo root after copying `.env.example` → `.env` (include `SANITY_STUDIO_PROJECT_ID` / `SANITY_STUDIO_DATASET`, or reuse `SANITY_PROJECT_ID` / `SANITY_DATASET`):

```bash
cd sanity
npm install
npm run dev
```

Studio defaults to **http://localhost:3333**. Docker Compose also exposes **`sanity-studio`** on `:3333` via [`docker-compose.yml`](../docker-compose.yml).

## Production: host with Sanity (`sanity deploy`)

Sanity hosts the compiled Studio at `https://<hostname>.sanity.studio`:

```bash
cd sanity
npm install
npx sanity login    # once per machine
npx sanity deploy   # choose hostname when prompted
```

Ensure env vars match your Sanity project (`SANITY_STUDIO_PROJECT_ID`, `SANITY_STUDIO_DATASET` — see [`sanity.config.ts`](sanity.config.ts)).

See **[DEPLOYMENT.md](../DEPLOYMENT.md)** for how Studio fits next to Vercel (frontend) and the Docker backend.
