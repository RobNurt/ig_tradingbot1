# This file contains the main TradingBot class.
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
