"""CSV batch processing with bounded concurrency."""

from __future__ import annotations

import asyncio
import csv
import io
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from config import get_settings
from models.schemas import BatchJobStatus
from pipeline.orchestrator import run_pipeline

logger = logging.getLogger(__name__)


def _batch_dir() -> Path:
    p = Path(get_settings().storage_dir) / "batches"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _save_batch(status: BatchJobStatus) -> None:
    path = _batch_dir() / f"{status.batch_id}.json"
    path.write_text(status.model_dump_json(indent=2), encoding="utf-8")


def load_batch(batch_id: str) -> BatchJobStatus | None:
    path = _batch_dir() / f"{batch_id}.json"
    if not path.exists():
        return None
    return BatchJobStatus.model_validate_json(path.read_text(encoding="utf-8"))


def parse_urls_from_csv(text: str) -> list[str]:
    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames:
        lower = {h.lower().strip(): h for h in reader.fieldnames}
        for key in ("url", "website", "domain", "company_url"):
            if key in lower:
                url_col = lower[key]
                return [str(row.get(url_col, "")).strip() for row in reader if row.get(url_col)]
    reader2 = csv.reader(io.StringIO(text))
    rows = list(reader2)
    if not rows:
        return []
    return [row[0].strip() for row in rows[1:] if row and row[0].strip()]


def prepare_batch(urls: list[str]) -> tuple[str, list[str]]:
    """Return (batch_id, deduped urls). Persists initial batch row."""
    batch_id = str(uuid.uuid4())
    uniq: list[str] = []
    seen: set[str] = set()
    for u in urls:
        u = u.strip()
        if not u or u in seen:
            continue
        seen.add(u)
        uniq.append(u)

    status = BatchJobStatus(
        batch_id=batch_id,
        status="running",
        total=len(uniq),
        completed=0,
        failed=0,
        in_progress=len(uniq),
        created_at=datetime.now(timezone.utc),
    )
    _save_batch(status)
    logger.info(
        "[batch] step=prepared batch_id=%s total_urls=%s",
        batch_id,
        len(uniq),
    )
    return batch_id, uniq


async def run_batch_job(batch_id: str, urls: list[str]) -> None:
    settings = get_settings()
    sem = asyncio.Semaphore(max(1, settings.batch_concurrency))
    lock = asyncio.Lock()
    logger.info(
        "[batch] step=start batch_id=%s urls=%s concurrency=%s",
        batch_id,
        len(urls),
        settings.batch_concurrency,
    )

    async def one(url: str) -> None:
        async with sem:
            logger.info("[batch] step=url_start batch_id=%s url=%s", batch_id, url)
            res = await run_pipeline(url)
            logger.info(
                "[batch] step=url_done batch_id=%s url=%s domain=%s pipeline_status=%s",
                batch_id,
                url,
                res.domain,
                res.status,
            )
            async with lock:
                st = load_batch(batch_id)
                if not st:
                    return
                key = res.domain or url
                st.results[key] = res
                if res.status == "completed":
                    st.completed += 1
                else:
                    st.failed += 1
                st.in_progress = max(0, st.total - st.completed - st.failed)
                if st.completed + st.failed >= st.total:
                    st.status = "completed"
                _save_batch(st)

    await asyncio.gather(*(one(u) for u in urls))
    st = load_batch(batch_id)
    if st:
        st.in_progress = 0
        st.status = "completed"
        _save_batch(st)
        logger.info(
            "[batch] step=complete batch_id=%s total=%s completed=%s failed=%s",
            batch_id,
            st.total,
            st.completed,
            st.failed,
        )
    else:
        logger.warning("[batch] step=complete batch_id=%s error=batch_state_missing", batch_id)


async def run_batch(urls: list[str]) -> str:
    """Runs synchronously to completion (CLI/tests)."""
    batch_id, uniq = prepare_batch(urls)
    await run_batch_job(batch_id, uniq)
    return batch_id
