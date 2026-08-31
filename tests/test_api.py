import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"
    print("[PASS] test_api_health")

def test_api_ports():
    res = client.get("/api/v1/ports/indian")
    assert res.status_code == 200
    ports = res.json()
    assert len(ports) == 7
    paradip = next((p for p in ports if p["id"] == "INPRT"), None)
    assert paradip is not None
    assert paradip["max_draft_m"] == 14.5
    print("[PASS] test_api_ports")

def test_api_vessels():
    res = client.get("/api/v1/vessels")
    assert res.status_code == 200
    vessels = res.json()
    assert len(vessels) >= 7
    print("[PASS] test_api_vessels")

def test_api_optimize():
    payload = {
        "parcel_tonnage_mt": 75000,
        "commodity": "Coking Coal",
        "origin_port_id": "AUHPT",
        "dest_port_id": "INPRT",
        "laycan_days_ahead": 21,
        "risk_tolerance": "BALANCED",
        "holding_cost_usd_per_day": 2500.0
    }
    res = client.post("/api/v1/optimize", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "recommendation" in data
    assert data["recommended_vessel_class"] in ["Kamsarmax", "Panamax"]
    print("[PASS] test_api_optimize")

def test_api_demo():
    res = client.get("/api/v1/demo/75k-coal-australia-paradip")
    assert res.status_code == 200
    data = res.json()
    assert data["recommended_vessel_class"] == "Kamsarmax"
    print("[PASS] test_api_demo")

def test_api_backtest():
    res = client.post("/api/v1/backtest?period_days=180&origin_port_id=AUHPT&dest_port_id=INPRT&parcel_size_mt=75000")
    assert res.status_code == 200
    data = res.json()
    assert data["total_voyages_simulated"] > 0
    assert "trades" in data
    print("[PASS] test_api_backtest")

if __name__ == "__main__":
    test_api_health()
    test_api_ports()
    test_api_vessels()
    test_api_optimize()
    test_api_demo()
    test_api_backtest()
