from fastapi import APIRouter, HTTPException, Query, Body
from typing import List, Dict, Any, Optional
from datetime import datetime
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

# Pre-defined High Impact Scenarios for Hackathon Demos
PRESET_SCENARIOS = [
    {
        "id": "scenario-1",
        "title": "Official SIH Demo: 75k MT Coal (Aus -> Paradip)",
        "subtitle": "Kamsarmax direct berthing at Paradip CQ mechanized berth with rate dip wait optimization",
        "tag": "PRIMARY DEMO",
        "badge_color": "amber",
        "request": {
            "parcel_tonnage_mt": 75000,
            "commodity": "Coking Coal",
            "origin_port_id": "AUHPT",
            "dest_port_id": "INPRT",
            "laycan_days_ahead": 21,
            "risk_tolerance": "BALANCED",
            "holding_cost_usd_per_day": 2500.0
        }
    },
    {
        "id": "scenario-2",
        "title": "Deepwater Capesize: 160k MT Met Coal (Aus -> Gangavaram)",
        "subtitle": "Fully laden Capesize parcel taking advantage of Gangavaram's 20.0m draft and 55,000 TPD discharge",
        "tag": "CAPESIZE SCALE",
        "badge_color": "emerald",
        "request": {
            "parcel_tonnage_mt": 160000,
            "commodity": "Coking Coal",
            "origin_port_id": "AUHPT",
            "dest_port_id": "INGNR",
            "laycan_days_ahead": 28,
            "risk_tolerance": "AGGRESSIVE",
            "holding_cost_usd_per_day": 4000.0
        }
    },
    {
        "id": "scenario-3",
        "title": "Riverine & Lightering: 40k MT Low-Ash Coal (Indonesia -> Haldia)",
        "subtitle": "Evaluating river draft restriction (8.0m) and offshore lighterage requirement at Sandheads",
        "tag": "TRANSSHIPMENT",
        "badge_color": "purple",
        "request": {
            "parcel_tonnage_mt": 40000,
            "commodity": "Thermal Coal",
            "origin_port_id": "IDTBO",
            "dest_port_id": "INHLD",
            "laycan_days_ahead": 14,
            "risk_tolerance": "CONSERVATIVE",
            "holding_cost_usd_per_day": 1800.0
        }
    },
    {
        "id": "scenario-4",
        "title": "Suez Transit PCI Coal: 70k MT (Russia Ust-Luga -> Vizag)",
        "subtitle": "Long-distance European/Baltic route via Suez Canal with canal toll economics",
        "tag": "LONG HAUL",
        "badge_color": "sky",
        "request": {
            "parcel_tonnage_mt": 70000,
            "commodity": "PCI Coal",
            "origin_port_id": "RUUST",
            "dest_port_id": "INVTZ",
            "laycan_days_ahead": 35,
            "risk_tolerance": "BALANCED",
            "holding_cost_usd_per_day": 3000.0
        }
    }
]

OPERATIONAL_NOTIFICATIONS = [
    {
        "id": "notif-1",
        "type": "alert",
        "title": "BPI Rate Momentum Alert",
        "message": "Panamax index decreased 1.8% over the last 48 hours. Favorable window opening for Australian loadings.",
        "time": "12 mins ago",
        "read": False
    },
    {
        "id": "notif-2",
        "type": "warning",
        "title": "Gopalpur Swell Advisory",
        "message": "Monsoon swell forecast indicates possible 1.2 day discharge delays at Gopalpur Port between Sept 04-07.",
        "time": "1 hour ago",
        "read": False
    },
    {
        "id": "notif-3",
        "type": "info",
        "title": "Paradip CQ Berth Clearance",
        "message": "Paradip mechanized coal berth queue reduced to 1.4 days. Optimal turn-around window active.",
        "time": "3 hours ago",
        "read": True
    },
    {
        "id": "notif-4",
        "type": "success",
        "title": "Charter Executed (Bhilai Supply)",
        "message": "Charter #SAIL-2026-084 locked in at $12.95/MT, saving $84,200 vs initial spot quote.",
        "time": "Yesterday",
        "read": True
    }
]

USER_PROFILES = {
    "cpo": {
        "id": "USR-001",
        "name": "Devendra Tyagi",
        "title": "Chief Procurement & Shipping Officer",
        "organization": "Steel Authority of India Limited (SAIL)",
        "department": "Raw Materials & Bulk Chartering Division",
        "location": "SAIL Headquarters, New Delhi",
        "allocated_plants": ["Rourkela Steel Plant (RSP)", "Bhilai Steel Plant (BSP)", "Bokaro Steel Plant (BSL)"],
        "doa_limit_usd": 50000000,
        "avatar_badge": "DT",
        "role": "Procurement Authority"
    },
    "chartering_lead": {
        "id": "USR-002",
        "name": "Ananya Sen",
        "title": "Lead Vessel Operations & Chartering Broker",
        "organization": "SAIL Shipping Cell (Kolkata Port Operations)",
        "department": "Maritime Logistics & Laytime Management",
        "location": "Kolkata, West Bengal",
        "allocated_plants": ["Durgapur Steel Plant (DSP)", "IISCO Steel Plant (ISP Burnpur)"],
        "doa_limit_usd": 15000000,
        "avatar_badge": "AS",
        "role": "Chartering Specialist"
    },
    "auditor": {
        "id": "USR-003",
        "name": "Dr. R. K. Mukherjee",
        "title": "Principal Audit Officer",
        "organization": "Ministry of Steel, Government of India",
        "department": "Public Sector Vigilance & Procurement Oversight",
        "location": "Udyog Bhawan, New Delhi",
        "allocated_plants": ["All SAIL Units & Joint Ventures"],
        "doa_limit_usd": 0,
        "avatar_badge": "RM",
        "role": "Ministry Auditor"
    }
}

@router.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "SAIL Freight Forecasting & Chartering Decision Engine",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@router.get("/scenarios", tags=["Demos & Presets"])
def get_preset_scenarios():
    """Retrieve pre-configured hackathon demo scenarios for 1-click loading."""
    return PRESET_SCENARIOS

@router.get("/notifications", tags=["Operational Signals"])
def get_operational_notifications():
    """Retrieve live operational alerts, demurrage warnings, and rate change signals."""
    return OPERATIONAL_NOTIFICATIONS

@router.get("/profile", tags=["Authentication & User"])
def get_user_profile(role: str = Query(default="cpo")):
    """Retrieve current logged-in user profile details and plant authorizations."""
    return USER_PROFILES.get(role, USER_PROFILES["cpo"])

@router.get("/ports/indian", response_model=List[PortInfo], tags=["Ports & Routes"])
def get_indian_ports():
    return port_service.get_all_indian_ports()

@router.get("/ports/origin", response_model=List[PortInfo], tags=["Ports & Routes"])
def get_origin_ports():
    return port_service.get_all_origin_ports()

@router.get("/vessels", response_model=List[VesselClassInfo], tags=["Vessels"])
def get_vessel_classes():
    return vessel_service.get_all_vessel_classes()

@router.get("/market/latest", tags=["Market Data"])
def get_latest_market_data():
    return forecasting_engine.get_latest_market_snapshot()

@router.get("/market/history", tags=["Market Data"])
def get_market_history(days: int = Query(default=60, ge=7, le=730)):
    return forecasting_engine.get_historical_window(days=days)

@router.post("/optimize", response_model=OptimizeResponse, tags=["Optimization"])
def optimize_charter(request: OptimizeRequest):
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
    return backtest_service.run_backtest(
        test_period_days=period_days,
        origin_id=origin_port_id,
        dest_id=dest_port_id,
        parcel_size_mt=parcel_size_mt
    )

@router.get("/demo/75k-coal-australia-paradip", response_model=OptimizeResponse, tags=["Demo"])
def run_official_sih_demo():
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
