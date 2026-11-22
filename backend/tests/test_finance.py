from __future__ import annotations

from decimal import Decimal

from app.schemas.audit import ExtractedCharge
from app.services.finance import build_audit_report, to_monthly_equivalent


def test_monthly_equivalent_conversions() -> None:
    assert to_monthly_equivalent(Decimal("120.00"), "annual") == Decimal("10.00")
    assert to_monthly_equivalent(Decimal("30.00"), "quarterly") == Decimal("10.00")
    assert to_monthly_equivalent(Decimal("12.00"), "weekly") == Decimal("52.00")
    assert to_monthly_equivalent(Decimal("15.99"), "monthly") == Decimal("15.99")


def test_price_creep_and_category_overlap_detection() -> None:
    charges = [
        # Price creep on Netflix: $15.49 -> $17.99
        ExtractedCharge(
            merchant="Netflix",
            amount=15.49,
            currency="USD",
            billing_frequency="monthly",
            category="Entertainment",
            billed_date="2026-03-10",
            is_recurring=True,
        ),
        ExtractedCharge(
            merchant="Netflix",
            amount=17.99,
            currency="USD",
            billing_frequency="monthly",
            category="Entertainment",
            billed_date="2026-10-10",
            is_recurring=True,
        ),
        # Overlapping Cloud Storage subscriptions
        ExtractedCharge(
            merchant="Dropbox Plus",
            amount=119.88,
            currency="USD",
            billing_frequency="annual",
            category="Cloud Storage",
            billed_date="2026-05-01",
            is_recurring=True,
        ),
        ExtractedCharge(
            merchant="Apple iCloud+",
            amount=9.99,
            currency="USD",
            billing_frequency="monthly",
            category="Cloud Storage",
            billed_date="2026-11-01",
            is_recurring=True,
        ),
        # Variable utility should NOT be flagged as subscription price creep
        ExtractedCharge(
            merchant="PG&E",
            amount=95.00,
            currency="USD",
            billing_frequency="monthly",
            category="Utilities",
            billed_date="2026-08-20",
            is_recurring=True,
        ),
        ExtractedCharge(
            merchant="PG&E",
            amount=122.00,
            currency="USD",
            billing_frequency="monthly",
            category="Utilities",
            billed_date="2026-10-20",
            is_recurring=True,
        ),
        # One-off order should be ignored completely
        ExtractedCharge(
            merchant="DoorDash",
            amount=34.50,
            currency="USD",
            billing_frequency="one_time",
            category="Other",
            billed_date="2026-11-02",
            is_recurring=False,
        ),
    ]

    report = build_audit_report(
        provider="gmail",
        scanned_emails_count=42,
        charges=charges,
    )

    assert report.scanned_emails_count == 42
    # 17.99 + (119.88 / 12 = 9.99) + 9.99 + 122.00 = 159.97
    assert report.total_monthly_recurring == 159.97
    assert report.total_annual_recurring == 1919.64
    assert len(report.items) == 4

    by_merchant = {item.merchant: item for item in report.items}
    assert "price_creep" in by_merchant["Netflix"].flags
    assert by_merchant["Netflix"].price_change_amount == 2.5
    assert "duplicate_category" in by_merchant["Dropbox Plus"].flags
    assert "duplicate_category" in by_merchant["Apple iCloud+"].flags
    assert by_merchant["PG&E"].flags == []

