# This file contains the laddering logic.
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
