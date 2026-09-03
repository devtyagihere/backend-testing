import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.vessel_service import vessel_service

def test_75k_parcel_vessel_matching():
    """75k MT at Paradip: Kamsarmax has only 0.19m UKC (below 0.3m minimum),
    so Panamax should be recommended instead for safety compliance."""
    matches, recommended = vessel_service.evaluate_vessel_fit(
        parcel_tonnage_mt=75000,
        origin_port_id="AUHPT",
        dest_port_id="INPRT"
    )
    # Panamax should be recommended (Kamsarmax fails 0.3m UKC at Paradip 14.5m draft)
    assert recommended == "Panamax"
    kamsarmax_match = next((m for m in matches if m.vessel_class == "Kamsarmax"), None)
    assert kamsarmax_match is not None
    # Kamsarmax arrival draft of ~14.31m leaves only 0.19m clearance at Paradip (14.5m)
    # This is below the 0.3m UKC minimum — correctly flagged as unsuitable
    assert kamsarmax_match.is_suitable is False
    assert kamsarmax_match.draft_clearance_m < 0.3
    print("[PASS] test_75k_parcel_vessel_matching (UKC safety enforced)")

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
    test_75k_parcel_vessel_matching()
    test_capesize_disqualified_at_paradip_for_small_parcel()
    test_haldia_port_requires_lighterage()
