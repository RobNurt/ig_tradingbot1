# This file is for market scanning and analysis.
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
