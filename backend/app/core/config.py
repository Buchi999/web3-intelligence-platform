"""
Application configuration.

Loads settings from environment variables (see .env.example).
Nothing here should ever contain a hard-coded secret.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "Web3 Wallet & NFT Intelligence Platform"
    ENV: str = "development"
    DEMO_MODE: bool = True  # auto-flips to False once real keys are detected (see get_settings)

    # Database
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/web3intel"

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"

    # Blockchain provider
    BLOCKCHAIN_RPC_URL: str | None = None
    ETHERSCAN_API_KEY: str | None = None
    CHAIN_ID: int = 1  # 1 = Ethereum mainnet (MVP chain, see architecture doc §3)

    # LLM provider (Groq — OpenAI-compatible chat completions API)
    GROQ_API_KEY: str | None = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    # Auth
    JWT_SECRET: str = "change-me-in-.env"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    # Demo mode is automatic: if the required provider keys aren't set,
    # we never pretend to have real data (see section 37 / 22 of the spec).
    settings.DEMO_MODE = not bool(settings.ETHERSCAN_API_KEY)
    return settings
