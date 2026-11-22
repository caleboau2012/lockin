from __future__ import annotations

import re
from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Tuple

from app.schemas.audit import (
    AuditAlert,
    AuditResponse,
    BillingFrequency,
    ExtractedCharge,
    ItemFlag,
    OAuthProvider,
    RecurringItem,
)

CENTS = Decimal("0.01")
PRICE_CREEP_MIN_DELTA = Decimal("0.50")

# Metered/essential categories where multiple providers or usage swings are normal
NON_OVERLAP_CATEGORIES = {
    "Utilities",
    "Telecom & Internet",
    "Insurance",
    "Other",
}
METERED_CATEGORIES = {"Utilities"}


def _to_decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)


def _normalize_merchant_key(merchant: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", merchant.lower()).strip()
    return cleaned or merchant.strip().lower()


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "item"


def to_monthly_equivalent(amount: Decimal, frequency: BillingFrequency) -> Decimal:
    if frequency == "monthly":
        monthly = amount
    elif frequency == "annual":
        monthly = amount / Decimal("12")
    elif frequency == "quarterly":
        monthly = amount / Decimal("3")
    elif frequency == "weekly":
        monthly = (amount * Decimal("52")) / Decimal("12")
    else:
        monthly = Decimal("0.00")
    return monthly.quantize(CENTS, rounding=ROUND_HALF_UP)


def _dedupe_same_day_charges(charges: List[ExtractedCharge]) -> List[ExtractedCharge]:
    seen = set()
    unique: List[ExtractedCharge] = []
    for ch in sorted(charges, key=lambda c: c.billed_date):
        key = (ch.billed_date, _to_decimal(ch.amount), ch.billing_frequency)
        if key not in seen:
            seen.add(key)
            unique.append(ch)
    return unique


def build_audit_report(
    provider: OAuthProvider,
    scanned_emails_count: int,
    charges: List[ExtractedCharge],
    annual_return_rate: float = 0.07,
) -> AuditResponse:
    grouped: Dict[str, List[ExtractedCharge]] = defaultdict(list)

    for charge in charges:
        if not charge.is_recurring or charge.billing_frequency == "one_time":
            continue
        if charge.amount <= 0:
            continue
        if charge.currency and charge.currency.upper() != "USD":
            continue
        grouped[_normalize_merchant_key(charge.merchant)].append(charge)

    draft_items: List[RecurringItem] = []
    alerts: List[AuditAlert] = []
    price_creep_alerts: List[Tuple[Decimal, AuditAlert]] = []

    for merchant_key, raw_group in grouped.items():
        history = _dedupe_same_day_charges(raw_group)
        latest = history[-1]
        latest_dec = _to_decimal(latest.amount)
        monthly_dec = to_monthly_equivalent(latest_dec, latest.billing_frequency)

        flags: List[ItemFlag] = []
        prev_amount_float = None
        delta_float = None

        if len(history) >= 2 and latest.category not in METERED_CATEGORIES:
            same_cycle_prior = [
                h for h in history[:-1] if h.billing_frequency == latest.billing_frequency
            ]
            if same_cycle_prior:
                baseline_dec = _to_decimal(same_cycle_prior[0].amount)
                delta_dec = (latest_dec - baseline_dec).quantize(
                    CENTS, rounding=ROUND_HALF_UP
                )
                if delta_dec >= PRICE_CREEP_MIN_DELTA:
                    flags.append("price_creep")
                    prev_amount_float = float(baseline_dec)
                    delta_float = float(delta_dec)
                    cycle_suffix = (
                        "mo"
                        if latest.billing_frequency == "monthly"
                        else latest.billing_frequency
                    )
                    price_creep_alerts.append(
                        (
                            delta_dec,
                            AuditAlert(
                                type="price_creep",
                                message=(
                                    f"{latest.merchant} rose from "
                                    f"${baseline_dec:.2f} to ${latest_dec:.2f}/{cycle_suffix} "
                                    f"(+${delta_dec:.2f})"
                                ),
                            ),
                        )
                    )

        draft_items.append(
            RecurringItem(
                id=f"sub-{_slugify(merchant_key)}",
                merchant=latest.merchant.strip(),
                category=latest.category,
                billing_frequency=latest.billing_frequency,
                latest_amount=float(latest_dec),
                monthly_equivalent=float(monthly_dec),
                previous_amount=prev_amount_float,
                price_change_amount=delta_float,
                last_billed_date=latest.billed_date,
                flags=flags,
                default_selected=bool(flags),
            )
        )

    # Detect category overlap across discretionary categories
    by_category: Dict[str, List[RecurringItem]] = defaultdict(list)
    for item in draft_items:
        if item.category not in NON_OVERLAP_CATEGORIES:
            by_category[item.category].append(item)

    overlap_alerts: List[AuditAlert] = []
    for category, cat_items in sorted(by_category.items()):
        if len(cat_items) >= 2:
            cat_sorted = sorted(cat_items, key=lambda x: x.monthly_equivalent)
            for idx, item in enumerate(cat_sorted):
                if "duplicate_category" not in item.flags:
                    item.flags.append("duplicate_category")
                # Pre-select the cheaper duplicate(s), keeping the primary one unchecked unless price-crept
                if idx < len(cat_sorted) - 1:
                    item.default_selected = True

            names = " + ".join(i.merchant for i in cat_items[:3])
            extra = f" +{len(cat_items) - 3} more" if len(cat_items) > 3 else ""
            overlap_alerts.append(
                AuditAlert(
                    type="duplicate_category",
                    message=(
                        f"{len(cat_items)} {category} subscriptions detected "
                        f"({names}{extra})"
                    ),
                )
            )

    price_creep_alerts.sort(key=lambda pair: pair[0], reverse=True)
    alerts.extend(alert for _, alert in price_creep_alerts)
    alerts.extend(overlap_alerts)

    # Sort flagged items first, then highest monthly cost descending
    draft_items.sort(
        key=lambda item: (len(item.flags) > 0, item.monthly_equivalent),
        reverse=True,
    )

    total_monthly_dec = sum(
        (_to_decimal(item.monthly_equivalent) for item in draft_items),
        Decimal("0.00"),
    ).quantize(CENTS, rounding=ROUND_HALF_UP)
    total_annual_dec = (total_monthly_dec * Decimal("12")).quantize(
        CENTS, rounding=ROUND_HALF_UP
    )

    return AuditResponse(
        provider=provider,
        scanned_emails_count=scanned_emails_count,
        annual_return_rate=annual_return_rate,
        total_monthly_recurring=float(total_monthly_dec),
        total_annual_recurring=float(total_annual_dec),
        alerts=alerts,
        items=draft_items,
    )

