import json
import os
import math
from typing import Dict, Any
from app.models.schemas import VoyageCostBreakdown
from app.services.port_service import port_service
from app.services.vessel_service import vessel_service

class VoyageService:
    def __init__(self):
        self._load_data()

    def _load_data(self):
        routes_path = os.path.join(os.path.dirname(__file__), "..", "data", "routes_distances.json")
        with open(routes_path, "r", encoding="utf-8-sig") as f:
            self.routes_data = json.load(f)["routes"]

    def get_route_info(self, origin_id: str, dest_id: str) -> Dict[str, Any]:
        for r in self.routes_data:
            if r["origin_id"] == origin_id:
                dest = r["destinations"].get(dest_id)
                if dest:
                    return {
                        "origin_name": r["origin_name"],
                        "dest_name": dest["dest_name"],
                        "distance_nm": dest["distance_nm"],
                        "canal_transit": dest.get("canal_transit", "None"),
                        "canal_dues_usd": dest.get("canal_dues_usd", 0.0)
                    }
        # No silent fallback — unknown routes must be explicitly flagged
        raise ValueError(
            f"Route not found: origin '{origin_id}' to destination '{dest_id}'. "
            f"Please verify port IDs against the routes_distances database."
        )

    def calculate_voyage_economics(
        self,
        parcel_tonnage_mt: float,
        origin_id: str,
        dest_id: str,
        vessel_class_name: str,
        tce_daily_rate_usd: float = 17500.0,
        vlsfo_bunker_price_usd_t: float = 620.0
    ) -> VoyageCostBreakdown:
        route = self.get_route_info(origin_id, dest_id)
        vessel = vessel_service.get_vessel_by_class(vessel_class_name)
        origin_port = port_service.get_port_by_id(origin_id)
        dest_port = port_service.get_port_by_id(dest_id)

        speed_knots = vessel["service_speed_knots"]
        distance_nm = route["distance_nm"]

        # 1. Steaming Days (with 5% weather/sea margin)
        steaming_hours = (distance_nm / speed_knots) * 1.05
        steaming_days = round(steaming_hours / 24.0, 2)

        # 2. Port Days (Loading + Discharging)
        loading_rate = origin_port.get("loading_rate_tpd", 45000.0) if origin_port else 45000.0
        discharge_rate = dest_port.get("discharge_rate_tpd", 30000.0) if dest_port else 30000.0

        loading_days = round(parcel_tonnage_mt / loading_rate, 2)
        discharge_days = round(parcel_tonnage_mt / discharge_rate, 2)
        port_waiting_days = round(dest_port.get("avg_waiting_days", 1.8), 2) if dest_port else 1.8

        total_port_days = round(loading_days + discharge_days + port_waiting_days, 2)
        total_voyage_days = round(steaming_days + total_port_days, 2)

        # 3. Fuel Consumption
        vlsfo_sea_tpd = vessel["sea_fuel_consumption_vlsfo_tpd"]
        mgo_port_tpd = vessel["port_fuel_consumption_mgo_tpd"]
        
        bunker_vlsfo_mt = round(steaming_days * vlsfo_sea_tpd, 2)
        bunker_mgo_mt = round(total_port_days * mgo_port_tpd, 2)

        mgo_price_usd_t = vlsfo_bunker_price_usd_t * 1.25 # MGO is typically 25% premium over VLSFO
        bunker_cost_usd = round((bunker_vlsfo_mt * vlsfo_bunker_price_usd_t) + (bunker_mgo_mt * mgo_price_usd_t), 2)

        # 4. Charter Hire / Time Charter Equivalent Cost
        vessel_charter_cost_usd = round(total_voyage_days * tce_daily_rate_usd, 2)

        # 5. Port & Canal Dues
        port_dues_usd = 65000.0 # Standard port dues for major Indian bulk port
        canal_dues_usd = float(route.get("canal_dues_usd", 0.0))

        # 6. Lighterage Cost (if applicable, e.g. Haldia transshipment)
        lighterage_cost_usd = 0.0
        if dest_port and dest_port.get("lighterage_required", False) and vessel_class_name != "Handysize":
            # ~$4.50 per ton for offshore lightering barges at Sandheads
            lighterage_cost_usd = round(parcel_tonnage_mt * 4.50, 2)

        total_voyage_cost_usd = round(
            bunker_cost_usd + vessel_charter_cost_usd + port_dues_usd + canal_dues_usd + lighterage_cost_usd, 2
        )
        freight_rate_per_mt_usd = round(total_voyage_cost_usd / parcel_tonnage_mt, 2)

        return VoyageCostBreakdown(
            origin_name=route["origin_name"],
            dest_name=route["dest_name"],
            vessel_class=vessel_class_name,
            distance_nm=distance_nm,
            steaming_days=steaming_days,
            loading_days=loading_days,
            discharge_days=discharge_days,
            port_waiting_days=port_waiting_days,
            total_voyage_days=total_voyage_days,
            bunker_vlsfo_mt=bunker_vlsfo_mt,
            bunker_fuel_cost_usd=bunker_cost_usd,
            vessel_charter_cost_usd=vessel_charter_cost_usd,
            port_dues_usd=port_dues_usd,
            canal_dues_usd=canal_dues_usd,
            lighterage_cost_usd=lighterage_cost_usd,
            total_voyage_cost_usd=total_voyage_cost_usd,
            freight_rate_per_mt_usd=freight_rate_per_mt_usd
        )

voyage_service = VoyageService()
