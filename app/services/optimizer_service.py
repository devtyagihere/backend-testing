from datetime import datetime, timedelta
from typing import Dict, Any
from app.models.schemas import (
    OptimizeRequest, OptimizeResponse, RiskAssessment,
    VesselMatchResult, VoyageCostBreakdown
)
from app.services.port_service import port_service
from app.services.vessel_service import vessel_service
from app.services.voyage_service import voyage_service
from app.services.forecasting_engine import forecasting_engine
from app.services.llm_service import llm_service

class CharterOptimizerService:
    def optimize_charter_decision(self, req: OptimizeRequest) -> OptimizeResponse:
        # 1. Deterministic Port & Vessel Matching
        vessel_matches, recommended_class = vessel_service.evaluate_vessel_fit(
            parcel_tonnage_mt=req.parcel_tonnage_mt,
            origin_port_id=req.origin_port_id,
            dest_port_id=req.dest_port_id
        )

        # 2. Freight Rate Forecast
        forecast_points, spot_rate, trend_dir, vol_idx = forecasting_engine.generate_forecast(
            parcel_tonnage_mt=req.parcel_tonnage_mt,
            origin_id=req.origin_port_id,
            dest_id=req.dest_port_id,
            vessel_class=recommended_class,
            horizon_days=req.laycan_days_ahead
        )

        # 3. Current Voyage Economics
        current_voyage = voyage_service.calculate_voyage_economics(
            parcel_tonnage_mt=req.parcel_tonnage_mt,
            origin_id=req.origin_port_id,
            dest_id=req.dest_port_id,
            vessel_class_name=recommended_class
        )

        # 4. "Wait vs Book" Cost Curve Optimization
        # For each future day t, calculate: Net Cost = (Forecasted Freight Rate * Tonnage) + (Holding Cost * t)
        # Find day t* that minimizes Net Cost within the permissible booking window (up to laycan - transit_days - 3)
        steaming_days = current_voyage.steaming_days
        max_wait_days = max(1, int(req.laycan_days_ahead - steaming_days - 3))
        max_wait_days = min(max_wait_days, len(forecast_points))

        best_day_idx = 0
        best_rate = spot_rate
        min_total_cost = spot_rate * req.parcel_tonnage_mt
        current_total_cost = min_total_cost

        # Risk tolerance tuning
        risk_multipliers = {
            "CONSERVATIVE": 1.25, # High holding/stockout penalty
            "BALANCED": 1.0,
            "AGGRESSIVE": 0.75   # Willing to wait longer for bigger rate dips
        }
        mult = risk_multipliers.get(req.risk_tolerance, 1.0)
        adj_holding_cost = req.holding_cost_usd_per_day * mult

        for i in range(max_wait_days):
            fp = forecast_points[i]
            # Use lower 80% CI weight for upside/downside risk
            expected_rate = fp.predicted_rate_usd_t
            holding_penalty = (i + 1) * adj_holding_cost
            total_projected_cost = (expected_rate * req.parcel_tonnage_mt) + holding_penalty

            if total_projected_cost < min_total_cost:
                min_total_cost = total_projected_cost
                best_rate = expected_rate
                best_day_idx = i + 1

        # 5. Recommendation Decision Logic
        today = datetime.now()
        expected_savings_usd = round(current_total_cost - (best_rate * req.parcel_tonnage_mt + (best_day_idx * adj_holding_cost)), 2)
        expected_savings_pct = round((expected_savings_usd / current_total_cost) * 100.0, 2)

        origin_port = port_service.get_port_by_id(req.origin_port_id)
        dest_port = port_service.get_port_by_id(req.dest_port_id)
        origin_name = origin_port.get("name", req.origin_port_id) if origin_port else req.origin_port_id
        dest_name = dest_port.get("name", req.dest_port_id) if dest_port else req.dest_port_id

        if best_day_idx > 0 and expected_savings_usd > 15000:
            recommendation = "WAIT"
            optimal_date = (today + timedelta(days=best_day_idx)).strftime("%Y-%m-%d")
            confidence = min(92.0, max(70.0, 85.0 - (best_day_idx * 1.2)))
        else:
            recommendation = "BOOK_NOW"
            best_day_idx = 0
            best_rate = spot_rate
            expected_savings_usd = 0.0
            expected_savings_pct = 0.0
            optimal_date = today.strftime("%Y-%m-%d")
            confidence = 88.0

        # Generate LLM-powered Executive Summary & Narrative
        summary = llm_service.generate_decision_narrative(
            recommendation=recommendation,
            commodity=req.commodity,
            parcel_tonnage=req.parcel_tonnage_mt,
            origin_port_name=origin_name,
            dest_port_name=dest_name,
            recommended_vessel=recommended_class,
            current_spot=spot_rate,
            target_rate=best_rate,
            expected_savings=expected_savings_usd,
            savings_pct=expected_savings_pct,
            optimal_day=best_day_idx,
            confidence_pct=confidence
        )

        # 6. Risk Assessment
        dest_port = port_service.get_port_by_id(req.dest_port_id)
        avg_wait = dest_port.get("avg_waiting_days", 1.8) if dest_port else 1.8
        demurrage_exposure = round(avg_wait * dest_port.get("demurrage_rate_per_day_usd", 20000), 2) if dest_port else 36000.0

        current_month = today.month
        monsoon_active = current_month in [6, 7, 8]
        cyclone_active = current_month in [1, 2, 3] and "AU" in req.origin_port_id

        congestion_level = "LOW" if avg_wait < 2.0 else ("MEDIUM" if avg_wait < 3.0 else "HIGH")

        risk = RiskAssessment(
            volatility_warning=vol_idx > 3.0,
            congestion_risk_level=congestion_level,
            stockout_risk_score=round(min(1.0, (best_day_idx / max(1, req.laycan_days_ahead))), 2),
            demurrage_exposure_usd=demurrage_exposure,
            monsoon_impact_flag=monsoon_active,
            cyclone_season_flag=cyclone_active
        )

        return OptimizeResponse(
            recommendation=recommendation,
            decision_summary=summary,
            confidence_pct=round(confidence, 1),
            optimal_booking_day_offset=best_day_idx,
            optimal_booking_date=optimal_date,
            current_spot_rate_usd_t=spot_rate,
            target_booking_rate_usd_t=best_rate,
            expected_savings_usd=max(0.0, expected_savings_usd),
            expected_savings_pct=max(0.0, expected_savings_pct),
            recommended_vessel_class=recommended_class,
            all_vessel_matches=vessel_matches,
            voyage_breakdown=current_voyage,
            forecast_curve=forecast_points,
            risk_assessment=risk
        )

optimizer_service = CharterOptimizerService()
