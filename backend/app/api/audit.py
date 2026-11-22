from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.schemas.audit import AuditRequest, AuditResponse
from app.services.extractor import extract_recurring_charges
from app.services.finance import build_audit_report
from app.services.gmail import fetch_gmail_billing_emails
from app.services.pii import sanitize_email_snippets

router = APIRouter(prefix="/api", tags=["audit"])


@router.post("/audit", response_model=AuditResponse)
async def run_audit(payload: AuditRequest) -> AuditResponse:
    settings = get_settings()

    if payload.provider == "outlook":
        raise HTTPException(
            status_code=501,
            detail="Outlook auditing is not wired yet. Connect Gmail for now.",
        )

    emails = await fetch_gmail_billing_emails(
        access_token=payload.access_token,
        lookback_days=settings.audit_lookback_days,
        max_emails=settings.audit_max_emails,
    )
    emails = sanitize_email_snippets(emails)

    charges = await extract_recurring_charges(
        emails=emails,
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
    )

    report = build_audit_report(
        provider=payload.provider,
        scanned_emails_count=len(emails),
        charges=charges,
        annual_return_rate=settings.annual_return_rate,
    )

    return report

