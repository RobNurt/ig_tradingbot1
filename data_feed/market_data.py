# This file is for fetching market data.
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
        """
        Fetches candlestick data and returns a pandas DataFrame.
        """
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
