"""
IG Trading Bot - Main Entry Point
Modular trading bot for IG Markets
"""
from config import Config
from api.ig_client import IGClient
from trading import risk_manager
from trading.auto_strategy import AutoStrategy  
from trading.ladder_strategy import LadderStrategy
from trading.risk_manager import RiskManager  # Add this import
from ui.main_window import MainWindow

def main():
    """Main entry point"""
    # Initialize components
    config = Config()
    ig_client = IGClient()
    ladder_strategy = LadderStrategy(ig_client)
    auto_strategy = AutoStrategy(ig_client, ladder_strategy) 
    risk_manager = RiskManager(ig_client)  # Initialize RiskManager
    
    # Create and run GUI
    window = MainWindow(config, ig_client, ladder_strategy, auto_strategy, risk_manager)
    window.run()

if __name__ == "__main__":
    main()