import json
import os
import math
from typing import List, Dict, Any, Tuple
from app.models.schemas import VesselClassInfo, VesselMatchResult
from app.services.port_service import port_service

class VesselService:
    def __init__(self):
        self._load_data()

    def _load_data(self):
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "vessels_db.json")
        with open(data_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        self.vessels: Dict[str, Dict[str, Any]] = {v["class_name"]: v for v in data["vessel_classes"]}

    def get_all_vessel_classes(self) -> List[VesselClassInfo]:
        return [VesselClassInfo(**v) for v in self.vessels.values()]

    def get_vessel_by_class(self, class_name: str) -> Dict[str, Any]:
        return self.vessels.get(class_name, self.vessels["Panamax"])

    def evaluate_vessel_fit(
        self,
        parcel_tonnage_mt: float,
        origin_port_id: str,
        dest_port_id: str
    ) -> Tuple[List[VesselMatchResult], str]:
        dest_port = port_service.get_port_by_id(dest_port_id)
        origin_port = port_service.get_port_by_id(origin_port_id)
        
        if not dest_port or not origin_port:
            raise ValueError("Invalid origin or destination port ID")

        match_results = []
        best_candidate = None
        min_freight_penalty = float("inf")

        for class_name, vessel in self.vessels.items():
            reasons = []
            is_suitable = True
            
            # 1. Capacity & Parcel Size check
            min_cap = vessel["dwt_min"] * 0.85
            max_cap = vessel["dwt_max"] * 0.95
            utilization = (parcel_tonnage_mt / vessel["typical_dwt"]) * 100.0

            if parcel_tonnage_mt < min_cap * 0.7:
                is_suitable = False
                reasons.append(f"Parcel size ({parcel_tonnage_mt:,.0f} MT) severely underfills vessel capacity (min required ~{min_cap:,.0f} MT).")
            elif parcel_tonnage_mt > max_cap:
                is_suitable = False
                reasons.append(f"Parcel size ({parcel_tonnage_mt:,.0f} MT) exceeds vessel deadweight capacity ({max_cap:,.0f} MT).")

            # 2. Dynamic Arrival Draft Calculation based on cargo load
            light_draft = 4.5
            load_factor = min(1.0, parcel_tonnage_mt / vessel["typical_capacity_mt"])
            estimated_draft = round(light_draft + (vessel["design_draft_m"] - light_draft) * math.sqrt(load_factor), 2)
            
            port_max_draft = dest_port["max_draft_m"]
            draft_clearance = round(port_max_draft - estimated_draft, 2)
            loa_clearance = round(dest_port["max_loa_m"] - vessel["max_loa_m"], 2)
            beam_clearance = round(dest_port["max_beam_m"] - vessel["max_beam_m"], 2)

            # 3. Port Physical Restrictions Check
            if draft_clearance < 0.0: # Minimum 0.3m under-keel clearance (UKC)
                is_suitable = False
                reasons.append(f"Draft restriction at {dest_port['name']}: Arrival draft {estimated_draft}m exceeds max permissible {port_max_draft}m (UKC clearance: {draft_clearance}m).")

            if loa_clearance < 0:
                is_suitable = False
                reasons.append(f"LOA restriction: Vessel length {vessel['max_loa_m']}m exceeds {dest_port['name']} berth limit {dest_port['max_loa_m']}m.")

            if beam_clearance < 0:
                is_suitable = False
                reasons.append(f"Beam restriction: Vessel beam {vessel['max_beam_m']}m exceeds berth limit {dest_port['max_beam_m']}m.")

            # 4. Special Lighterage & Transshipment Logic for Haldia / Sandheads
            lighterage_req = False
            transshipment_rec = None
            if dest_port.get("lighterage_required", False) and class_name not in ["Handysize"]:
                lighterage_req = True
                transshipment_rec = f"Requires offshore lightering at {dest_port.get('transshipment_hub', 'Sagar / Sandheads Anchorage')} before river transit to Haldia."
                if estimated_draft > port_max_draft:
                    reasons.append("Subject to mandatory lighterage at Sandheads Anchorage.")

            match_res = VesselMatchResult(
                vessel_class=class_name,
                is_suitable=is_suitable,
                disqualification_reasons=reasons,
                estimated_arrival_draft_m=estimated_draft,
                port_max_draft_m=port_max_draft,
                draft_clearance_m=draft_clearance,
                loa_clearance_m=loa_clearance,
                beam_clearance_m=beam_clearance,
                capacity_utilization_pct=round(min(100.0, utilization), 1),
                lighterage_required=lighterage_req,
                transshipment_recommendation=transshipment_rec
            )
            match_results.append(match_res)

            if is_suitable:
                utilization_diff = abs(utilization - 95.0)
                if utilization_diff < min_freight_penalty:
                    min_freight_penalty = utilization_diff
                    best_candidate = class_name

        if not best_candidate:
            for r in match_results:
                if "Panamax" in r.vessel_class or "Kamsarmax" in r.vessel_class:
                    best_candidate = r.vessel_class
                    break
            if not best_candidate:
                best_candidate = "Kamsarmax"

        return match_results, best_candidate

vessel_service = VesselService()
