# This file contains the core trading logic for orders.
from typing import List, Dict, Optional
from requests import Timeout, RequestException
import json
import re, time, os
import requests
import logging

def _safe_ref(text: str, maxlen: int = 30) -> str:
    """Alnum/underscore only, trimmed to IG's length limits."""
    s = re.sub(r"[^A-Za-z0-9_]+", "_", text)
    return s[:maxlen] or f"R{int(time.time())}"

class OrderStore:
    # This class was in trading.py, but is better placed here.
    def __init__(self, path="orders.json"):
        self.path = path
        self.orders = {}
        if os.path.exists(path):
            with open(path) as f:
                self.orders = json.load(f)

    def add(self, epic, order_type, deal_ref):
        if epic not in self.orders:
            self.orders[epic] = []
        self.orders[epic].append({
            "deal_ref": deal_ref,
            "order_type": order_type,
            "timestamp": time.time()
        })
        self.save()

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.orders, f, indent=2)

class OrderManager:
    def __init__(self, session, headers, base_url, store_path="orders.json"):
        self.session = session
        self.headers = headers
        self.base_url = base_url
        self.store = OrderStore(store_path)

    def place_stop_entry(
        self,
        epic: str,
        level: float,
        direction: str,
        size: float = 1.0,
        use_gslo: bool = False,
        stop_distance: float | None = None,
        **kwargs,
    ):
        if "guaranteedStop" in kwargs and not use_gslo:
            use_gslo = bool(kwargs["guaranteedStop"])
        if "dealDirection" in kwargs and not direction:
            direction = str(kwargs["dealDirection"])

        lvl = round(float(level), 2)
        ref_base = f"STP_{direction}_{epic}_{int(lvl*100)}_{int(time.time()%1_000_000)}"
        deal_ref = _safe_ref(ref_base)

        payload = {
            "epic": epic,
            "expiry": "-",
            "direction": direction,
            "size": size,
            "level": lvl,
            "type": "STOP_ENTRY",
            "currencyCode": "GBP",
            "timeInForce": "GOOD_TILL_CANCELLED",
            "guaranteedStop": use_gslo,
        }
        if stop_distance is not None:
            payload["trailingStop"] = True
            payload["trailingStopDistance"] = stop_distance
            payload["guaranteedStop"] = False
        
        h = self.headers.copy()
        h["Version"] = "2"
        try:
            r = self.session.post(f"{self.base_url}/workingorders/otc", headers=h, json=payload)
            if r.status_code in (200, 201, 202):
                logging.info(f"Stop entry placed for {epic} at {level}. Deal ref: {deal_ref}")
                return (r.json() or {}).get("dealReference") or payload["dealReference"]
            logging.warning(f"place_stop_entry failed: {r.status_code} {r.text}")
            return None
        except (Timeout, RequestException) as e:
            logging.error(f"place_stop_entry error: {e}")
            return None

    def ensure_ladder(self, epic: str, base_level: float, size: float, count: int,
                      gap: float, max_live: int, stop_distance: float, lowering: bool = True):
        live = self.list_epic_stop_buys(epic)
        if len(live) >= max_live:
            return
        to_place = max(0, int(count) - len(live))
        for i in range(to_place):
            level = round(base_level + i * float(gap), 2)
            dr = self.place_stop_entry(epic, level, size, stop_distance=stop_distance)
            if dr:
                self.store.add(epic, "BUY_STOP_GTC", dr)

    def cancel_all_for_epic(self, epic: str) -> int:
        cancelled = 0
        for o in self.list_all_working_orders():
            md = o.get("marketData", {}) or {}
            wod = o.get("workingOrderData", {}) or {}
            if md.get("epic") == epic:
                try:
                    r = self.session.delete(
                        f"{self.base_url}/workingorders/otc/{wod['dealId']}",
                        headers=self.headers.copy()
                    )
                    if r.status_code == 200:
                        cancelled += 1
                        logging.info(f"Cancelled order for {epic}: {wod['dealId']}")
                    else:
                        logging.warning(f"Failed to cancel order {wod['dealId']}: {r.text}")
                except Exception as e:
                    logging.error(f"Error cancelling order: {e}")
        return cancelled

    def list_all_working_orders(self) -> List[Dict]:
        h = self.headers.copy()
        h["Version"] = "2"
        try:
            r = self.session.get(f"{self.base_url}/workingorders", headers=h)
            if r.status_code == 200:
                return r.json().get("workingOrders", [])
        except (Timeout, RequestException) as e:
            logging.error(f"Error fetching working orders: {e}")
        return []

    def list_epic_stop_buys(self, epic: str) -> List[Dict]:
        return [o for o in self.list_all_working_orders()
                if o.get("marketData", {}).get("epic") == epic
                and o.get("workingOrderData", {}).get("direction") == "BUY"
                and o.get("workingOrderData", {}).get("type") == "STOP_ENTRY"]
