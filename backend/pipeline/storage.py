"""Persist pipeline run results to disk for API listing."""

from __future__ import annotations

from pathlib import Path

from config import get_settings
from models.schemas import PipelineRunResult


def _runs_dir() -> Path:
    s = get_settings()
    p = Path(s.storage_dir) / "runs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def save_run(result: PipelineRunResult) -> None:
    path = _runs_dir() / f"{result.run_id}.json"
    path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    if result.domain:
        domain_path = _runs_dir() / f"domain-{slugify_domain(result.domain)}.json"
        domain_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")


def slugify_domain(domain: str) -> str:
    return domain.replace(".", "-").lower()


def load_run(run_id: str) -> PipelineRunResult | None:
    path = _runs_dir() / f"{run_id}.json"
    if not path.exists():
        return None
    return PipelineRunResult.model_validate_json(path.read_text(encoding="utf-8"))


def load_run_by_domain(domain: str) -> PipelineRunResult | None:
    path = _runs_dir() / f"domain-{slugify_domain(domain)}.json"
    if not path.exists():
        return None
    return PipelineRunResult.model_validate_json(path.read_text(encoding="utf-8"))


def list_runs(limit: int = 100, offset: int = 0) -> list[PipelineRunResult]:
    files = sorted(_runs_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[PipelineRunResult] = []
    for p in files:
        if p.name.startswith("domain-"):
            continue
        try:
            out.append(PipelineRunResult.model_validate_json(p.read_text(encoding="utf-8")))
        except Exception:
            continue
    return out[offset : offset + limit]
