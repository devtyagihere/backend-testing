import json
import os
from typing import List, Optional, Dict, Any
from app.models.schemas import PortInfo

class PortService:
    def __init__(self):
        self._load_data()

    def _load_data(self):
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "ports_db.json")
        with open(data_path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        
        self.indian_ports: Dict[str, Dict[str, Any]] = {p["id"]: p for p in data["indian_ports"]}
        self.origin_ports: Dict[str, Dict[str, Any]] = {p["id"]: p for p in data["origin_ports"]}

    def get_all_indian_ports(self) -> List[PortInfo]:
        results = []
        for p in self.indian_ports.values():
            results.append(PortInfo(
                id=p["id"],
                name=p["name"],
                state_or_country=p["state"],
                max_draft_m=p["max_draft_m"],
                max_loa_m=p["max_loa_m"],
                max_beam_m=p["max_beam_m"],
                max_dwt=p.get("max_dwt"),
                handling_rate_tpd=p["discharge_rate_tpd"],
                allowed_vessel_classes=p["allowed_vessel_classes"],
                lighterage_required=p.get("lighterage_required", False),
                transshipment_hub=p.get("transshipment_hub"),
                demurrage_rate_per_day_usd=p.get("demurrage_rate_per_day_usd", 20000),
                avg_waiting_days=p.get("avg_waiting_days", 2.0),
                notes=p.get("notes")
            ))
        return results

    def get_all_origin_ports(self) -> List[PortInfo]:
        results = []
        for p in self.origin_ports.values():
            results.append(PortInfo(
                id=p["id"],
                name=p["name"],
                state_or_country=f"{p['region']}, {p['country']}",
                max_draft_m=p["max_draft_m"],
                max_loa_m=p["max_loa_m"],
                max_beam_m=p["max_beam_m"],
                max_dwt=None,
                handling_rate_tpd=p["loading_rate_tpd"],
                allowed_vessel_classes=p["allowed_vessel_classes"],
                lighterage_required=False,
                transshipment_hub=None,
                demurrage_rate_per_day_usd=p.get("demurrage_rate_per_day_usd", 22000),
                avg_waiting_days=1.5,
                notes=f"Key commodity: {p.get('commodity', 'Bulk Coal')}"
            ))
        return results

    def get_port_by_id(self, port_id: str) -> Optional[Dict[str, Any]]:
        return self.indian_ports.get(port_id) or self.origin_ports.get(port_id)

port_service = PortService()
