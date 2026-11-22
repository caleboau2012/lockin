from __future__ import annotations

import re
from typing import List

from app.schemas.audit import EmailSnippet

EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"
)

# Matches standard 10-digit US / +country phone formats (e.g. (415) 555-0199, +1-800-555-1234)
# without touching YYYY-MM-DD dates, dollar amounts, or long numeric order IDs.
PHONE_PATTERN = re.compile(
    r"(?<!\d)(?:\+?\d{1,2}[\s.-]?)?(?:\(\d{3}\)|\b\d{3}\b)[\s.-]\d{3}[\s.-]\d{4}(?!\d)"
)


def redact_text(text: str) -> str:
    if not text:
        return text
    redacted = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    redacted = PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)
    return redacted


def redact_sender(sender: str) -> str:
    if not sender:
        return sender
    # Keep sender domain (e.g. *@netflix.com) so merchant context stays intact
    redacted = EMAIL_PATTERN.sub(r"*@\1", sender)
    return PHONE_PATTERN.sub("[REDACTED_PHONE]", redacted)


def sanitize_email_snippets(emails: List[EmailSnippet]) -> List[EmailSnippet]:
    return [
        EmailSnippet(
            message_id=email.message_id,
            billed_date=email.billed_date,
            sender=redact_sender(email.sender),
            subject=redact_text(email.subject),
            body_text=redact_text(email.body_text),
        )
        for email in emails
    ]

