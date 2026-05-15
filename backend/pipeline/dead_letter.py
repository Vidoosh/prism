"""Dead-letter queue for failed writes / stages."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import get_settings
from models.schemas import DeadLetterEntry

logger = logging.getLogger(__name__)


def _dlq_dir() -> Path:
    s = get_settings()
    p = Path(s.failed_writes_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def enqueue(stage: str, domain: str, error: str, partial: dict[str, Any] | None = None) -> str:
    eid = str(uuid.uuid4())
    entry = DeadLetterEntry(
        id=eid,
        domain=domain,
        stage=stage,
        error=error,
        timestamp=datetime.now(timezone.utc).isoformat(),
        partial=partial or {},
    )
    path = _dlq_dir() / f"{eid}.json"
    path.write_text(entry.model_dump_json(indent=2), encoding="utf-8")
    logger.warning(
        "[dead-letter] stage=%s domain=%s entry_id=%s error=%s",
        stage,
        domain,
        eid,
        error[:500] + ("…" if len(error) > 500 else ""),
    )
    return eid


def list_entries() -> list[DeadLetterEntry]:
    out: list[DeadLetterEntry] = []
    for p in sorted(_dlq_dir().glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            out.append(DeadLetterEntry.model_validate_json(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out


def load_entry(eid: str) -> DeadLetterEntry | None:
    path = _dlq_dir() / f"{eid}.json"
    if not path.exists():
        return None
    return DeadLetterEntry.model_validate_json(path.read_text(encoding="utf-8"))


def delete_entry(eid: str) -> None:
    path = _dlq_dir() / f"{eid}.json"
    if path.exists():
        path.unlink()
