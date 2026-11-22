from __future__ import annotations

import asyncio
import base64
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any, Dict, List, Optional

import httpx
from bs4 import BeautifulSoup
from fastapi import HTTPException

from app.schemas.audit import EmailSnippet

GMAIL_BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"
MAX_BODY_CHARS = 1200
CONCURRENT_FETCH_LIMIT = 15


def _build_gmail_query(lookback_days: int) -> str:
    return (
        '(subscription OR renewal OR membership OR recurring OR invoice OR '
        f'statement OR receipt) newer_than:{lookback_days}d '
        "-category:promotions -category:social"
    )


def _decode_base64url(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    raw_bytes = base64.urlsafe_b64decode(padded.encode("ascii"))
    return raw_bytes.decode("utf-8", errors="replace")


def _html_to_clean_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "head", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return re.sub(r"\s+", " ", text).strip()


def _extract_mime_body(payload: Dict[str, Any]) -> str:
    mime_type = payload.get("mimeType", "")
    body_data = (payload.get("body") or {}).get("data")

    if mime_type == "text/plain" and body_data:
        return re.sub(r"\s+", " ", _decode_base64url(body_data)).strip()

    parts = payload.get("parts") or []
    plain_chunks: List[str] = []
    html_chunks: List[str] = []

    for part in parts:
        part_mime = part.get("mimeType", "")
        part_data = (part.get("body") or {}).get("data")
        if part_mime == "text/plain" and part_data:
            plain_chunks.append(_decode_base64url(part_data))
        elif part_mime == "text/html" and part_data:
            html_chunks.append(_decode_base64url(part_data))
        elif part.get("parts"):
            nested = _extract_mime_body(part)
            if nested:
                plain_chunks.append(nested)

    if plain_chunks:
        joined = " ".join(plain_chunks)
        return re.sub(r"\s+", " ", joined).strip()

    if html_chunks:
        return _html_to_clean_text(" ".join(html_chunks))

    if mime_type == "text/html" and body_data:
        return _html_to_clean_text(_decode_base64url(body_data))

    return ""


def _parse_message_date(
    headers: Dict[str, str], internal_date_ms: Optional[str]
) -> str:
    raw_date = headers.get("date")
    if raw_date:
        try:
            dt = parsedate_to_datetime(raw_date)
            return dt.date().isoformat()
        except (TypeError, ValueError):
            pass

    if internal_date_ms and internal_date_ms.isdigit():
        ts = int(internal_date_ms) / 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()

    return datetime.now(tz=timezone.utc).date().isoformat()


async def _fetch_single_message(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    message_id: str,
) -> Optional[EmailSnippet]:
    async with semaphore:
        resp = await client.get(
            f"{GMAIL_BASE_URL}/messages/{message_id}",
            params={"format": "full"},
        )
        if resp.status_code != 200:
            return None

        msg = resp.json()
        payload = msg.get("payload") or {}
        raw_headers = payload.get("headers") or []
        headers = {
            h.get("name", "").lower(): h.get("value", "")
            for h in raw_headers
            if h.get("name")
        }

        subject = headers.get("subject", "").strip()
        sender = headers.get("from", "").strip()
        billed_date = _parse_message_date(headers, msg.get("internalDate"))

        body_text = _extract_mime_body(payload)
        if not body_text:
            body_text = (msg.get("snippet") or "").strip()

        if not subject and not body_text:
            return None

        return EmailSnippet(
            message_id=message_id,
            billed_date=billed_date,
            sender=sender[:140],
            subject=subject[:200],
            body_text=body_text[:MAX_BODY_CHARS],
        )


async def fetch_gmail_billing_emails(
    access_token: str,
    lookback_days: int = 365,
    max_emails: int = 200,
) -> List[EmailSnippet]:
    headers = {"Authorization": f"Bearer {access_token}"}
    query = _build_gmail_query(lookback_days)
    message_ids: List[str] = []
    page_token: Optional[str] = None

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        while len(message_ids) < max_emails:
            batch_size = min(100, max_emails - len(message_ids))
            params: Dict[str, Any] = {"q": query, "maxResults": batch_size}
            if page_token:
                params["pageToken"] = page_token

            list_resp = await client.get(f"{GMAIL_BASE_URL}/messages", params=params)

            if list_resp.status_code == 401:
                raise HTTPException(
                    status_code=401,
                    detail="Gmail access token expired or is invalid. Please reconnect Gmail.",
                )
            if list_resp.status_code == 403:
                raise HTTPException(
                    status_code=403,
                    detail=(
                        "Gmail read-only access was denied, or the Gmail API is not "
                        "enabled on your Google Cloud project."
                    ),
                )
            if list_resp.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"Gmail API returned HTTP {list_resp.status_code}.",
                )

            data = list_resp.json()
            for item in data.get("messages") or []:
                if item.get("id"):
                    message_ids.append(item["id"])

            page_token = data.get("nextPageToken")
            if not page_token or not data.get("messages"):
                break

        if not message_ids:
            return []

        semaphore = asyncio.Semaphore(CONCURRENT_FETCH_LIMIT)
        tasks = [
            _fetch_single_message(client, semaphore, msg_id)
            for msg_id in message_ids[:max_emails]
        ]
        results = await asyncio.gather(*tasks)

    return [snippet for snippet in results if snippet is not None]

