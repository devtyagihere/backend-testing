"""
Charter Inquiry API Routes
- POST /api/v1/charter/submit   — public endpoint for form submission
- GET  /api/v1/charter/admin/inquiries  — protected admin view
- PATCH /api/v1/charter/admin/inquiries/{id}/status — update status
- GET /api/v1/charter/admin/ping  — verify admin token
"""
import re
import time
import secrets
import logging
from fastapi import APIRouter, HTTPException, Header, Request
from pydantic import BaseModel, field_validator
from typing import Optional
from app.services.charter_service import (
    save_inquiry_to_supabase,
    get_all_inquiries_from_supabase,
    update_inquiry_status,
    send_owner_notification,
    send_customer_confirmation
)
from app.core.config import settings

logger = logging.getLogger(__name__)
charter_router = APIRouter(prefix="/charter", tags=["Charter Inquiries"])

EMAIL_REGEX = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# --- Simple in-memory rate limiter (per IP, max 3 submissions per 5 min) ---
_submission_log: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 300  # 5 minutes
RATE_LIMIT_MAX = 5


def _check_rate_limit(ip: str):
    now = time.time()
    timestamps = [t for t in _submission_log.get(ip, []) if now - t < RATE_LIMIT_WINDOW]
    if len(timestamps) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail=f"Too many submissions. Please wait a few minutes before trying again."
        )
    timestamps.append(now)
    _submission_log[ip] = timestamps


# --- Valid statuses ---
VALID_STATUSES = {"PENDING", "UNDER REVIEW", "VESSEL MATCHING", "QUOTATION SENT", "ACCEPTED", "REJECTED"}


# --- Request / Response Schemas ---
class CharterInquiryRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    commodity: str
    parcel_mt: float
    load_port: str
    discharge_port: str
    voyage_notes: Optional[str] = ""

    @field_validator("first_name", "last_name", "commodity", "load_port", "discharge_port")
    @classmethod
    def not_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()

    @field_validator("email")
    @classmethod
    def valid_email(cls, v: str) -> str:
        if not v or not EMAIL_REGEX.match(v.strip()):
            raise ValueError("Corporate Email must be a valid email address")
        return v.strip().lower()

    @field_validator("parcel_mt")
    @classmethod
    def positive_parcel(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Parcel must be a positive number")
        return v


class StatusUpdateRequest(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: str) -> str:
        if v not in VALID_STATUSES:
            raise ValueError(f"Invalid status. Must be one of: {', '.join(VALID_STATUSES)}")
        return v


def _require_admin(x_admin_token: Optional[str]):
    """Validate admin secret token from request header using constant-time comparison."""
    if not x_admin_token or not secrets.compare_digest(x_admin_token, settings.ADMIN_SECRET_TOKEN):
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid or missing admin token.")


# ─── PUBLIC: Submit Charter Inquiry ───────────────────────────────────────────
@charter_router.post("/submit")
async def submit_charter_inquiry(request: Request, body: CharterInquiryRequest):
    """
    Public endpoint — validates form, saves to Supabase, sends both emails.
    """
    client_ip = request.client.host if request.client else "unknown"
    _check_rate_limit(client_ip)

    data = body.model_dump()

    # 1. Save to Supabase / persistent store
    try:
        saved_inquiry = save_inquiry_to_supabase(data)
    except RuntimeError as e:
        logger.error("Supabase save error: %s", str(e))
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error saving inquiry: %s", str(e))
        raise HTTPException(status_code=500, detail="Database error. Please try again.")

    # 2. Send owner notification
    owner_email_sent = False
    try:
        owner_email_sent = send_owner_notification(saved_inquiry)
    except Exception as e:
        logger.error("Owner email error (non-fatal): %s", str(e))

    # 3. Send customer confirmation
    customer_email_sent = False
    try:
        customer_email_sent = send_customer_confirmation(saved_inquiry)
    except Exception as e:
        logger.error("Customer email error (non-fatal): %s", str(e))

    return {
        "success": True,
        "inquiry_id": saved_inquiry["inquiry_id"],
        "status": "PENDING",
        "message": "Charter inquiry successfully received. Our team will respond within 2 hours.",
        "email_sent": {
            "owner_notification": owner_email_sent,
            "customer_confirmation": customer_email_sent,
        }
    }


# ─── ADMIN: Verify Token ──────────────────────────────────────────────────────
@charter_router.get("/admin/ping")
async def admin_ping(x_admin_token: Optional[str] = Header(default=None)):
    """Verify admin token is valid."""
    _require_admin(x_admin_token)
    return {"ok": True, "message": "Admin access verified."}


# ─── ADMIN: List All Inquiries ────────────────────────────────────────────────
@charter_router.get("/admin/inquiries")
async def list_all_inquiries(x_admin_token: Optional[str] = Header(default=None)):
    """Protected admin endpoint — returns all charter inquiries sorted newest first."""
    _require_admin(x_admin_token)
    try:
        inquiries = get_all_inquiries_from_supabase()
        return {"success": True, "count": len(inquiries), "inquiries": inquiries}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ─── ADMIN: Update Inquiry Status ────────────────────────────────────────────
@charter_router.patch("/admin/inquiries/{inquiry_id}/status")
async def update_status(
    inquiry_id: str,
    body: StatusUpdateRequest,
    x_admin_token: Optional[str] = Header(default=None)
):
    """Protected admin endpoint — update status of a charter inquiry."""
    _require_admin(x_admin_token)
    try:
        result = update_inquiry_status(inquiry_id, body.status)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
