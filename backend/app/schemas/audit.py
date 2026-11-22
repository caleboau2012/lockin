from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

OAuthProvider = Literal["gmail", "outlook"]
BillingFrequency = Literal["monthly", "annual", "quarterly", "weekly", "one_time"]
ItemFlag = Literal["price_creep", "duplicate_category"]


class AuditRequest(BaseModel):
    provider: OAuthProvider
    access_token: str = Field(..., min_length=1)


class EmailSnippet(BaseModel):
    message_id: str
    billed_date: str
    sender: str
    subject: str
    body_text: str


class ExtractedCharge(BaseModel):
    merchant: str
    amount: float
    currency: str = "USD"
    billing_frequency: BillingFrequency
    category: str
    billed_date: str
    is_recurring: bool


class ExtractedChargeBatch(BaseModel):
    charges: List[ExtractedCharge] = Field(default_factory=list)


class AuditAlert(BaseModel):
    type: ItemFlag
    message: str


class RecurringItem(BaseModel):
    id: str
    merchant: str
    category: str
    billing_frequency: BillingFrequency
    latest_amount: float
    monthly_equivalent: float
    previous_amount: Optional[float] = None
    price_change_amount: Optional[float] = None
    last_billed_date: str
    flags: List[ItemFlag] = Field(default_factory=list)
    default_selected: bool = False


class AuditResponse(BaseModel):
    provider: OAuthProvider
    scanned_emails_count: int
    annual_return_rate: float
    total_monthly_recurring: float
    total_annual_recurring: float
    alerts: List[AuditAlert] = Field(default_factory=list)
    items: List[RecurringItem] = Field(default_factory=list)

