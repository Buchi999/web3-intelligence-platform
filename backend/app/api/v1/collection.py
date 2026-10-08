"""
NFT collection analysis endpoints.

TODO (Phase 7-8): implement real logic against BlockchainProvider.
"""
from fastapi import APIRouter

router = APIRouter(prefix="/collection", tags=["collection"])


@router.get("/{address}")
async def get_collection(address: str):
    # TODO(Phase 7)
    return {"status": "not_implemented", "address": address, "note": "Implemented in Phase 7"}


@router.get("/{address}/holders")
async def get_collection_holders(address: str):
    # TODO(Phase 8)
    return {"status": "not_implemented", "address": address, "note": "Implemented in Phase 8"}


@router.get("/{address}/analysis")
async def get_collection_analysis(address: str):
    # TODO(Phase 8-9)
    return {"status": "not_implemented", "address": address, "note": "Implemented in Phase 8-9"}
