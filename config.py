"""
Configuration management for IG Trading Bot
Handles loading credentials and settings from .env file
"""
import os
from pathlib import Path

class Config:
    """Configuration manager for trading bot"""
    
    def __init__(self):
        self.load_env()
        
        # Demo account credentials
        self.demo_username = os.environ.get('IG_USERNAME', '')
        self.demo_password = os.environ.get('IG_PASSWORD', '')
        self.demo_api_key = os.environ.get('IG_API_KEY', '')
        
        # Live account credentials
        self.live_username = os.environ.get('IG_LIVE_USERNAME', '')
        self.live_password = os.environ.get('IG_LIVE_PASSWORD', '')
        self.live_api_key = os.environ.get('IG_LIVE_API_KEY', '')
        
        # API URLs
        self.demo_url = "https://demo-api.ig.com/gateway/deal"
        self.live_url = "https://api.ig.com/gateway/deal"
        
        # Market epics - spread betting
        self.markets = {
            "Gold Spot": "CS.D.USCGC.TODAY.IP",
            "Russell 2000": "IX.D.RUSSELL.DAILY.IP",
            "FTSE 100 Daily": "IX.D.FTSE.DAILY.IP",
            "S&P 500": "IX.D.SPTRD.DAILY.IP",
            "Germany 40 Daily": "IX.D.DAX.DAILY.IP",
            "Wall Street Daily": "IX.D.DOW.DAILY.IP",
            "UK 100 Cash": "IX.D.FTSE.CASH.IP",
            "France 40 Daily": "IX.D.CAC.DAILY.IP"
        }
    
    def load_env(self):
        """Load environment variables from .env file"""
        env_path = Path(__file__).parent / '.env'
        
        if not env_path.exists():
            print(f"Warning: .env file not found at {env_path}")
            return
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    
    def get_credentials(self, account_type):
        """Get credentials for specified account type"""
        if account_type == "DEMO":
            return {
                'username': self.demo_username,
                'password': self.demo_password,
                'api_key': self.demo_api_key,
                'base_url': self.demo_url
            }
        else:
            return {
                'username': self.live_username,
                'password': self.live_password,
                'api_key': self.live_api_key,
                'base_url': self.live_url
            }
    
    def has_credentials(self, account_type):
        """Check if credentials exist for account type"""
        creds = self.get_credentials(account_type)
        return all([creds['username'], creds['password'], creds['api_key']])