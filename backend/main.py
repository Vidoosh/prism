"""FastAPI application entrypoint."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config import get_settings


def _configure_logging() -> None:
    """Ensure app loggers emit at LOG_LEVEL (default INFO) when running under uvicorn."""
    settings = get_settings()
    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)
    fmt = "%(asctime)s | %(levelname)-5s | %(name)s | %(message)s"
    if not logging.root.handlers:
        logging.basicConfig(level=level, format=fmt, datefmt="%Y-%m-%dT%H:%M:%S")
    else:
        logging.getLogger().setLevel(level)


_configure_logging()

app = FastAPI(title="Prism Pipeline API", version="0.1.0")

settings = get_settings()
origins = [
    settings.frontend_url,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "prism-pipeline", "docs": "/docs"}


app.include_router(router)
