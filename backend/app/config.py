from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

ROOT_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ROOT_ENV_PATH)


@dataclass(frozen=True)
class Settings:
    gemini_api_key: str
    gemini_model: str
    audit_lookback_days: int
    audit_max_emails: int
    annual_return_rate: float
    allowed_origins: List[str]


def get_settings() -> Settings:
    raw_origins = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    )
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]

    return Settings(
        gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash").strip(),
        audit_lookback_days=int(os.getenv("AUDIT_LOOKBACK_DAYS", "365")),
        audit_max_emails=int(os.getenv("AUDIT_MAX_EMAILS", "200")),
        annual_return_rate=float(os.getenv("ANNUAL_RETURN_RATE", "0.07")),
        allowed_origins=origins,
    )

