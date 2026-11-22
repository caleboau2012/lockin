from __future__ import annotations

from app.schemas.audit import EmailSnippet
from app.services.pii import redact_text, sanitize_email_snippets


def test_redacts_emails_and_phones_without_touching_dates_or_amounts() -> None:
    raw = (
        "Receipt for jane.doe+bills@gmail.com on 2026-11-08. "
        "Billed $17.99 and $1,234.56. Questions? Call (415) 555-0199 or +1-800-555-1234."
    )
    cleaned = redact_text(raw)

    assert "jane.doe" not in cleaned
    assert "[REDACTED_EMAIL]" in cleaned
    assert "415" not in cleaned
    assert "800-555-1234" not in cleaned
    assert cleaned.count("[REDACTED_PHONE]") == 2
    # Financial & date fields remain completely intact
    assert "2026-11-08" in cleaned
    assert "$17.99" in cleaned
    assert "$1,234.56" in cleaned


def test_sanitize_email_snippets_preserves_merchant_sender_domain() -> None:
    snippets = [
        EmailSnippet(
            message_id="m1",
            billed_date="2026-11-01",
            sender="Netflix <info@account.netflix.com>",
            subject="Receipt for alex@yahoo.com",
            body_text="Netflix Standard $17.99/mo · Support: 408.555.9876",
        )
    ]
    sanitized = sanitize_email_snippets(snippets)
    assert sanitized[0].sender == "Netflix <*@account.netflix.com>"
    assert sanitized[0].subject == "Receipt for [REDACTED_EMAIL]"
    assert sanitized[0].body_text == "Netflix Standard $17.99/mo · Support: [REDACTED_PHONE]"

