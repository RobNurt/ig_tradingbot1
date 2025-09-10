# This file is for managing open positions.
import requests
from requests import Timeout, RequestException
from typing import Dict, List, Optional
import logging
import json

class PositionManager:
    def __init__(self, session, headers, base_url):
        self.session = session
        self.headers = headers
        self.base_url = base_url

    def get_open_position(self, epic):
        headers = self.headers.copy()
        headers["Version"] = "2"
        try:
            r = self.session.get(f"{self.base_url}/positions", headers=headers)
            if r.status_code == 200:
                for p in r.json().get("positions", []):
                    if p["market"]["epic"] == epic:
                        return p
        except (Timeout, RequestException) as e:
            logging.error(f"Error fetching open positions: {e}")
        return None

    def get_open_positions_map(self) -> Dict[str, Dict]:
        """Returns a dict of open positions keyed by epic."""
        positions = self.list_all_open_positions()
        return {p["market"]["epic"]: p for p in positions}

    def list_all_open_positions(self) -> List[Dict]:
        headers = self.headers.copy()
        headers["Version"] = "2"
        try:
            r = self.session.get(f"{self.base_url}/positions", headers=headers)
            if r.status_code == 200:
                return r.json().get("positions", [])
        except (Timeout, RequestException) as e:
            logging.error(f"Error fetching open positions: {e}")
        return []

    def close_position_by_epic(self, epic: str, reason: str = "") -> bool:
        """Closes a position using the epic identifier."""
        position = self.get_open_position(epic)
        if not position:
            return False
        
        deal_id = position["position"]["dealId"]
        direction = position["position"]["direction"]
        size = position["position"]["size"]
        
        logging.info(f"Closing position for {epic} (Deal ID: {deal_id}) due to: {reason}")
        return self.close_position(deal_id, direction, size)

    def close_position(self, deal_id: str, direction: str, size: float) -> bool:
        headers = self.headers.copy()
        headers["Version"] = "3"
        payload = {
            "dealId": deal_id,
            "direction": "SELL" if direction == "BUY" else "BUY",
            "orderType": "MARKET",
            "size": size,
            "timeInForce": "FILL_OR_KILL",
        }
        try:
            r = self.session.post(f"{self.base_url}/positions/otc", headers=headers, json=payload)
            if r.status_code in (200, 202):
                return True
            else:
                logging.warning(f"Failed to close position {deal_id}: {r.status_code} {r.text}")
                return False
        except (Timeout, RequestException) as e:
            logging.error(f"Request failed to close position {deal_id}: {e}")
            return False
            
    def set_manual_trailing_stop(self, deal_id, stop_level):
        headers = self.headers.copy()
        headers["Version"] = "2"
        data = {"stopLevel": stop_level}
        try:
            r = self.session.put(f"{self.base_url}/positions/otc/{deal_id}", headers=headers, json=data)
            logging.info(f"Manual trailing stop set at {stop_level}: {r.status_code} {r.text}")
        except Exception as e:
            logging.error(f"Error setting trailing stop: {e}")

    def amend_position(self, deal_id: str, stop: float = None, limit: float = None):
        headers = self.headers.copy()
        headers["Version"] = "2"
        payload = {}
        if stop is not None:
            payload["stopLevel"] = float(stop)
        if limit is not None:
            payload["limitLevel"] = float(limit)
        if not payload:
            return False
        try:
            r = self.session.put(f"{self.base_url}/positions/otc/{deal_id}", headers=headers, json=payload)
            logging.info(f"Amended position {deal_id}: {r.status_code} {r.text}")
        except Exception as e:
            logging.error(f"Error amending position: {e}")
