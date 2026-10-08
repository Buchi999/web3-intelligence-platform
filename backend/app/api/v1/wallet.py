"""
Wallet analysis endpoints.

TODO (Phase 4+): implement real logic. These routes exist now so the API
surface and OpenAPI docs are visible from Phase 2 onward, and so the
frontend can be built against a stable contract before the backend logic
lands. Every response is explicitly marked as a stub — never fake data
silently.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/wallet", tags=["wallet"])


@router.get("/{address}")
async def get_wallet(address: str):
    # TODO(Phase 4): validate checksum address, call BlockchainProvider
    return {"status": "not_implemented", "address": address, "note": "Implemented in Phase 4"}


@router.get("/{address}/transactions")
async def get_wallet_transactions(address: str):
    # TODO(Phase 5)
    return {"status": "not_implemented", "address": address, "note": "Implemented in Phase 5"}


@router.get("/{address}/tokens")
async def get_wallet_tokens(address: str):
    # TODO(Phase 6)
    return {"status": "not_implemented", "address": address, "note": "Implemented in Phase 6"}


@router.get("/{address}/nfts")
async def get_wallet_nfts(address: str):
    # TODO(Phase 7)
    return {"status": "not_implemented", "address": address, "note": "Implemented in Phase 7"}


@router.get("/{address}/analysis")
async def get_wallet_analysis(address: str):
    # TODO(Phase 9): behavior classification + risk scoring
    return {"status": "not_implemented", "address": address, "note": "Implemented in Phase 9"}
