# Prism — Account Research to Personalized Content Pipeline

**Monorepo:** Python/FastAPI enrichment API, Next.js dashboard + personalized landing pages, Sanity CMS studio/schemas, HubSpot CRM custom company properties.

Given any company URL, Prism scrapes the public website **in parallel** with optional LinkedIn enrichment and Gemini-powered open-web research, runs a **structured Gemini enrichment pass** (analyst + CRM-ready copywriter), then a **second Gemini pass** that emits rich landing-page JSON stored on the pipeline run and exposed via the API. Results are written to **Sanity** (account profile + versioning) and **HubSpot** (`certify_*` properties + landing/Sanity links). The Next.js app renders **`/lp/{slug}`** using **API-first** landing content when present, with a **Sanity GROQ fallback** for older runs.

---

## Table of Contents

1. [Architecture](#architecture)
2. [Design Decisions](#design-decisions--what-was-built-and-why)
3. [Handling Blocked and Thin-Content Sites](#handling-blocked-and-thin-content-sites)
4. [Scaling to Hundreds of Accounts](#scaling-to-hundreds-of-accounts)
5. [Gong and Salesforce Integration](#how-gong-and-salesforce-would-augment-the-pipeline)
6. [Landing Page Rendering](#landing-page-rendering)
7. [API Endpoints](#api-endpoints)
8. [Measurement](#measurement--connecting-pipeline-to-revenue)
9. [Known Limitations](#known-limitations-and-future-improvements)
10. [Quick Start](#quick-start)
11. [Troubleshooting](#troubleshooting)
12. [Demo (Loom)](#demo-loom)

---

## Architecture

```mermaid
flowchart LR
  URL["Company URL"] --> Norm["Normalize"]
  Norm --> Parallel["Parallel stages"]
  Parallel --> Scrape["3-Tier Scrape\nhttpx → Playwright → Apify"]
  Parallel --> LinkedIn["LinkedIn\nApify"]
  Parallel --> WebRes["Web research\nGEMINI_GOOGLE_SEARCH_MODEL\nplus Google Search tool"]
  Scrape --> Merge["Merge into ScrapedContent"]
  LinkedIn --> Merge
  WebRes --> Merge
  Merge --> Enrich["Gemini enrichment\nGEMINI_MODEL\nstructured EnrichmentResult"]
  Enrich --> LandingPass["Gemini landing JSON\nGEMINI_MODEL\noptional second pass"]
  LandingPass --> Sanity["Sanity CMS\nupsert plus versioning"]
  Enrich --> Sanity
  LandingPass --> HubSpot["HubSpot CRM\ncertify_* properties"]
  Enrich --> HubSpot
  LandingPass --> ApiLanding["Backend GET /api/landing/{domain}"]
  ApiLanding --> LP["Next.js /lp/slug"]
  Sanity --> LP
```

Each stage is independently resilient: failures enqueue dead-letter entries where applicable and degrade gracefully rather than aborting the entire flow. Scrape, LinkedIn, and web research results merge into `ScrapedContent`; enrichment produces `EnrichmentResult`; the landing pass produces JSON stored on the run (`landing_page_content`) and served by the API.

**Key architectural principle:** the pipeline aims to leave visibility in CRM/CMS even when upstream stages fail (e.g. blocked scrape → low-confidence enrichment). Inspect each run’s `stages` array for per-stage success; the top-level run `status` is `"completed"` for most paths unless URL normalization fails early.

**Assignment alignment:** The brief asks for a single LLM step acting as analyst plus copywriter for structured JSON — Prism satisfies that in the **enrichment pass** (ICP, intent, pain, hero/value prop/CTA blocks for Sanity and HubSpot). The **landing pass** is an extra PoC layer that turns that profile into a long-form page JSON without changing the core CRM/CMS contract.

---

## Design Decisions — What Was Built and Why

### Gemini vs Anthropic Claude (assignment vs implementation)

**Decision:** The role kickoff specifies Claude; this PoC uses **Google Gemini** — [`google-generativeai`](backend/ai/gemini_client.py) for enrichment + landing JSON, and [`google-genai`](backend/ai/web_research.py) with the **Google Search** tool for grounded web research.

**Why:** Gemini gives native JSON mode for the enrichment schema, a supported tooling path for live search grounding, and Flash-tier economics at batch scale. The prompt engineering approach (structured analyst + copywriter role, defensive parsing) maps cleanly to Claude or other APIs if you swap SDK + model IDs.

### Primary Gemini enrichment pass (analyst + CRM copywriter)

**Decision:** One structured Gemini call ingests merged scrape + LinkedIn + web research and returns JSON mapped to `EnrichmentResult`: ICP tier/score, intent signals, pain points, and Sanity/HubSpot content blocks (hero, value prop, pain paragraph, CTA, etc.).

**Why:** A single enrichment payload keeps CRM and CMS contracts aligned — scoring and outbound copy stay mutually consistent. Gemini `response_mime_type: application/json` enforces shape; [`parse_enrichment_json`](backend/ai/response_parser.py) tolerates minor formatting drift.

**What breaks:** Very rich sites may hit context limits — mitigated by summarizing each page to ~1,500 tokens before assembly.

### Second Gemini pass: long-form landing JSON

**Decision:** After enrichment succeeds, [`generate_landing_content`](backend/ai/gemini_client.py) runs a **second** Gemini call whose JSON is stored on the run as `landing_page_content` and served by [`GET /api/landing/{domain}`](backend/api/routes.py) (see [API Endpoints](#api-endpoints)).

**Why:** Twelve on-page sections (below) would overload the enrichment schema and HubSpot property surface. Separating concerns keeps `EnrichmentResult` stable for Sanity/HubSpot while the frontend renders a deep LP from dedicated JSON.

**Failure mode:** Landing failures enqueue dead-letter (`landing_page`) but **do not** fail the pipeline. The Next app falls back to Sanity GROQ + [`LegacyLanding`](frontend/src/components/landing/legacy-landing.tsx) when API landing JSON is absent.

### Pre-processing before LLM

**Decision:** Raw HTML is never sent to the LLM. Each scraped page goes through `extract_clean_text_from_html` (strips nav, footers, scripts, cookie banners) and `summarize_page_for_llm` (keeps headings + first sentence per paragraph, capped at 1,500 tokens per page) before assembly into a structured JSON bundle.

**Why:** Passing raw HTML wastes tokens on markup that carries no intelligence value. Pre-processing produces a consistent input schema regardless of how different companies structure their websites — the LLM always receives the same field names (`homepage_text`, `about_text`, `career_titles`, `blog_excerpts`, `press_excerpts`) with quality metadata (`scrape_quality`, `pages_blocked`, `thin_content_pages`). This makes prompt engineering stable and reproducible.

### Model configuration (`GEMINI_MODEL`, `GEMINI_GOOGLE_SEARCH_MODEL`)

**Decision:** Model IDs are **environment-driven**. [`config.py`](backend/config.py) defaults both `GEMINI_MODEL` and `GEMINI_GOOGLE_SEARCH_MODEL` to `gemini-2.5-flash-lite`; [`.env.example`](.env.example) may pin newer Flash SKUs (e.g. `gemini-3.1-flash-lite`) — use whichever your Google AI project exposes.

**Why:** Web research requires the **`google-genai`** client with **`GoogleSearch`** grounding; enrichment + landing use **`google-generativeai`**. Keeping IDs in `.env` avoids code churn when Google rotates model names.

### Sanity document identity: `_id = account-{domain}`

**Decision:** Every company's Sanity document uses a deterministic `_id` derived from the domain, enabling idempotent `createOrReplace` mutations.

**Why:** Re-running the pipeline against the same URL overwrites the document rather than creating duplicates. Before overwriting, the previous version is snapshot into an `enrichmentVersion` document (linked via `account_reference`), preserving the full history of how a company's ICP score, intent signals, and content evolved over time. This versioning is critical for measuring whether re-enrichment produces meaningful signal drift — if a company's intent score jumps from 30 to 75 between runs, something changed (new funding round, new job postings) and that delta is itself an actionable signal.

The five `productPageContent` seed documents (`product-credentialing`, `product-licensing`, `product-compliance-monitoring`, `product-roster-management`, `product-provider-hub`) are auto-upserted in the same mutation batch to guarantee referential integrity for the `primary_product_fit` references.

### Flat HubSpot `certify_*` properties vs custom objects

**Decision:** All enrichment data is stored as flat custom properties on the Company record, prefixed with `certify_` to namespace cleanly.

**Why:** HubSpot's free tier does not support custom objects. Even on paid tiers, flat properties are more immediately useful for workflows, list segmentation, and reporting without requiring custom object setup. The `certify_` prefix means these properties coexist cleanly with any existing CRM properties, and an SDR can see the ICP tier, intent score, value prop, and landing page link directly on the company record without navigating to a related object.

**Tradeoff acknowledged:** This flattening means granular per-signal-type data (individual job posting titles, per-page scrape results) can't be stored in HubSpot. The full structured data lives in Sanity — HubSpot carries the summary scores and the SDR-facing content. The `certify_sanity_content_url` property links back to the Sanity document for anyone who needs the full dossier.

### 3-tier scraping escalation: httpx → Playwright → Apify

**Decision:** Start with the cheapest, fastest method and escalate only when needed.

**Why:** Most company websites serve static HTML that `httpx` handles in milliseconds. Playwright (headless Chromium) is only invoked when `is_js_rendered_hint` detects a JS-heavy page with fewer than 400 words of static content — this avoids spinning up a browser for sites that don't need it. Apify (managed Website Content Crawler with residential proxies) is the final escalation, triggered only when all pages are blocked or total scraped words fall below 120 — this handles Cloudflare-protected sites and aggressive bot detection at scale.

**Cost profile:** httpx is essentially free. Playwright adds ~2s of latency per page but no API cost. Apify costs ~$0.002/page but handles the hardest cases reliably. For a batch of 500 companies, the expected distribution is roughly 80% httpx, 15% Playwright, 5% Apify.

### LinkedIn enrichment via Apify

**Decision:** When an Apify token is configured, the pipeline resolves the company's LinkedIn page and scrapes the public company profile for additional firmographic signals.

**Why:** Company websites are often thin on the specific data points that matter for ICP scoring — employee count, geographic footprint, industry classification, specialties. LinkedIn company profiles are consistently structured and rich in these signals. The LinkedIn data is merged into the scrape bundle as `linkedin_data` and referenced by the Gemini prompt for higher-confidence classifications.

### Web research via Gemini + Google Search grounding

**Decision:** A dedicated call using **`GEMINI_GOOGLE_SEARCH_MODEL`** and the Google Search tool ([`research_domain_with_google_search`](backend/ai/web_research.py)) produces structured open-web intelligence.

**Why:** Sites omit timing-sensitive signals (funding, exec moves, incidents). Grounded search complements scrape + LinkedIn; results merge into `ScrapedContent.web_research` for the enrichment prompt.

---

## Handling Blocked and Thin-Content Sites

The pipeline is designed around the assumption that real-world scraping will encounter messiness. Every failure mode degrades gracefully rather than crashing.

### Site blocks scraping (HTTP 403, 429, 503)

**Detection:** The HTTP scraper checks response status codes. A 403, 429, or 503 marks the page as blocked.

**Escalation chain:**
1. **Wayback Machine fallback** — immediately retries via `https://web.archive.org/web/{original_url}` using the same HTTP client. Cached snapshots are often sufficient for about/product pages that rarely change.
2. **Playwright headless browser** — if the page appears JS-rendered (detected via framework signatures in HTML and low static word count), Chromium renders the page with a 1,500ms wait for dynamic content.
3. **Apify Website Content Crawler** — if all pages are blocked or total words scraped fall below 120, the entire domain is handed to Apify's managed crawler with residential proxies, adaptive rendering, and anti-bot handling.
4. **Minimal stub** — if all fallbacks fail, the pipeline sets `scrape_quality = "blocked"` and `scrape_blocked = true`, then continues with the domain name as the only input to the LLM. The Gemini prompt is explicitly instructed to produce a low-confidence assessment without specific numeric claims when the input indicates a blocked or thin scrape.

### JavaScript-rendered sites with thin static HTML

**Detection:** `is_js_rendered_hint()` checks for JS framework signatures (React, Next.js, Vue, Angular meta tags or script patterns) combined with a body word count under 400.

**Handling:** Playwright renders the page with `domcontentloaded` wait + 1,500ms buffer for async data loading. If Playwright recovers meaningful content, the tier is upgraded to `"playwright"` and the extracted text replaces the thin static version.

### No careers page found

**Detection:** Link discovery and direct URL construction (`/careers`, `/jobs`, `/join-us`, `/open-positions`) both fail to locate a careers page.

**Impact:** The careers page is the single most valuable intent signal source — open credentialing/enrollment roles are a Tier-1 buying trigger. Its absence significantly reduces signal quality. The pipeline applies a **-15 point penalty** to `intent_score` and appends the adjustment rationale to `confidence_rationale`.

**Why this matters:** Without careers page data, the pipeline cannot detect whether the company is actively hiring credentialing coordinators (a strong buying signal) or mentions competitor tools in job descriptions. The intent score reduction ensures these companies are routed to nurture rather than immediate SDR outreach, preventing wasted rep time on incomplete intelligence.

### Thin or non-descriptive homepage

**Detection:** Pages with fewer than 150 words of extracted body text are flagged as thin content.

**Handling:** The scraper doesn't give up after the homepage — it crawls up to 14 URLs discovered via sitemap/robots.txt and direct URL construction for high-value paths (`/about`, `/company`, `/products`, `/services`, `/blog`, `/press`). Thin pages are still included as supplementary evidence but are not weighted as primary signals. The `scrape_quality` is downgraded to `"thin"` or `"medium"` based on the ratio of thin pages to total pages scraped.

### LLM returns invalid JSON

**Detection:** `parse_enrichment_json` attempts `json.loads` after stripping markdown code fences. If parsing fails, or required fields are missing, the response is flagged.

**Handling:** The parser is deliberately flexible — it handles alternate key casings (`painPoints` vs `pain_points`), coerces lists vs single dicts, and uses regex to extract structured IDs (e.g., `P1.1` pain IDs, `T1/T2/T3` signal tiers). If JSON is fundamentally malformed, the pipeline returns a minimal `EnrichmentResult` with `data_confidence = "failed"` and `requires_review = True`. This stub is still written to both Sanity and HubSpot — a failed enrichment is visible in the CRM as a record that needs manual attention, not silently dropped.

### Sanity / HubSpot API failures

**Handling:** All API writes use retry logic (Sanity: retries at 0, 2, 4, 8s intervals; HubSpot: single retry with field-stripping on `INVALID_OPTION` errors). On terminal failure, the enrichment JSON is persisted to `failed_writes/{timestamp}-{domain}.json` as a dead-letter entry. The API exposes `GET /api/dead-letter` and `POST /api/dead-letter/{entry_id}/retry` endpoints for manual recovery. The pipeline continues past write failures and still marks the run as `"completed"` — inspect the `stages` array on each result for per-stage success/failure detail.

---

## Scaling to Hundreds of Accounts

### Concurrency model

The batch processor uses an `asyncio.Semaphore` with a configurable `BATCH_CONCURRENCY` limit (default: 3 parallel pipeline runs). Each pipeline run internally uses `asyncio.to_thread` for blocking operations (Gemini API calls, Apify actors, LinkedIn resolution) to avoid starving the event loop.

For a batch of 500 URLs at concurrency 3, expected wall-clock time is roughly 2-3 hours (dominated by scraping and Gemini latency per company). Increasing concurrency to 10 would cut this proportionally, subject to API rate limits.

### Scraping rate limits

The httpx client is configured with `max_connections=20` and `max_keepalive_connections=10`. URL discovery prioritizes and deduplicates to cap at 14 URLs per domain, preventing unbounded crawling. For Apify-escalated sites, the managed crawler handles its own proxy rotation and rate limiting internally.

At 500 companies x ~10 pages each = ~5,000 HTTP requests, the primary bottleneck is per-domain politeness, not aggregate throughput. The pipeline processes companies in parallel (not pages within a company), so per-domain rate limiting is naturally satisfied.

### LLM throughput

Per successful company run with `GEMINI_API_KEY` set: **one optional grounded web-research call** (`google-genai` + Google Search), **one enrichment call** (`google-generativeai`, structured JSON), and **one landing-page JSON call** when enrichment succeeds — roughly **three** Gemini-facing requests per domain at peak (fewer if keys/tokens omit stages). At batch concurrency 3, budget sustained RPM against your Google quota accordingly. Blocking operations run via `asyncio.to_thread` so the event loop stays responsive.

For bulk runs exceeding ~1,000 companies, Gemini's Batch API could lower cost for the enrichment pass; scrape → enrich → write separation keeps that swap localized.

### HubSpot API limits

HubSpot limits API calls to 100 requests per 10 seconds on free/starter tiers. The current pipeline makes 2 calls per company (search + create/update). For 500 companies, this requires ~17 minutes of API time at the rate limit ceiling. For larger batches, HubSpot's batch create/update endpoints support up to 100 objects per call — reducing 500 companies to 5 batch calls plus 5 search calls.

### Cost estimates

| Component | Per-company cost | 500-company batch |
|-----------|-----------------|-------------------|
| Scraping (httpx/Playwright) | ~$0 | ~$0 |
| Scraping (Apify, ~5% of sites) | ~$0.002 | ~$0.50 |
| LinkedIn enrichment (Apify) | ~$0.003 | ~$1.50 |
| Web research (`GEMINI_GOOGLE_SEARCH_MODEL`) | ~$0.003 | ~$1.50 |
| AI enrichment (`GEMINI_MODEL`) | ~$0.008 | ~$4.00 |
| Landing JSON (`GEMINI_MODEL`) | ~$0.004–0.008 | ~$2–4 |
| Sanity writes | negligible (free tier) | $0 |
| HubSpot writes | negligible (API-based) | $0 |
| **Total** | **~$0.015–0.03** | **~$8–12** |

### What breaks first at scale

1. **Apify costs** — if a large percentage of target sites require the Apify escalation tier, costs scale linearly. Mitigation: cache scrape results and skip re-scraping domains enriched within 30 days.
2. **Gemini rate limits** — sustained throughput above ~60 requests/minute may hit quota. Mitigation: implement a token-aware queue that estimates input tokens before queuing and regulates throughput.
3. **Storage** — pipeline run results are stored as JSON files on disk (`storage/`). At 10,000+ runs, this should migrate to a database. The current approach is deliberately simple for the PoC.

---

## How Gong and Salesforce Would Augment the Pipeline

The current pipeline produces a cold-start intelligence profile from public data. The transformative enhancement is layering in warm signals from Gong call transcripts and hot signals from Salesforce activity data.

### Gong call transcript integration

**What Gong provides:** When a prospect has had calls recorded in Gong, the transcript contains the exact words the buyer used to describe their pain, the objections they raised, the competitors they mentioned, and the decision timeline they implied. This is the highest-value intelligence available — and it's currently invisible to the scrape-only pipeline.

**How to integrate:** Pull Gong call transcripts via the Gong API (`/v2/calls` and `/v2/calls/{callId}/transcript`) filtered by company domain. For each company in the pipeline, retrieve the 3 most recent calls where a participant's email domain matches the target. Pass transcript excerpts (or Gong's own AI summaries) as a `gong_signals` input alongside the scraped data in the Gemini prompt.

**What this changes in the output:**
- **Pain points shift from inferred to verbatim.** If a VP of Operations said "we're spending 40 hours a week cleaning delegated rosters," that first-person statement overrides any inferred pain severity from website language.
- **Objections inform the CTA block.** If the company previously objected to price, the CTA should lead with ROI framing rather than feature depth.
- **Decision timeline gives urgency.** "We need NCQA certification by Q3" is a time-bounded signal that scraping can never produce — it should elevate the intent score and trigger immediate SDR routing.
- **Competitor mentions are confirmed, not inferred.** A call where the prospect says "we're evaluating Medallion" is qualitatively different from inferring competitor use from a job description.

**Data model addition (Sanity + HubSpot):**
```
gong_signals:
  gong_calls_available: boolean
  gong_last_call_date: datetime
  gong_verbatim_pain_statements: string[]
  gong_objections_raised: string[]
  gong_competitors_mentioned: string[]
  gong_decision_timeline: string
  gong_buyer_sentiment: string
```

The existing Sanity schema and HubSpot property group are structured so that adding these fields requires no migration — they extend the `accountResearchProfile` document and the `certify_*` property namespace without breaking the scrape-only path.

### Salesforce activity data integration

**What Salesforce provides:** Opportunity stage history, deal age, contact engagement history, past contract details for existing customers, and the structured record of every touchpoint the sales team has had with the account.

**How to integrate:** Query Salesforce via SOQL for the Account object matching the domain. Pull: opportunity stage and age, last activity date, contact titles, and any past contracts or churned customer status.

**What this changes in the output:**
- **Existing customers switch to expansion mode.** The content blocks should reference products they don't yet use, not the ones they have.
- **Open opportunities get deal acceleration content.** If a company is in "Proposal Sent" stage, the CTA should be "Questions about the proposal?" not "Book a demo."
- **Closed-lost accounts get re-engagement framing.** The pipeline notes the lost reason (if captured) and adjusts content to address the specific objection.
- **Deal velocity + Gong sentiment = deal health.** Stalled deals get different nurture content than companies in active evaluation.

**Data model addition:**
```
salesforce_signals:
  sf_account_id: string
  sf_open_opportunity: boolean
  sf_opportunity_stage: string
  sf_opportunity_age_days: number
  sf_last_activity_date: datetime
  sf_is_existing_customer: boolean
  sf_products_purchased: string[]
  sf_closed_lost_reason: string
```

### Combined signal architecture (future state)

In the mature pipeline, each company URL triggers a four-source enrichment:

```mermaid
flowchart TD
  URL["Company URL"] --> Scrape["Public Web Scrape\n(cold signals)"]
  URL --> Gong["Gong Transcripts\n(warm signals)"]
  URL --> SF["Salesforce Activity\n(hot signals)"]
  URL --> ThirdParty["3rd Party Enrichment\nClay / Apollo / ZoomInfo\n(verification layer)"]
  Scrape --> Gemini["Gemini Prompt\n(all four inputs,\nsource-labeled,\nconfidence-weighted)"]
  Gong --> Gemini
  SF --> Gemini
  ThirdParty --> Gemini
  Gemini --> Output["Enrichment Result\nwith signal hierarchy:\nGong overrides scrape,\nSF stage overrides\ninferred intent"]
```

Signals from Gong override inferences from scraping. Salesforce stage overrides inferred buying intent. The resulting content blocks reflect the full relationship context, not just what's publicly visible. The current PoC's data model is designed to accommodate this evolution without a schema migration — the `gong_signals` and `salesforce_signals` fields can be added as optional extensions to the existing document types.

---

## Landing Page Rendering

Personalized landing pages live at **`/lp/{slug}`** (e.g. `/lp/example-health-com`). Implementation: [`frontend/src/app/lp/[slug]/page.tsx`](frontend/src/app/lp/[slug]/page.tsx).

### API-first JSON + Sanity fallback

**Primary path:** The Next.js server loads **`GET /api/landing/{domain}`** (same origin via [`INTERNAL_API_URL`](frontend/src/lib/api.ts) / `NEXT_PUBLIC_API_URL`), which returns the **`landing_page_content`** stored on the latest [`PipelineRunResult`](backend/models/schemas.py). That JSON drives **twelve** React sections under [`frontend/src/components/landing/`](frontend/src/components/landing/).

**Fallback:** If the API returns 404 (no landing JSON — e.g. landing stage skipped or failed), the route loads Sanity via GROQ ([`frontend/src/lib/sanity.ts`](frontend/src/lib/sanity.ts)) and renders **`LegacyLanding`** — roughly the earlier five-block layout built from `accountResearchProfile`.

### Twelve-section layout (rich LP)

When API landing JSON is present, sections render in order:

1. **Hero** — headline/value framing (`HeroSection`)
2. **Pain** — narrative + proof (`PainSection`)
3. **Solution bridge** — positioning (`SolutionBridgeSection`)
4. **Social proof** — logos/stories (`SocialProofSection`)
5. **Product** — capability depth (`ProductSection`)
6. **ROI** — economics (`RoiSection`)
7. **Urgency / intent** — timing (`UrgencySection`)
8. **Objections** — preemptive answers (`ObjectionSection`)
9. **Trust bar** — credibility chips (`TrustBar`)
10. **Final CTA** — conversion (`FinalCtaSection`)
11. **Personalization meta** — internal ribbon (`PersonalizationMetaRibbon`)
12. **SEO block** — optional crawl-oriented copy (`SeoBlock`)

**Metadata:** [`generateMetadata`](frontend/src/app/lp/[slug]/page.tsx) prefers titles/descriptions from landing JSON when present.

### Sanity GROQ (fallback query)

```groq
*[_type == "accountResearchProfile" && domain == $domain][0]{
  company_name,
  domain,
  organization_type,
  pain_points,
  intent_signals,
  content_blocks,
  primary_product_fit,
  "product_details": primary_product_fit[]->{
    product_name,
    hero_copy,
    proof_points
  }
}
```

### URL design and access control

**Slug format:** Hyphenated domain (`example.com` → `example-com`). [`slugToDomain`](frontend/src/app/lp/[slug]/page.tsx) accepts either dotted or hyphenated slugs.

**Optional HMAC token:** When **`LANDING_PAGE_SECRET`** is set, requests must include **`?t=`** — see [`frontend/src/lib/landing-token.ts`](frontend/src/lib/landing-token.ts). If unset, pages are publicly reachable.

**Preview:** **`?preview=true`** shows an amber **Draft — Internal Preview Only** banner (does not toggle Sanity draft mode).

### Trigger from outbound

The pipeline writes **`certify_sanity_content_url`**, Sanity Studio deep links, and a **`landing_page_url`** derived from **`FRONTEND_URL`** + `/lp/{slug}` so reps can paste one outbound link — prospects hit API-backed LP JSON or legacy Sanity-backed UI depending on run outcome.

---

## API Endpoints

FastAPI routes ([`backend/api/routes.py`](backend/api/routes.py)); interactive docs at **`/docs`**.

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/` | Service metadata |
| POST | `/api/pipeline/run` | Body `{ "url": "..." }`; enqueue pipeline; returns `{ "run_id" }` |
| GET | `/api/pipeline/status/{run_id}` | Full run JSON from disk |
| POST | `/api/pipeline/batch` | Multipart CSV upload; returns `{ "batch_id" }` |
| GET | `/api/pipeline/batch/{batch_id}` | Batch progress JSON |
| GET | `/api/results` | Paginated runs (`limit`, `offset`) |
| GET | `/api/results/{domain}` | Latest run for domain (supports slug-style domains) |
| GET | `/api/landing/{domain}` | **`landing_page_content`** JSON only |
| GET | `/api/dead-letter` | Dead-letter queue listing |
| POST | `/api/dead-letter/{entry_id}/retry` | Re-run pipeline from queued payload |
| POST | `/api/setup/hubspot` | Ensure HubSpot `certify_*` properties (needs token) |
| POST | `/api/setup/sanity` | Seed product docs |
| GET | `/api/health` | Liveness `{ "status": "ok" }` |

---

## Measurement — Connecting Pipeline to Revenue

A pipeline that generates personalized content is only valuable if it impacts pipeline and revenue. The measurement framework connects pipeline operations to business outcomes across three dimensions.

### Pipeline quality metrics

- **Outbound reply rate:** Compare reply rates for emails that include a personalized landing page URL vs. generic outbound. Target: 2-3x lift over cold outreach baseline.
- **Meeting booked rate:** Track meetings booked from accounts enriched by the pipeline. Segment by ICP tier to validate scoring accuracy.
- **ICP tier-to-opportunity conversion:** Of companies scored Tier A, what percentage convert to qualified opportunities? Target: >=50%. If it's 20%, the scoring model is overweighting the wrong signals and the prompt needs refinement.

### Content quality metrics

- **SDR acceptance rate:** What percentage of AI-generated value props and headlines do SDRs send as-is vs. editing significantly? Low acceptance = prompt engineering needs iteration. Over time, the delta between the LLM's output and the SDR's edit becomes training data for prompt refinement.
- **Landing page engagement:** Time on page, scroll depth, and CTA click rate for pipeline-generated pages vs. generic pages.
- **A/B testing:** Same SDR email template with and without the personalized landing page link, controlling for ICP tier and rep quality.

### Data quality metrics

- **Intent signal predictive value:** Of companies with Tier-1 signals (open credentialing roles, geographic expansion, recent funding), what percentage book a meeting within 30 days of outreach? This validates the signal definitions and their tier assignments.
- **Re-enrichment drift:** Do companies re-enriched 90 days later show meaningfully changed ICP scores or new intent signals? The `enrichmentVersion` snapshots in Sanity enable this comparison. Meaningful drift validates the monitoring cadence; no drift suggests the re-enrichment interval can be extended.
- **Hook technique performance by ICP type:** Sanity tracks `hook_technique_used` on every enrichment. Combining this with CRM conversion data reveals which hooks work for which ICP types — regulatory guillotine may convert health plans while revenue leakage calculator converts digital health. This insight makes the prompt smarter over time.

### Feedback loops

1. **SDR edit tracking:** When an SDR modifies `certify_personalized_value_prop` in HubSpot before sending, the original and edited versions create implicit preference data for prompt refinement.
2. **Closed-won attribution:** When a deal closes, pull the account's enrichment history from Sanity. Identify which signals were present at first outreach. Over 50+ deals, patterns emerge — the signals most predictive of close become the highest-weighted in the ICP scoring formula.
3. **Content variant performance:** Track which `hook_technique_used` variants (regulatory guillotine, competitive clock, hiring intercept, etc.) correlate with higher reply rates per ICP segment. Feed winning patterns back into the prompt as preferred techniques for each organization type.

---

## Known Limitations and Future Improvements

- **LinkedIn / third-party enrichment is best-effort.** LinkedIn scraping via Apify depends on the actor's ability to resolve and access the company page. No ZoomInfo/Apollo/Clay verification layer is implemented.
- **No continuous re-enrichment trigger.** Re-enrichment is manual (re-submit the URL). A production system would schedule re-enrichment every 90 days for non-customer accounts and trigger immediate re-enrichment on HubSpot lifecycle stage changes.
- **Content requires human review.** The personalized content blocks are LLM-generated and should be reviewed by an SDR before external use. The `requires_review` flag and `data_confidence` levels help prioritize which accounts need more attention.
- **Provider count estimation is imprecise.** For companies that don't explicitly state their network size, the LLM infers from indirect signals (language like "hundreds of providers," employee count proxies). This inference is flagged in `confidence_rationale`.
- **HubSpot workflows are not automated in the PoC.** The `certify_*` properties support workflow triggers (Tier-A SDR alert, Tier-B nurture enrollment, 90-day re-enrichment reminder), but these must be configured in the HubSpot UI.
- **Social proof / layout differs by path.** Rich LP social proof comes from landing JSON when present; **`LegacyLanding`** still blends hardcoded proof patterns tied to `organization_type`.
- **Landing preview is cosmetic.** `?preview=true` adds a banner only; neither path toggles Sanity draft preview APIs — published vs preview uses the same fetched documents/run payloads.

---

## Quick Start

1. Copy [`.env.example`](.env.example) → `.env` and fill secrets (**minimum:** `GEMINI_API_KEY`, Sanity IDs/tokens; **HubSpot:** `HUBSPOT_ACCESS_TOKEN` Private App token starting with `pat-` for CRM writes).
2. `chmod +x setup.sh && ./setup.sh` (local venv + npm installs), **or** `docker compose up --build`.
3. **One-time setup (with tokens in `.env`):**
   - `curl -X POST http://localhost:8000/api/setup/hubspot` — create `certify_*` properties.
   - `curl -X POST http://localhost:8000/api/setup/sanity` — seed `productPageContent` docs.
4. Open **http://localhost:3000** — submit a URL or CSV batch.
5. Sanity Studio: **http://localhost:3333** (see `docker-compose`).
6. API docs: **http://localhost:8000/docs**.

### Landing pages

- URL pattern: `/lp/{domain-with-hyphens}` (e.g., `/lp/example-health-com`).
- Preview banner: `?preview=true`.
- Optional shared secret: set `LANDING_PAGE_SECRET` and open `/lp/{slug}?t={hmac}` (see [`frontend/src/lib/landing-token.ts`](frontend/src/lib/landing-token.ts)).

---

## Troubleshooting

### Sanity `409` — `documentReferenceDoesNotExistError`

Account docs reference `productPageContent` IDs. The pipeline auto-seeds those five product documents in the same mutation batch, so a fresh pull should fix this without running setup manually. If you still see 409s, confirm `SANITY_PROJECT_ID` / `SANITY_DATASET` match the project where you expect data.

### HubSpot `401` / `EXPIRED_AUTHENTICATION` with `1970-01-01`

Usually means `HUBSPOT_ACCESS_TOKEN` is missing, wrong, or not a Private App token. Use a current token from **Settings → Integrations → Private Apps** (starts with `pat-`). Remove quotes/spaces in `.env`, restart uvicorn.

---

## Demo (Loom)

Submission demo (two companies, pipeline end-to-end): [Loom recording](https://www.loom.com/share/03a0839c361c426eac5fd88edd70c20f).

---

## License

Apache-2.0 (see [LICENSE](LICENSE)).
