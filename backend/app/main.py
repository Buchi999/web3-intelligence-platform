"""
Application entrypoint.

Run with: uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import health, wallet, collection, reports
from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler
from app.core.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("startup", extra={"demo_mode": settings.DEMO_MODE, "env": settings.ENV})
    if settings.DEMO_MODE:
        logger.warning(
            "Running in DEMO_MODE — no ETHERSCAN_API_KEY configured. "
            "All wallet/collection data will be clearly labeled as sample data, not real chain data."
        )
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Wallet, token, and NFT intelligence built on public blockchain data. "
    "Read-only analytics — never requests private keys or seed phrases.",
    lifespan=lifespan,
)

# CORS: tighten allow_origins to your real frontend domain(s) before production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppError, app_error_handler)

app.include_router(health.router, prefix="/api/v1")
app.include_router(wallet.router, prefix="/api/v1")
app.include_router(collection.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
