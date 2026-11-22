from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.audit import router as audit_router
from app.config import get_settings

logger = logging.getLogger("lockin")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="LockIn API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url=None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    @app.exception_handler(Exception)
    async def sanitized_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        # Never log request payloads, tokens, or email contents
        logger.error(
            "Unhandled %s on %s %s",
            exc.__class__.__name__,
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error while processing audit."},
        )

    @app.get("/health")
    async def health_check() -> dict:
        return {"status": "ok"}

    app.include_router(audit_router)
    return app


app = create_app()

