import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.schemas import OptimizeRequest
from app.services.optimizer_service import optimizer_service

def test_optimizer_recommendation():
    req = OptimizeRequest(
        parcel_tonnage_mt=75000,
        commodity="Coking Coal",
        origin_port_id="AUHPT",
        dest_port_id="INPRT",
        laycan_days_ahead=21,
        risk_tolerance="BALANCED"
    )
    res = optimizer_service.optimize_charter_decision(req)
    assert res.recommendation in ["WAIT", "BOOK_NOW"]
    assert res.recommended_vessel_class in ["Kamsarmax", "Panamax"]
    assert res.confidence_pct >= 70.0
    print(f"[PASS] test_optimizer_recommendation: {res.recommendation} (Confidence: {res.confidence_pct}%)")

if __name__ == "__main__":
    test_optimizer_recommendation()
