"""
Structured application exceptions.

Every error the API returns should follow the same envelope:
{"error": "CODE", "message": "...", "retryable": bool}
so the frontend never has to guess how to handle a failure.
"""
from fastapi import Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    """Base class for all application-level errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    retryable: bool = False

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class InvalidAddressError(AppError):
    status_code = 422
    error_code = "INVALID_ADDRESS"
    retryable = False


class DataUnavailableError(AppError):
    status_code = 502
    error_code = "DATA_UNAVAILABLE"
    retryable = True


class ProviderRateLimitError(AppError):
    status_code = 429
    error_code = "PROVIDER_RATE_LIMITED"
    retryable = True


class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"
    retryable = False


class ProviderCapabilityError(AppError):
    """Raised when a provider is asked to do something its current tier/plan
    cannot do (e.g. Etherscan free tier has no collection-holder-list endpoint).
    Not retryable — retrying won't help until the provider or plan changes."""

    status_code = 501
    error_code = "PROVIDER_CAPABILITY_UNAVAILABLE"
    retryable = False


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "retryable": exc.retryable,
        },
    )
