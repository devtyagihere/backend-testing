import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)

def test_submit_invalid_form_validation_errors():
    """TEST 1: Submitting invalid data should be rejected with 422 validation errors."""
    # Empty first name
    res = client.post("/api/v1/charter/submit", json={
        "first_name": "",
        "last_name": "Doe",
        "email": "john@example.com",
        "commodity": "Coking Coal",
        "parcel_mt": 50000,
        "load_port": "Hay Point",
        "discharge_port": "Paradip"
    })
    assert res.status_code == 422

    # Invalid email
    res2 = client.post("/api/v1/charter/submit", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "not-an-email",
        "commodity": "Coking Coal",
        "parcel_mt": 50000,
        "load_port": "Hay Point",
        "discharge_port": "Paradip"
    })
    assert res2.status_code == 422

    # Negative parcel
    res3 = client.post("/api/v1/charter/submit", json={
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@example.com",
        "commodity": "Coking Coal",
        "parcel_mt": -100,
        "load_port": "Hay Point",
        "discharge_port": "Paradip"
    })
    assert res3.status_code == 422


def test_submit_valid_form_and_save():
    """TEST 2: Submitting a valid form generates a FW-YYYY-XXXXXX inquiry ID with PENDING status."""
    payload = {
        "first_name": "Arjun",
        "last_name": "Sharma",
        "email": "arjun.sharma@sailsteel.in",
        "commodity": "Clean Petroleum Products (ULSD/Gasoline)",
        "parcel_mt": 75000.0,
        "load_port": "Augusta, IT",
        "discharge_port": "Paradip, IN",
        "voyage_notes": "Urgent delivery required within laycan window"
    }
    res = client.post("/api/v1/charter/submit", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["inquiry_id"].startswith("FW-2026-")
    assert data["status"] == "PENDING"
    assert "inquiry_id" in data


def test_admin_unauthorized_access_denied():
    """TEST 7: Unauthenticated users are strictly denied access to admin endpoints."""
    # No token
    res = client.get("/api/v1/charter/admin/inquiries")
    assert res.status_code == 401

    # Invalid token
    res2 = client.get("/api/v1/charter/admin/inquiries", headers={"x-admin-token": "wrong-token"})
    assert res2.status_code == 401


def test_admin_authorized_fetch_and_status_update():
    """TEST 3 & 10: Authenticated admin can inspect inquiries and update their status."""
    # 1. First submit a new test inquiry
    sub_res = client.post("/api/v1/charter/submit", json={
        "first_name": "Priya",
        "last_name": "Verma",
        "email": "priya.verma@shipping.com",
        "commodity": "Liquid Chemicals (IMO II/III)",
        "parcel_mt": 12000.0,
        "load_port": "Rotterdam",
        "discharge_port": "Piraeus"
    })
    assert sub_res.status_code == 200
    inquiry_id = sub_res.json()["inquiry_id"]

    admin_headers = {"x-admin-token": settings.ADMIN_SECRET_TOKEN}

    # 2. Ping check
    ping_res = client.get("/api/v1/charter/admin/ping", headers=admin_headers)
    assert ping_res.status_code == 200

    # 3. Fetch all inquiries
    fetch_res = client.get("/api/v1/charter/admin/inquiries", headers=admin_headers)
    assert fetch_res.status_code == 200
    inquiries = fetch_res.json()["inquiries"]
    assert any(i["inquiry_id"] == inquiry_id for i in inquiries)

    # 4. Update status to 'VESSEL MATCHING'
    patch_res = client.patch(
        f"/api/v1/charter/admin/inquiries/{inquiry_id}/status",
        json={"status": "VESSEL MATCHING"},
        headers=admin_headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["new_status"] == "VESSEL MATCHING"

    # 5. Invalid status is rejected
    bad_patch = client.patch(
        f"/api/v1/charter/admin/inquiries/{inquiry_id}/status",
        json={"status": "NON_EXISTENT_STATUS"},
        headers=admin_headers
    )
    assert bad_patch.status_code == 422
    print("[PASS] test_admin_authorized_fetch_and_status_update")


if __name__ == "__main__":
    test_submit_invalid_form_validation_errors()
    print("[PASS] test_submit_invalid_form_validation_errors")
    test_submit_valid_form_and_save()
    print("[PASS] test_submit_valid_form_and_save")
    test_admin_unauthorized_access_denied()
    print("[PASS] test_admin_unauthorized_access_denied")
    test_admin_authorized_fetch_and_status_update()

