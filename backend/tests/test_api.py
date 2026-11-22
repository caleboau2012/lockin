from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.audit import EmailSnippet, ExtractedCharge


def test_health_endpoint() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_audit_pipeline_endpoint(monkeypatch) -> None:
    async def fake_fetch_gmail(access_token: str, lookback_days: int, max_emails: int):
        assert access_token == "test-oauth-token"
        assert lookback_days == 365
        assert max_emails == 200
        return [
            EmailSnippet(
                message_id="m1",
                billed_date="2026-11-01",
                sender="billing@spotify.com",
                subject="Your Spotify receipt",
                body_text="Spotify Individual $11.99 monthly",
            )
        ]

    async def fake_extract(emails, api_key: str, model: str):
        assert len(emails) == 1
        return [
            ExtractedCharge(
                merchant="Spotify",
                amount=11.99,
                currency="USD",
                billing_frequency="monthly",
                category="Music & Audio",
                billed_date="2026-11-01",
                is_recurring=True,
            )
        ]

    monkeypatch.setattr("app.api.audit.fetch_gmail_billing_emails", fake_fetch_gmail)
    monkeypatch.setattr("app.api.audit.extract_recurring_charges", fake_extract)

    client = TestClient(app)
    resp = client.post(
        "/api/audit",
        json={"provider": "gmail", "access_token": "test-oauth-token"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["scanned_emails_count"] == 1
    assert body["total_monthly_recurring"] == 11.99
    assert body["items"][0]["merchant"] == "Spotify"

