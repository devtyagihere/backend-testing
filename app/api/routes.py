from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from app.models.schemas import (
    PortInfo, VesselClassInfo, VesselMatchResult, VoyageCostBreakdown,
    ForecastResponse, OptimizeRequest, OptimizeResponse,
    BacktestResponse
)
from app.services.port_service import port_service
from app.services.vessel_service import vessel_service
from app.services.voyage_service import voyage_service
from app.services.forecasting_engine import forecasting_engine
from app.services.optimizer_service import optimizer_service
from app.services.backtest_service import backtest_service

router = APIRouter()

@router.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "SAIL Freight Forecasting & Chartering Decision Engine",
        "version": "1.0.0"
    }

@router.get("/ports/indian", response_model=List[PortInfo], tags=["Ports & Routes"])
def get_indian_ports():
    """Retrieve all 7 Indian East Coast Ports with physical constraints (Draft, LOA, Beam, TPD)."""
    return port_service.get_all_indian_ports()

@router.get("/ports/origin", response_model=List[PortInfo], tags=["Ports & Routes"])
def get_origin_ports():
    """Retrieve major global loading origin ports (Australia, Indonesia, Mozambique, Russia, USA)."""
    return port_service.get_all_origin_ports()

@router.get("/vessels", response_model=List[VesselClassInfo], tags=["Vessels"])
def get_vessel_classes():
    """Retrieve bulk carrier specifications from Handysize to Newcastlemax."""
    return vessel_service.get_all_vessel_classes()

@router.get("/market/latest", tags=["Market Data"])
def get_latest_market_data():
    """Get the latest market snapshot for Baltic sub-indices (BCI, BPI, BSI, BHSI) and bunker fuel."""
    return forecasting_engine.get_latest_market_snapshot()

@router.get("/market/history", tags=["Market Data"])
def get_market_history(days: int = Query(default=60, ge=7, le=730)):
    """Retrieve historical market index and freight time-series."""
    return forecasting_engine.get_historical_window(days=days)

@router.post("/optimize", response_model=OptimizeResponse, tags=["Optimization"])
def optimize_charter(request: OptimizeRequest):
    """
    Run full multi-layer decision optimization:
    1. Deterministic port & vessel constraints check
    2. Multi-horizon freight forecast curve with confidence bands
    3. 'Wait or Book' timing recommendation minimizing net procurement cost
    """
    try:
        return optimizer_service.optimize_charter_decision(request)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/backtest", response_model=BacktestResponse, tags=["Backtesting"])
def run_historical_backtest(
    period_days: int = Query(default=365, ge=30, le=730),
    origin_port_id: str = Query(default="AUHPT"),
    dest_port_id: str = Query(default="INPRT"),
    parcel_size_mt: float = Query(default=75000)
):
    """
    Run historical backtest against actual spot market trajectories
    to demonstrate dollar savings vs naive day-of-booking procurement.
    """
    return backtest_service.run_backtest(
        test_period_days=period_days,
        origin_id=origin_port_id,
        dest_id=dest_port_id,
        parcel_size_mt=parcel_size_mt
    )

@router.get("/demo/75k-coal-australia-paradip", response_model=OptimizeResponse, tags=["Demo"])
def run_official_sih_demo():
    """
    Official SIH Minimum Demo Scenario:
    - Cargo: 75,000 MT Hard Coking Coal
    - Route: Hay Point / Gladstone (Australia) -> Paradip Port (East Coast India)
    - Returns: Draft limit check, Kamsarmax/Panamax recommendation, forecast curve, and Wait/Book recommendation.
    """
    demo_req = OptimizeRequest(
        parcel_tonnage_mt=75000,
        commodity="Coking Coal",
        origin_port_id="AUHPT",
        dest_port_id="INPRT",
        laycan_days_ahead=21,
        risk_tolerance="BALANCED",
        holding_cost_usd_per_day=2500.0
    )
    return optimizer_service.optimize_charter_decision(demo_req)
