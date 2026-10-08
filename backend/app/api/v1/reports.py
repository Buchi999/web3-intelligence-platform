"""
Report generation endpoint.

TODO (Phase 13): build report from a completed analysis and export PDF.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("")
async def create_report():
    # TODO(Phase 13)
    return {"status": "not_implemented", "note": "Implemented in Phase 13"}
