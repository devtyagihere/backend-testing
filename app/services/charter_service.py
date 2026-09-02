"""
Charter Inquiry Service
Handles: database saves via Supabase REST API (with local resilient ledger backup), email dispatch via Resend.
All API keys are server-side only — never exposed to frontend.
"""
import os
import json
import httpx
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

LOCAL_STORAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "charter_inquiries.json")


def _ensure_local_storage():
    os.makedirs(os.path.dirname(LOCAL_STORAGE_PATH), exist_ok=True)
    if not os.path.exists(LOCAL_STORAGE_PATH):
        with open(LOCAL_STORAGE_PATH, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)


def _save_local_inquiry(inquiry: dict):
    _ensure_local_storage()
    try:
        with open(LOCAL_STORAGE_PATH, "r+", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except Exception:
                data = []
            data.insert(0, inquiry)
            f.seek(0)
            json.dump(data, f, indent=2)
            f.truncate()
    except Exception as e:
        logger.error("Error writing to local backup ledger: %s", str(e))


def _get_local_inquiries() -> List[dict]:
    _ensure_local_storage()
    try:
        with open(LOCAL_STORAGE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _update_local_status(inquiry_id: str, new_status: str) -> bool:
    _ensure_local_storage()
    try:
        with open(LOCAL_STORAGE_PATH, "r+", encoding="utf-8") as f:
            data = json.load(f)
            found = False
            for item in data:
                if item.get("inquiry_id") == inquiry_id:
                    item["status"] = new_status
                    item["updated_at"] = datetime.now(timezone.utc).isoformat()
                    found = True
                    break
            if found:
                f.seek(0)
                json.dump(data, f, indent=2)
                f.truncate()
            return found
    except Exception as e:
        logger.error("Error updating local ledger: %s", str(e))
        return False


def _supabase_headers(use_service_key: bool = False) -> dict:
    """Build Supabase REST API auth headers."""
    key = settings.SUPABASE_SERVICE_KEY if (use_service_key and settings.SUPABASE_SERVICE_KEY) else settings.SUPABASE_PUBLISHABLE_KEY
    return {
        "apikey": key or "",
        "Authorization": f"Bearer {key or ''}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }


def _generate_inquiry_id() -> str:
    """Generate human-readable inquiry ID: FW-2026-XXXXXX"""
    import random, string
    suffix = ''.join(random.choices(string.digits, k=6))
    year = datetime.now(timezone.utc).year
    return f"FW-{year}-{suffix}"


def save_inquiry_to_supabase(data: dict) -> dict:
    """Insert charter inquiry into Supabase charter_inquiries table & local ledger."""
    inquiry_id = _generate_inquiry_id()
    created_at = datetime.now(timezone.utc).isoformat()

    payload = {
        "inquiry_id": inquiry_id,
        "first_name": data["first_name"],
        "last_name": data["last_name"],
        "email": data["email"],
        "commodity": data["commodity"],
        "parcel_mt": float(data["parcel_mt"]),
        "load_port": data["load_port"],
        "discharge_port": data["discharge_port"],
        "voyage_notes": data.get("voyage_notes", "") or "",
        "status": "PENDING",
        "created_at": created_at,
    }

    # Always persist locally first so data is never lost
    _save_local_inquiry(payload)

    # If Supabase URL is configured, also post to Supabase
    if settings.SUPABASE_URL and not "YOUR_PROJECT_ID" in settings.SUPABASE_URL and settings.SUPABASE_PUBLISHABLE_KEY:
        try:
            url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/charter_inquiries"
            resp = httpx.post(url, json=payload, headers=_supabase_headers(use_service_key=False), timeout=10)
            if resp.status_code in (200, 201):
                rows = resp.json()
                saved = rows[0] if isinstance(rows, list) and len(rows) > 0 else payload
                saved["inquiry_id"] = inquiry_id
                return saved
            else:
                logger.warning("Supabase returned %s: %s. Using local persistent ledger.", resp.status_code, resp.text)
        except Exception as e:
            logger.warning("Supabase connection error: %s. Saved in resilient local ledger.", str(e))

    return payload


def get_all_inquiries_from_supabase() -> list:
    """Fetch all charter inquiries (admin only). Tries Supabase, falls back to local ledger."""
    if settings.SUPABASE_URL and not "YOUR_PROJECT_ID" in settings.SUPABASE_URL:
        try:
            url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/charter_inquiries?order=created_at.desc"
            resp = httpx.get(url, headers=_supabase_headers(use_service_key=True), timeout=10)
            if resp.status_code == 200:
                return resp.json()
        except Exception as e:
            logger.warning("Supabase fetch failed: %s. Falling back to local ledger.", str(e))

    return _get_local_inquiries()


def update_inquiry_status(inquiry_id: str, new_status: str) -> dict:
    """Update charter inquiry status across Supabase & local ledger."""
    # Update local ledger
    _update_local_status(inquiry_id, new_status)

    # Update Supabase if configured
    if settings.SUPABASE_URL and not "YOUR_PROJECT_ID" in settings.SUPABASE_URL:
        try:
            url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/charter_inquiries?inquiry_id=eq.{inquiry_id}"
            httpx.patch(
                url,
                json={"status": new_status},
                headers=_supabase_headers(use_service_key=True),
                timeout=10
            )
        except Exception as e:
            logger.warning("Supabase status update exception: %s", str(e))

    return {"ok": True, "inquiry_id": inquiry_id, "new_status": new_status}


def send_owner_notification(inquiry: dict) -> bool:
    """Send new inquiry alert email to owner via Resend."""
    if not settings.RESEND_API_KEY or not settings.OWNER_EMAIL:
        logger.warning("Resend not configured. Skipping owner email.")
        return False

    submitted_at = inquiry.get("created_at", datetime.now(timezone.utc).isoformat())

    html_body = f"""
    <div style="font-family: 'Inter', Arial, sans-serif; background: #080808; color: #ffffff; padding: 32px; border-radius: 12px;">
      <div style="max-width: 600px; margin: 0 auto; background: #121418; border: 1px solid rgba(255,255,255,0.1); border-left: 4px solid #00a8ff; border-radius: 12px; padding: 32px;">
        <h2 style="color: #00a8ff; font-size: 14px; letter-spacing: 2px; text-transform: uppercase; margin: 0 0 4px;">FREIGHTWAVES</h2>
        <h1 style="color: #ffffff; font-size: 22px; margin: 0 0 24px;">New Charter Inquiry Received</h1>

        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
          <tr><td style="padding: 10px 0; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.06); width: 40%;">Inquiry ID</td>
              <td style="padding: 10px 0; color: #ffffff; font-weight: 700; border-bottom: 1px solid rgba(255,255,255,0.06); font-family: monospace;">{inquiry.get('inquiry_id')}</td></tr>
          <tr><td style="padding: 10px 0; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.06);">Customer Name</td>
              <td style="padding: 10px 0; color: #ffffff; border-bottom: 1px solid rgba(255,255,255,0.06);">{inquiry.get('first_name')} {inquiry.get('last_name')}</td></tr>
          <tr><td style="padding: 10px 0; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.06);">Corporate Email</td>
              <td style="padding: 10px 0; color: #00a8ff; border-bottom: 1px solid rgba(255,255,255,0.06);">{inquiry.get('email')}</td></tr>
          <tr><td style="padding: 10px 0; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.06);">Cargo Commodity</td>
              <td style="padding: 10px 0; color: #ffffff; border-bottom: 1px solid rgba(255,255,255,0.06);">{inquiry.get('commodity')}</td></tr>
          <tr><td style="padding: 10px 0; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.06);">Parcel</td>
              <td style="padding: 10px 0; color: #ffffff; border-bottom: 1px solid rgba(255,255,255,0.06); font-weight: bold;">{inquiry.get('parcel_mt')} MT</td></tr>
          <tr><td style="padding: 10px 0; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.06);">Load Port</td>
              <td style="padding: 10px 0; color: #ffffff; border-bottom: 1px solid rgba(255,255,255,0.06);">{inquiry.get('load_port')}</td></tr>
          <tr><td style="padding: 10px 0; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.06);">Discharge Port</td>
              <td style="padding: 10px 0; color: #ffffff; border-bottom: 1px solid rgba(255,255,255,0.06);">{inquiry.get('discharge_port')}</td></tr>
          <tr><td style="padding: 10px 0; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.06);">Voyage Notes / Laycan</td>
              <td style="padding: 10px 0; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.06);">{inquiry.get('voyage_notes') or '—'}</td></tr>
          <tr><td style="padding: 10px 0; color: #94a3b8; border-bottom: 1px solid rgba(255,255,255,0.06);">Status</td>
              <td style="padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.06);"><span style="background: rgba(0,168,255,0.15); color: #00a8ff; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 700;">PENDING</span></td></tr>
          <tr><td style="padding: 10px 0; color: #94a3b8;">Submitted At</td>
              <td style="padding: 10px 0; color: #ffffff;">{submitted_at}</td></tr>
        </table>

        <div style="margin-top: 24px; padding: 16px; background: rgba(0,168,255,0.05); border: 1px solid rgba(0,168,255,0.2); border-radius: 8px;">
          <p style="margin: 0; font-size: 12px; color: #94a3b8;">Manage this inquiry in the Admin Cockpit at <strong style="color: #00a8ff;">http://localhost:8000/admin</strong></p>
        </div>
      </div>
    </div>
    """

    payload = {
        "from": "FreightWaves <onboarding@resend.dev>",
        "to": [settings.OWNER_EMAIL],
        "subject": f"New Charter Inquiry - {inquiry.get('inquiry_id')}",
        "html": html_body,
    }

    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=15
        )
        if resp.status_code in (200, 201):
            logger.info("Owner notification email sent for %s", inquiry.get('inquiry_id'))
            return True
        else:
            logger.error("Resend owner email failed: %s — %s", resp.status_code, resp.text)
            return False
    except Exception as e:
        logger.error("Resend owner email exception: %s", str(e))
        return False


def send_customer_confirmation(inquiry: dict) -> bool:
    """Send confirmation email to the customer via Resend."""
    if not settings.RESEND_API_KEY:
        logger.warning("Resend not configured. Skipping customer confirmation.")
        return False

    first_name = inquiry.get("first_name", "Valued Customer")
    inquiry_id = inquiry.get("inquiry_id")

    html_body = f"""
    <div style="font-family: 'Inter', Arial, sans-serif; background: #080808; color: #ffffff; padding: 32px; border-radius: 12px;">
      <div style="max-width: 600px; margin: 0 auto; background: #121418; border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 32px;">

        <div style="margin-bottom: 24px;">
          <h2 style="color: #00a8ff; font-size: 13px; letter-spacing: 3px; text-transform: uppercase; margin: 0 0 4px;">FREIGHTWAVES</h2>
          <p style="color: #64748b; font-size: 11px; margin: 0; font-family: monospace;">Chartering & Bulk Vessel Operations</p>
        </div>

        <h1 style="color: #ffffff; font-size: 20px; margin: 0 0 8px;">Hello {first_name},</h1>
        <p style="color: #94a3b8; font-size: 14px; line-height: 1.7; margin: 0 0 24px;">
          Your charter inquiry has been successfully received by the FreightWaves Chartering Team.
        </p>

        <div style="background: rgba(0,168,255,0.08); border: 1px solid rgba(0,168,255,0.3); border-radius: 10px; padding: 20px; text-align: center; margin-bottom: 24px;">
          <p style="color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; margin: 0 0 6px; font-family: monospace;">Your Inquiry Reference ID</p>
          <p style="color: #00a8ff; font-size: 26px; font-weight: 800; margin: 0; font-family: monospace; letter-spacing: 4px;">{inquiry_id}</p>
        </div>

        <p style="color: #94a3b8; font-size: 13px; line-height: 1.7; margin: 0 0 8px;">
          Our team will review your cargo and voyage requirements. We aim to respond within <strong style="color: #ffffff;">2 hours</strong>.
        </p>
        <p style="color: #94a3b8; font-size: 13px; margin: 0 0 24px;">
          Thank you for using FreightWaves.
        </p>

        <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 20px;">
          <p style="color: #64748b; font-size: 12px; margin: 0;">Regards,</p>
          <p style="color: #ffffff; font-size: 13px; font-weight: 700; margin: 4px 0 0;">FreightWaves</p>
          <p style="color: #64748b; font-size: 11px; margin: 2px 0 0; font-family: monospace;">Chartering Team</p>
        </div>
      </div>
    </div>
    """

    payload = {
        "from": "FreightWaves <onboarding@resend.dev>",
        "to": [inquiry.get("email")],
        "subject": "We Received Your Charter Inquiry | FreightWaves",
        "html": html_body,
    }

    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={"Authorization": f"Bearer {settings.RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=15
        )
        if resp.status_code in (200, 201):
            logger.info("Customer confirmation email sent to %s", inquiry.get("email"))
            return True
        else:
            logger.error("Resend customer email failed: %s — %s", resp.status_code, resp.text)
            return False
    except Exception as e:
        logger.error("Resend customer email exception: %s", str(e))
        return False
