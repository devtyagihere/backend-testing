from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class PortInfo(BaseModel):
    id: str
    name: str
    state_or_country: str
    max_draft_m: float
    max_loa_m: float
    max_beam_m: float
    max_dwt: Optional[int] = None
    handling_rate_tpd: float
    allowed_vessel_classes: List[str]
    lighterage_required: bool = False
    transshipment_hub: Optional[str] = None
    demurrage_rate_per_day_usd: float = 20000
    avg_waiting_days: float = 2.0
    notes: Optional[str] = None

class VesselClassInfo(BaseModel):
    class_name: str
    dwt_min: int
    dwt_max: int
    typical_dwt: int
    typical_capacity_mt: int
    design_draft_m: float
    max_loa_m: float
    max_beam_m: float
    service_speed_knots: float
    sea_fuel_consumption_vlsfo_tpd: float
    port_fuel_consumption_mgo_tpd: float
    daily_opex_usd: float
    baltic_index_proxy: str
    base_tce_rate_usd_day: float
    description: str

class VesselMatchResult(BaseModel):
    vessel_class: str
    is_suitable: bool
    disqualification_reasons: List[str] = []
    estimated_arrival_draft_m: float
    port_max_draft_m: float
    draft_clearance_m: float
    loa_clearance_m: float
    beam_clearance_m: float
    capacity_utilization_pct: float
    lighterage_required: bool = False
    transshipment_recommendation: Optional[str] = None

class VoyageCostBreakdown(BaseModel):
    origin_name: str
    dest_name: str
    vessel_class: str
    distance_nm: float
    steaming_days: float
    loading_days: float
    discharge_days: float
    port_waiting_days: float
    total_voyage_days: float
    bunker_vlsfo_mt: float
    bunker_fuel_cost_usd: float
    vessel_charter_cost_usd: float
    port_dues_usd: float
    canal_dues_usd: float
    lighterage_cost_usd: float = 0.0
    total_voyage_cost_usd: float
    freight_rate_per_mt_usd: float

class ForecastPoint(BaseModel):
    day_offset: int
    date: str
    predicted_rate_usd_t: float
    lower_80_pct: float
    upper_80_pct: float
    lower_95_pct: float
    upper_95_pct: float
    predicted_bpi_index: float
    predicted_vlsfo_usd_t: float

class ForecastResponse(BaseModel):
    route_name: str
    vessel_class: str
    current_spot_rate_usd_t: float
    forecast_horizon_days: int
    trend_direction: str # "BEARISH", "BULLISH", "NEUTRAL"
    volatility_index: float
    historical_points: List[Dict[str, Any]]
    forecast_points: List[ForecastPoint]

class OptimizeRequest(BaseModel):
    parcel_tonnage_mt: float = Field(default=75000, ge=10000, le=250000)
    commodity: str = Field(default="Coking Coal")
    origin_port_id: str = Field(default="AUHPT") # Gladstone / Hay Point
    dest_port_id: str = Field(default="INPRT")   # Paradip Port
    laycan_days_ahead: int = Field(default=21, ge=5, le=60) # Arrival readiness window
    risk_tolerance: str = Field(default="BALANCED") # "CONSERVATIVE", "BALANCED", "AGGRESSIVE"
    holding_cost_usd_per_day: float = Field(default=2500.0)

class RiskAssessment(BaseModel):
    volatility_warning: bool
    congestion_risk_level: str # "LOW", "MEDIUM", "HIGH"
    stockout_risk_score: float # 0.0 to 1.0
    demurrage_exposure_usd: float
    monsoon_impact_flag: bool
    cyclone_season_flag: bool

class OptimizeResponse(BaseModel):
    recommendation: str # "WAIT", "BOOK_NOW", "SPLIT_PARCEL"
    decision_summary: str
    confidence_pct: float
    optimal_booking_day_offset: int
    optimal_booking_date: str
    current_spot_rate_usd_t: float
    target_booking_rate_usd_t: float
    expected_savings_usd: float
    expected_savings_pct: float
    recommended_vessel_class: str
    all_vessel_matches: List[VesselMatchResult]
    voyage_breakdown: VoyageCostBreakdown
    forecast_curve: List[ForecastPoint]
    risk_assessment: RiskAssessment

class BacktestTrade(BaseModel):
    trade_id: int
    date: str
    route: str
    parcel_mt: float
    vessel_class: str
    spot_rate_usd_t: float
    model_action: str
    actual_booked_rate_usd_t: float
    naive_rate_usd_t: float
    savings_usd: float
    was_profitable: bool

class BacktestResponse(BaseModel):
    total_voyages_simulated: int
    profitable_decisions_pct: float
    total_freight_spend_naive_usd: float
    total_freight_spend_model_usd: float
    total_savings_usd: float
    savings_percentage: float
    avg_savings_per_voyage_usd: float
    trades: List[BacktestTrade]
