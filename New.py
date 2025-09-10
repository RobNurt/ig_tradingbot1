import os
import sys
import json
import logging
import tkinter as tk

# Define the root directory for the new project structure
# You can change this if you want the folders created elsewhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Define the file and folder structure with placeholder content
structure = {
    "auth": {
        "ig_session.py": """# This file handles all authentication and session management.
import os
from dotenv import load_dotenv
import requests
from requests import Timeout, RequestException
import json
import logging
import time
from typing import Optional

# This helper class is from the original auth.py
class IGAuth:
    \"\"\"Loads IG credentials from environment (.env supported).\"\"\"
    def __init__(self, mode: str = "demo"):
        load_dotenv()
        self.mode = (mode or "demo").strip().lower()
        if self.mode == "live":
            self.username = os.getenv("IG_LIVE_USERNAME", "")
            self.password = os.getenv("IG_LIVE_PASSWORD", "")
            self.api_key  = os.getenv("IG_LIVE_API_KEY",  "")
            self.base_url = "https://api.ig.com/gateway/deal"
        else:
            self.username = os.getenv("IG_USERNAME", "")
            self.password = os.getenv("IG_PASSWORD", "")
            self.api_key  = os.getenv("IG_API_KEY",  "")
            self.base_url = "https://demo-api.ig.com/gateway/deal"
            
    @property
    def credentials(self):
        return {"identifier": self.username, "password": self.password}
        
    def debug_print(self):
        logging.info(f"Mode: {self.mode}")
        logging.info(f"Base URL: {self.base_url}")

class IGSession:
    \"\"\"
    Handles authentication and session management with the IG API.
    \"\"\"
    def __init__(self, mode: str = "demo"):
        self.auth = IGAuth(mode=mode)
        self.session = requests.Session()
        self.headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json; charset=UTF-8",
            "X-IG-API-KEY": self.auth.api_key,
            "Version": "2",
        }
        self.account_id = None
        self.cst_token = None
        self.x_security_token = None
        self.is_authenticated = False

    def login(self) -> bool:
        logging.info("Authenticating with IG...")
        try:
            self.auth.debug_print()
            r = self.session.post(
                f"{self.auth.base_url}/session",
                data=json.dumps(self.auth.credentials),
                headers=self.headers,
                timeout=10
            )
            
            if r.status_code == 200:
                self.cst_token = r.headers["CST"]
                self.x_security_token = r.headers["X-SECURITY-TOKEN"]
                self.account_id = r.json().get("accountId")

                self.headers["CST"] = self.cst_token
                self.headers["X-SECURITY-TOKEN"] = self.x_security_token
                self.is_authenticated = True
                logging.info("Successfully authenticated.")
                return True
            else:
                logging.error(f"Authentication failed: {r.status_code} {r.text}")
                return False
        except (Timeout, RequestException) as e:
            logging.error(f"Authentication error: {e}")
            return False

    def logout(self) -> None:
        try:
            r = self.session.delete(f"{self.auth.base_url}/session", headers=self.headers)
            if r.status_code in (200, 204):
                logging.info("Successfully logged out.")
        except Exception as e:
            logging.warning(f"Logout error: {e}")

    def get_headers(self):
        return self.headers

    def get_base_url(self):
        return self.auth.base_url
""",
    },
    "data_feed": {
        "market_data.py": """# This file is for fetching market data.
import requests
from typing import Dict, List, Optional
import logging
import pandas as pd
from requests import Timeout, RequestException
import json

class MarketData:
    def __init__(self, session, headers, base_url):
        self.session = session
        self.headers = headers
        self.base_url = base_url

    def get_market_details(self, epic) -> tuple:
        headers = self.headers.copy()
        headers["Version"] = "3"
        r = self.session.get(f"{self.base_url}/markets/{epic}", headers=headers)
        if r.status_code == 200:
            data = r.json()
            return (
                data["dealingRules"]["minDealSize"]["value"],
                data["instrument"]["marginFactor"],
                data["snapshot"]["bid"],
                data["snapshot"]["offer"]
            )
        return 0, 0, None, None
        
    def get_prices(self, epic, resolution="MINUTE", max_points=200) -> Optional[List[Dict]]:
        headers = self.headers.copy()
        headers["Version"] = "3"
        
        RES_MAP = {
            "MINUTE": "MINUTE",
            "MINUTE_2": "MINUTE_2",
            "MINUTE_3": "MINUTE_3",
            "MINUTE_5": "MINUTE_5",
            "MINUTE_10": "MINUTE_10",
            "MINUTE_15": "MINUTE_15",
            "MINUTE_30": "MINUTE_30",
            "HOUR": "HOUR",
            "HOUR_2": "HOUR_2",
            "HOUR_3": "HOUR_3",
            "HOUR_4": "HOUR_4",
            "DAY": "DAY",
            "WEEK": "WEEK",
            "MONTH": "MONTH",
        }
        
        res = RES_MAP.get(resolution, "MINUTE")

        url = f"{self.base_url}/prices/{epic}?resolution={res}&max_points={max_points}"
        
        try:
            r = self.session.get(url, headers=headers)
            if r.status_code == 200:
                return (r.json() or {}).get("prices", [])
            else:
                logging.warning(f"Failed to get prices for {epic}: {r.status_code} {r.text}")
                return []
        except (Timeout, RequestException) as e:
            logging.error(f"Error fetching prices for {epic}: {e}")
            return []

    def get_mid_price(self, epic: str) -> Optional[float]:
        _, _, bid, offer = self.get_market_details(epic)
        if bid is not None and offer is not None:
            return (float(bid) + float(offer)) / 2.0
        return None

    def get_candles(self, epic: str, resolution: str, max_bars: int) -> Optional[pd.DataFrame]:
        \"\"\"
        Fetches candlestick data and returns a pandas DataFrame.
        \"\"\"
        candles = self.get_prices(epic, resolution=resolution, max_points=max_bars)
        if not candles:
            return None
        
        df = pd.DataFrame(candles)
        
        df['high'] = df['highPrice'].apply(lambda x: float(x.get('bid', float('nan'))))
        df['low'] = df['lowPrice'].apply(lambda x: float(x.get('bid', float('nan'))))
        df['open'] = df['openPrice'].apply(lambda x: float(x.get('bid', float('nan'))))
        df['close'] = df['closePrice'].apply(lambda x: float(x.get('bid', float('nan'))))
        
        df['snapshotTime'] = pd.to_datetime(df['snapshotTime'], utc=True)
        df.set_index('snapshotTime', inplace=True)
        
        return df

""",
    },
    "ig_trading": {
        "order_manager.py": """# This file contains the core trading logic for orders.
from typing import List, Dict, Optional
from requests import Timeout, RequestException
import json
import re, time
import requests
import logging

def _safe_ref(text: str, maxlen: int = 30) -> str:
    \"\"\"Alnum/underscore only, trimmed to IG's length limits.\"\"\"
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
""",
        "position_manager.py": """# This file is for managing open positions.
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
        \"\"\"Returns a dict of open positions keyed by epic.\"\"\"
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
        \"\"\"Closes a position using the epic identifier.\"\"\"
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
""",
        "scanner.py": """# This file is for market scanning and analysis.
import logging
import pandas as pd
from typing import Optional, List, Dict
import requests

class Scanner:
    def __init__(self, market_data):
        self.md = market_data

    def get_ohlc(self, epic, resolution="MINUTE", lookback=200):
        prices = self.md.get_prices(epic, resolution=resolution, max_points=lookback)
        return prices or []

    def recent_high_low(self, epic, lookback=200):
        ohlc = self.get_ohlc(epic, lookback=lookback)
        if not ohlc:
            return None, None, None, None
        highs = [(i, float(c["highPrice"]["bid"])) for i, c in enumerate(ohlc)]
        lows  = [(i, float(c["lowPrice"]["bid"])) for i, c in enumerate(ohlc)]
        i_hi, v_hi = max(highs, key=lambda x: x[1])
        i_lo, v_lo = min(lows,  key=lambda x: x[1])
        return v_hi, v_lo, i_hi, i_lo

    def is_breaking_high(self, epic, buffer=0.0, lookback=200):
        v_hi, _, _, _ = self.recent_high_low(epic, lookback)
        if v_hi is None:
            return False
        _, _, bid, offer = self.md.get_market_details(epic)
        if bid is None or offer is None:
            return False
        return offer > v_hi + buffer
""",
        "ladder_engine.py": """# This file contains the laddering logic.
from typing import Dict, Optional, Callable
from datetime import datetime, timezone
import logging

class LadderParams:
    def __init__(self, first_offset_pts: float, step_pts: float, rungs: int,
                 fail_fast_minutes: int, require_resistance_break: bool=True,
                 use_gslo_near_close: bool=True):
        self.first_offset_pts = first_offset_pts
        self.step_pts = step_pts
        self.rungs = int(rungs)
        self.fail_fast_minutes = int(fail_fast_minutes)
        self.require_resistance_break = require_resistance_break
        self.use_gslo_near_close = use_gslo_near_close

def place_breakout_ladder(epic: str,
                          side: str,
                          get_current_price: Callable[[str], float],
                          get_recent_resistance: Callable[[str], float],
                          place_stop_entry: Callable[[str, float, str, Optional[float], Optional[bool]], str],
                          convert_to_trailing: Callable[[str], None],
                          params: LadderParams) -> Dict:
    px = get_current_price(epic)
    if params.require_resistance_break:
        res = get_recent_resistance(epic)
        base = max(px, res) + params.first_offset_pts if side=="BUY" else min(px, res) - params.first_offset_pts
    else:
        base = px + params.first_offset_pts if side=="BUY" else px - params.first_offset_pts

    tickets = []
    for i in range(params.rungs):
        level = base + i * params.step_pts if side == "BUY" else base - i * params.step_pts
        use_gslo = params.use_gslo_near_close
        deal_ref = place_stop_entry(epic, level, side, None, use_gslo)
        tickets.append({"rung": i+1, "level": level, "deal_ref": deal_ref})
        if not deal_ref:
            logging.warning(f"Failed to place rung {i+1} for {epic}")
            break
    
    return {"tickets": tickets}
""",
        "trading_bot.py": """# This file contains the main TradingBot class.
import time
import requests
from requests import Timeout, RequestException
from typing import Optional, List
import pandas as pd
import logging
import os
import sys

# Ensure parent directory is in path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/..")

from auth.ig_session import IGSession
from data_feed.market_data import MarketData
from ig_trading.order_manager import OrderManager, OrderStore
from ig_trading.position_manager import PositionManager
from ig_trading.scanner import Scanner

class TradingBot:
    def __init__(self, mode: str = "demo", default_stop_distance: float = 8.0, store_path: str = "orders.json"):
        self.session_handler = IGSession(mode=mode)
        self.md = MarketData(self.session_handler.session, self.session_handler.get_headers(), self.session_handler.get_base_url())
        self.pm = PositionManager(self.session_handler.session, self.session_handler.get_headers(), self.session_handler.get_base_url())
        self.om = None  # set after authenticate()

        self.default_stop_distance = default_stop_distance
        self.store_path = store_path

    def authenticate(self) -> bool:
        if self.session_handler.login():
            self.om = OrderManager(self.session_handler.session, self.session_handler.get_headers(), self.session_handler.get_base_url(), self.store_path)
            return True
        return False
        
    def logout(self) -> None:
        self.session_handler.logout()

    def get_mid_price(self, epic: str) -> Optional[float]:
        return self.md.get_mid_price(epic)

    def get_candles(self, epic: str, resolution: str, max_bars: int) -> Optional[pd.DataFrame]:
        return self.md.get_candles(epic, resolution, max_bars)
""",
    },
    "gui.py": """# gui.py
# Simple IG control panel for laddered stop-entries + manual trailing stop + limit (take-profit) on open position.
import os
import sys
from dotenv import load_dotenv
load_dotenv()

import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
import json

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ig_trading.trading_bot import TradingBot
from ig_trading.ladder_engine import LadderParams, place_breakout_ladder

# Placeholder for styles
def apply_styles(root):
    try:
        from styles import apply_styles as imported_apply_styles
        imported_apply_styles(root)
    except ImportError:
        logging.warning("styles.py not found. Using default Tkinter styles.")

CONFIG_PATH = Path(__file__).resolve().parent / "ig_trading" / "bot_config_from_history.json"
try:
    with CONFIG_PATH.open() as f:
        BOTCFG = json.load(f)
except FileNotFoundError:
    BOTCFG = {}
    logging.warning("bot_config_from_history.json not found.")

class RsiRotationConfig:
    def __init__(self, ema_fast, ema_slow, rsi_len):
        self.ema_fast = ema_fast
        self.ema_slow = ema_slow
        self.rsi_len = rsi_len

def rank_instruments_by_rsi(watchlist, fetch_candles, RSI_CFG):
    return []

def rotation_and_manage_positions(signals, open_positions, close_fn, ladder_fn, RSI_CFG):
    pass

DEFAULTS = {
    "base_offset": 5.0,
    "gap": 10.0,
    "count": 4,
    "stop_distance": 8.0,
    "size": "min",
    "trail_stop": True,
    "trail_stop_dist": 10.0,
}

class IGControlGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("IG Trading Bot Control")
        self.bot = TradingBot()
        self.logged_in = False
        self.is_trading = False
        self.trade_thread = None

        self._create_widgets()

    def _create_widgets(self):
        # ... (GUI widget creation logic here)
        pass

    def _login(self):
        # ... (login logic here)
        pass

    def _start_trading(self):
        # ... (start trading logic here)
        pass
        
    def _run_trading_logic(self):
        # ... (trading logic loop here)
        pass

    def _log(self, msg):
        # ... (log to ScrolledText widget)
        pass
""",
    "main.py": """# Main application entry point.
import os
import sys
import logging
import tkinter as tk

# Add the parent directory to the Python path to allow imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# These imports are now correct based on the new folder structure
from gui import IGControlGUI

# Placeholder for styles.py, which was not provided
# A simple apply_styles function is needed for the GUI to run
class styles:
    @staticmethod
    def apply_styles(root):
        logging.info("Applying default styles (styles.py not provided).")

def main():
    try:
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        root = tk.Tk()
        styles.apply_styles(root)
        IGControlGUI(root)
        root.mainloop()

    except Exception as e:
        logging.critical(f"An unhandled exception occurred: {e}")

if __name__ == "__main__":
    main()
""",
    "bot_config_from_history.json": """{
    "global": {
        "ema_fast": 12,
        "ema_slow": 26,
        "rsi_len": 14
    }
}
""",
}

def create_structure(base_path, structure_dict):
    """Recursively creates directories and files based on the structure dictionary."""
    for name, content in structure_dict.items():
        path = os.path.join(base_path, name)
        if isinstance(content, dict):
            # It's a directory, so create it and recurse
            try:
                os.makedirs(path, exist_ok=True)
                print(f"Created directory: {path}")
                create_structure(path, content)
            except OSError as e:
                print(f"Error creating directory {path}: {e}")
        else:
            # It's a file, so create it and write the content
            try:
                with open(path, "w") as f:
                    f.write(content)
                print(f"Created file: {path}")
            except IOError as e:
                print(f"Error creating file {path}: {e}")

if __name__ == "__main__":
    print("Starting project structure creation...")
    create_structure(BASE_DIR, structure)
    print("\nProject structure creation complete!")
    print("You can now run 'main.py' to test the basic setup.")
    print("You may need to install any required libraries (e.g., requests, pandas) if not already present.")
