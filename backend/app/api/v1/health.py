"""
Health and readiness endpoints.

/health -> is the process alive
/ready  -> is the process able to serve traffic (DB/Redis reachable)
"""
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {"status": "ok"}


@router.get("/ready")
async def ready():
    settings = get_settings()
    # Phase 2 note: DB/Redis connectivity checks are wired in once
    # app/db/session.py exists (Phase 11). For now this reports config state
    # so it's obvious whether the app is running in DEMO_MODE.
    return {
        "status": "ok",
        "demo_mode": settings.DEMO_MODE,
        "env": settings.ENV,
    }
