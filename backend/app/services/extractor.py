from __future__ import annotations

from typing import Any, Dict, List

import httpx
from fastapi import HTTPException

from app.schemas.audit import (
    EmailSnippet,
    ExtractedCharge,
    ExtractedChargeBatch,
)

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)

FALLBACK_FLASH_MODELS = [
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.8-flash",
    "gemini-3.1-flash-lite",
]

RESPONSE_SCHEMA: Dict[str, Any] = {
    "type": "OBJECT",
    "properties": {
        "charges": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "merchant": {
                        "type": "STRING",
                        "description": (
                            "Clean canonical merchant/service name, e.g. 'Netflix', "
                            "'Apple iCloud+', 'Dropbox', 'Spotify', 'PG&E'."
                        ),
                    },
                    "amount": {
                        "type": "NUMBER",
                        "description": "Total billed charge amount (> 0).",
                    },
                    "currency": {
                        "type": "STRING",
                        "description": "3-letter ISO currency code such as 'USD'.",
                    },
                    "billing_frequency": {
                        "type": "STRING",
                        "enum": [
                            "monthly",
                            "annual",
                            "quarterly",
                            "weekly",
                            "one_time",
                        ],
                    },
                    "category": {
                        "type": "STRING",
                        "enum": [
                            "Entertainment",
                            "Music & Audio",
                            "Cloud Storage",
                            "Software & AI",
                            "Fitness & Health",
                            "News & Media",
                            "Memberships",
                            "Utilities",
                            "Telecom & Internet",
                            "Insurance",
                            "Other",
                        ],
                    },
                    "billed_date": {
                        "type": "STRING",
                        "description": "Billing date formatted as YYYY-MM-DD.",
                    },
                    "is_recurring": {
                        "type": "BOOLEAN",
                        "description": (
                            "True only for recurring subscriptions, memberships, "
                            "plan renewals, or recurring utility/telecom bills."
                        ),
                    },
                },
                "required": [
                    "merchant",
                    "amount",
                    "currency",
                    "billing_frequency",
                    "category",
                    "billed_date",
                    "is_recurring",
                ],
            },
        }
    },
    "required": ["charges"],
}

SYSTEM_INSTRUCTIONS = """You extract billed charges from email receipts, invoices, and billing statements.

Rules:
1. Extract ONLY confirmed billed charges with a positive dollar amount (> 0).
2. Ignore marketing promotions, $0 free trial signups, shipping/delivery updates, credit card payment transfers, bank balance alerts, and cancellation confirmations without a charge.
3. Mark is_recurring=true ONLY for subscriptions, memberships, SaaS plans, cloud storage, media plans, insurance, or recurring utility/telecom bills. Mark one-off retail, rideshare, flight, or food delivery purchases as is_recurring=false and billing_frequency="one_time".
4. Keep merchant names canonical and consistent across months (e.g., always use 'Netflix' instead of 'NETFLIX.COM', and distinguish distinct Apple services like 'Apple iCloud+' vs 'Apple TV+').
5. If an email represents the exact same charge twice (e.g., an upcoming renewal reminder AND the receipt for the same date), include only the actual billed charge once.
6. Use the email's Date (YYYY-MM-DD) when the body does not state a more specific billing date.
"""


def _format_emails_prompt(emails: List[EmailSnippet]) -> str:
    blocks = []
    for idx, email in enumerate(emails, start=1):
        blocks.append(
            f"[{idx}] Date: {email.billed_date}\n"
            f"From: {email.sender}\n"
            f"Subject: {email.subject}\n"
            f"Body: {email.body_text}"
        )
    return "Extract recurring and billed charges from these emails:\n\n" + "\n\n---\n\n".join(
        blocks
    )


def _extract_upstream_message(resp: httpx.Response) -> str:
    if not resp.content:
        return ""
    try:
        err_json = resp.json()
        return (err_json.get("error") or {}).get("message", "")
    except ValueError:
        return ""


async def extract_recurring_charges(
    emails: List[EmailSnippet],
    api_key: str,
    model: str = "gemini-3.5-flash",
) -> List[ExtractedCharge]:
    if not emails:
        return []

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="Missing GEMINI_API_KEY in root .env.",
        )

    candidate_models = [model] + [
        m for m in FALLBACK_FLASH_MODELS if m != model
    ]

    payload: Dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": SYSTEM_INSTRUCTIONS}]},
        "contents": [
            {
                "role": "user",
                "parts": [{"text": _format_emails_prompt(emails)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.0,
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
        },
    }

    resp: httpx.Response | None = None
    async with httpx.AsyncClient(timeout=90.0) as client:
        for candidate in candidate_models:
            url = GEMINI_API_URL.format(model=candidate)
            resp = await client.post(
                url,
                headers={
                    "x-goog-api-key": api_key,
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            # Retry next Flash model if deprecated (404) or temporarily overloaded (503)
            if resp.status_code in (404, 503):
                continue
            break

    assert resp is not None

    if resp.status_code == 429:
        raise HTTPException(
            status_code=429,
            detail=(
                "Gemini Free Tier rate limit reached. Wait about a minute and try again."
            ),
        )
    if resp.status_code != 200:
        api_msg = _extract_upstream_message(resp)
        detail_suffix = f": {api_msg}" if api_msg else "."
        raise HTTPException(
            status_code=502,
            detail=f"Gemini API returned HTTP {resp.status_code}{detail_suffix}",
        )

    body = resp.json()
    candidates = body.get("candidates") or []
    if not candidates:
        return []

    parts = ((candidates[0].get("content") or {}).get("parts")) or []
    text_parts = [
        p.get("text", "")
        for p in parts
        if not p.get("thought") and p.get("text")
    ]
    raw_json = text_parts[-1] if text_parts else ""
    if not raw_json:
        return []

    parsed = ExtractedChargeBatch.model_validate_json(raw_json)
    return parsed.charges
