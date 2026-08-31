import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.services.forecasting_engine import forecasting_engine

def test_forecast_confidence_bands():
    points, spot, trend, vol = forecasting_engine.generate_forecast(
        parcel_tonnage_mt=75000,
        origin_id="AUHPT",
        dest_id="INPRT",
        vessel_class="Kamsarmax",
        horizon_days=21
    )
    assert len(points) == 21
    assert spot > 0.0
    for p in points:
        assert p.lower_80_pct <= p.predicted_rate_usd_t <= p.upper_80_pct
        assert p.lower_95_pct <= p.lower_80_pct
        assert p.upper_80_pct <= p.upper_95_pct
    print("[PASS] test_forecast_confidence_bands")

if __name__ == "__main__":
    test_forecast_confidence_bands()
