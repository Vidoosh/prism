"""FastAPI routes."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from config import get_settings
from integrations.hubspot_client import create_hubspot_properties
from integrations.sanity_client import seed_products
from pipeline.batch_processor import load_batch, parse_urls_from_csv, prepare_batch, run_batch_job
from pipeline.dead_letter import delete_entry, list_entries, load_entry
from pipeline.orchestrator import run_pipeline
from pipeline.storage import list_runs, load_run, load_run_by_domain

router = APIRouter()
logger = logging.getLogger(__name__)


class RunRequest(BaseModel):
    url: str = Field(..., description="Company website URL")


class RunResponse(BaseModel):
    run_id: str


@router.post("/api/pipeline/run", response_model=RunResponse)
async def start_run(body: RunRequest) -> RunResponse:
    run_id = str(uuid.uuid4())
    logger.info("[api] step=enqueue_pipeline POST /api/pipeline/run run_id=%s url=%s", run_id, body.url)

    async def _bg() -> None:
        await run_pipeline(body.url, run_id)

    asyncio.create_task(_bg())
    logger.info("[api] step=accepted POST /api/pipeline/run run_id=%s (background task started)", run_id)
    return RunResponse(run_id=run_id)


@router.get("/api/pipeline/status/{run_id}")
async def run_status(run_id: str) -> dict[str, Any]:
    logger.debug("[api] GET /api/pipeline/status/%s", run_id)
    r = load_run(run_id)
    if not r:
        raise HTTPException(status_code=404, detail="run not found")
    return r.model_dump(mode="json")


@router.post("/api/pipeline/batch")
async def batch_upload(file: UploadFile = File(...)) -> dict[str, str]:
    logger.info("[api] step=batch_upload POST /api/pipeline/batch filename=%s", file.filename)
    raw = (await file.read()).decode("utf-8", errors="replace")
    urls = parse_urls_from_csv(raw)
    if not urls:
        logger.warning("[api] step=batch_upload rejected: no URLs in CSV")
        raise HTTPException(status_code=400, detail="No URLs found in CSV")
    batch_id, uniq = prepare_batch(urls)
    logger.info(
        "[api] step=batch_enqueued batch_id=%s distinct_urls=%s",
        batch_id,
        len(uniq),
    )

    async def _bg() -> None:
        await run_batch_job(batch_id, uniq)

    asyncio.create_task(_bg())
    return {"batch_id": batch_id}


@router.get("/api/pipeline/batch/{batch_id}")
async def batch_status(batch_id: str) -> dict[str, Any]:
    logger.debug("[api] GET /api/pipeline/batch/%s", batch_id)
    b = load_batch(batch_id)
    if not b:
        raise HTTPException(status_code=404, detail="batch not found")
    return b.model_dump(mode="json")


@router.get("/api/results")
async def results(limit: int = 50, offset: int = 0) -> dict[str, Any]:
    logger.debug("[api] GET /api/results limit=%s offset=%s", limit, offset)
    rows = list_runs(limit=limit, offset=offset)
    return {"items": [r.model_dump(mode="json") for r in rows], "limit": limit, "offset": offset}


@router.get("/api/results/{domain:path}")
async def result_by_domain(domain: str) -> dict[str, Any]:
    logger.debug("[api] GET /api/results/%s", domain)
    lookup = domain.replace("-", ".") if "." not in domain and "-" in domain else domain
    r = load_run_by_domain(lookup)
    if not r:
        r = load_run_by_domain(domain)
    if not r:
        raise HTTPException(status_code=404, detail="not found")
    return r.model_dump(mode="json")


@router.get("/api/landing/{domain:path}")
async def landing_by_domain(domain: str) -> dict[str, Any]:
    logger.debug("[api] GET /api/landing/%s", domain)
    lookup = domain.replace("-", ".") if "." not in domain and "-" in domain else domain
    r = load_run_by_domain(lookup)
    if not r:
        r = load_run_by_domain(domain)
    if not r:
        raise HTTPException(status_code=404, detail="not found")
    content = r.landing_page_content
    if not content:
        raise HTTPException(status_code=404, detail="landing page content not available")
    return content


@router.get("/api/dead-letter")
async def dead_letter_list() -> dict[str, Any]:
    logger.debug("[api] GET /api/dead-letter")
    return {"items": [e.model_dump(mode="json") for e in list_entries()]}


@router.post("/api/dead-letter/{entry_id}/retry")
async def dead_letter_retry(entry_id: str) -> dict[str, Any]:
    logger.info("[api] step=dead_letter_retry POST entry_id=%s", entry_id)
    e = load_entry(entry_id)
    if not e:
        raise HTTPException(status_code=404, detail="unknown entry")
    url = (e.partial or {}).get("url") or f"https://{e.domain}"
    logger.info(
        "[api] step=dead_letter_retry running_pipeline domain=%s url=%s",
        e.domain,
        url,
    )
    res = await run_pipeline(url)
    if res.status == "completed":
        delete_entry(entry_id)
        logger.info("[api] step=dead_letter_retry entry_id=%s removed after success", entry_id)
    else:
        logger.warning(
            "[api] step=dead_letter_retry entry_id=%s pipeline_status=%s (entry kept)",
            entry_id,
            res.status,
        )
    return res.model_dump(mode="json")


@router.post("/api/setup/hubspot")
async def setup_hubspot() -> dict[str, str]:
    logger.info("[api] step=setup POST /api/setup/hubspot")
    s = get_settings()
    if not s.hubspot_access_token:
        raise HTTPException(status_code=400, detail="HUBSPOT_ACCESS_TOKEN missing")
    await create_hubspot_properties(s.hubspot_access_token)
    logger.info("[api] step=setup hubspot properties ensured")
    return {"status": "ok"}


@router.post("/api/setup/sanity")
async def setup_sanity() -> dict[str, str]:
    logger.info("[api] step=setup POST /api/setup/sanity")
    await seed_products()
    logger.info("[api] step=setup sanity product seed complete")
    return {"status": "ok"}


@router.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
