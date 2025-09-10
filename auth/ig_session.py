# This file handles all authentication and session management.
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
    """Loads IG credentials from environment (.env supported)."""
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
    """
    Handles authentication and session management with the IG API.
    """
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
