# gui.py
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
import logging

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
        self.main_frame = ttk.Frame(self.master, padding="10")
        self.main_frame.pack(fill="both", expand=True)
        
        # Log Panel
        self.log_frame = ttk.LabelFrame(self.main_frame, text="Log", padding="5")
        self.log_frame.pack(fill="both", expand=True, pady=(0, 10))
        self.log_text = ScrolledText(self.log_frame, state="disabled", height=15, wrap="word")
        self.log_text.pack(fill="both", expand=True)
        
        # Controls Panel
        self.controls_frame = ttk.LabelFrame(self.main_frame, text="Controls", padding="5")
        self.controls_frame.pack(fill="x", pady=(0, 10))

        # Login/Logout and Status
        self.login_frame = ttk.Frame(self.controls_frame)
        self.login_frame.pack(fill="x", pady=(0, 5))
        self.login_btn = ttk.Button(self.login_frame, text="Login", command=self._login)
        self.login_btn.pack(side="left", padx=(0, 5))
        self.status_var = tk.StringVar(value="Status: Not Logged In")
        self.status_label = ttk.Label(self.login_frame, textvariable=self.status_var)
        self.status_label.pack(side="left", fill="x", expand=True)

        # Trading Buttons
        self.trading_buttons_frame = ttk.Frame(self.controls_frame)
        self.trading_buttons_frame.pack(fill="x", pady=5)
        self.start_btn = ttk.Button(self.trading_buttons_frame, text="Start Trading", command=self._start_trading, state="disabled")
        self.start_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.stop_btn = ttk.Button(self.trading_buttons_frame, text="Stop Trading", command=self._stop_trading, state="disabled")
        self.stop_btn.pack(side="left", fill="x", expand=True)

        # Other Controls
        self.other_controls_frame = ttk.Frame(self.controls_frame)
        self.other_controls_frame.pack(fill="x", pady=5)
        self.cancel_all_btn = ttk.Button(self.other_controls_frame, text="Cancel All Orders", command=self._cancel_all, state="disabled")
        self.cancel_all_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.epic_label = ttk.Label(self.other_controls_frame, text="Epic:")
        self.epic_label.pack(side="left", padx=(0, 5))
        self.epic_entry = ttk.Entry(self.other_controls_frame)
        self.epic_entry.pack(side="left", fill="x", expand=True)
        
    def _login(self):
        self._log("Attempting to log in...")
        if self.bot.authenticate():
            self.logged_in = True
            self.status_var.set("Status: Logged In")
            self.login_btn.config(text="Logout", command=self._logout)
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.cancel_all_btn.config(state="normal")
        else:
            self._log("Login failed.")

    def _logout(self):
        self._log("Logging out...")
        self.bot.logout()
        self.logged_in = False
        self.status_var.set("Status: Not Logged In")
        self.login_btn.config(text="Login", command=self._login)
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.cancel_all_btn.config(state="disabled")
        
    def _start_trading(self):
        if not self.is_trading:
            self._log("Starting trading logic...")
            self.is_trading = True
            self.trade_thread = threading.Thread(target=self._run_trading_logic, daemon=True)
            self.trade_thread.start()
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")

    def _stop_trading(self):
        if self.is_trading:
            self._log("Stopping trading logic...")
            self.is_trading = False
            if self.trade_thread and self.trade_thread.is_alive():
                # We can't directly kill a thread, but this will let the loop finish
                # and exit naturally.
                pass
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
        
    def _run_trading_logic(self):
        # Placeholder for the main trading loop
        while self.is_trading:
            self._log("Trading logic loop running...")
            time.sleep(5)
        self._log("Trading logic stopped.")

    def _cancel_all(self):
        epic = self.epic_entry.get()
        if epic:
            self._log(f"Cancelling all orders for epic: {epic}")
            cancelled_count = self.bot.om.cancel_all_for_epic(epic)
            self._log(f"Cancelled {cancelled_count} working orders for {epic}.")
        else:
            messagebox.showerror("Error", "Please enter an Epic ID to cancel orders.")
            
    def _log(self, msg):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
