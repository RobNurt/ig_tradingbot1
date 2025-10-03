"""
Auto Trading Strategy
Manages automatic ladder adjustment and trailing stop management
"""
import time
import threading

class AutoStrategy:
    """Automated ladder management with trailing stops"""
    
    def __init__(self, ig_client, ladder_strategy):
        self.ig_client = ig_client
        self.ladder_strategy = ladder_strategy
        self.running = False
        self.monitor_thread = None
        
        # Configuration
        self.check_interval = 30
        self.adjustment_threshold = 10
        self.trailing_stop_distance = 20
        self.max_spread = 5
        
        # State tracking
        self.last_price = None
        self.current_ladder_base = None
        
    def start(self, epic, direction, start_offset, step_size, num_orders, 
             order_size, retry_jump, max_retries, log_callback):
        """Start the auto strategy"""
        if self.running:
            log_callback("Auto strategy already running")
            return
        
        self.running = True
        self.epic = epic
        self.direction = direction
        self.start_offset = start_offset
        self.step_size = step_size
        self.num_orders = num_orders
        self.order_size = order_size
        self.retry_jump = retry_jump
        self.max_retries = max_retries
        self.log_callback = log_callback
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        log_callback(f"Auto strategy started - monitoring every {self.check_interval}s")
    
    def stop(self):
        """Stop the auto strategy"""
        self.running = False
        if self.log_callback:
            self.log_callback("Auto strategy stopped")