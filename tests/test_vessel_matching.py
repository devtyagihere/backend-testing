import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.vessel_service import vessel_service

def test_75k_parcel_matches_kamsarmax():
    matches, recommended = vessel_service.evaluate_vessel_fit(
        parcel_tonnage_mt=75000,
        origin_port_id="AUHPT",
        dest_port_id="INPRT"
    )
    assert recommended in ["Kamsarmax", "Panamax"]
    kamsarmax_match = next((m for m in matches if m.vessel_class == "Kamsarmax"), None)
    assert kamsarmax_match is not None
    assert kamsarmax_match.is_suitable is True
    assert kamsarmax_match.estimated_arrival_draft_m <= 14.5
    print("[PASS] test_75k_parcel_matches_kamsarmax")

def test_capesize_disqualified_at_paradip_for_small_parcel():
    matches, _ = vessel_service.evaluate_vessel_fit(
        parcel_tonnage_mt=75000,
        origin_port_id="AUHPT",
        dest_port_id="INPRT"
    )
    cape_match = next((m for m in matches if m.vessel_class == "Capesize"), None)
    assert cape_match is not None
    assert cape_match.is_suitable is False
    print("[PASS] test_capesize_disqualified_at_paradip_for_small_parcel")

def test_haldia_port_requires_lighterage():
    matches, _ = vessel_service.evaluate_vessel_fit(
        parcel_tonnage_mt=75000,
        origin_port_id="AUHPT",
        dest_port_id="INHLD"
    )
    panamax_match = next((m for m in matches if m.vessel_class == "Panamax"), None)
    assert panamax_match is not None
    assert panamax_match.lighterage_required is True
    print("[PASS] test_haldia_port_requires_lighterage")

if __name__ == "__main__":
    test_75k_parcel_matches_kamsarmax()
    test_capesize_disqualified_at_paradip_for_small_parcel()
    test_haldia_port_requires_lighterage()
