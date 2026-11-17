"""All tunable settings in one place. Nothing here touches real money."""
from dataclasses import dataclass


@dataclass
class Config:
    # --- instrument (verify lot size from the exchange before real use) ---
    lot_size: int = 75
    # round-trip cost + slippage, in index points (brokerage, STT, charges, spread)
    cost_points: float = 4.0

    # --- opening range breakout ---
    or_end: str = "09:30"          # opening range = bars before this time
    last_entry: str = "14:30"
    force_exit: str = "15:15"
    breakout_buffer: float = 2.0   # points beyond OR to confirm breakout
    rr: float = 1.5                # target = rr * risk
    min_risk: float = 15.0         # skip if stop is too tight (noise)
    max_risk: float = 80.0         # skip if stop is too wide (bad R:R)

    # --- day filter ("aaj trade karna hai ya nahi") ---
    use_day_filter: bool = True
    or_hist_days: int = 10
    min_or_ratio: float = 0.7      # today's OR must be >= 0.7x recent average
    max_or_ratio: float = 2.0      # ...and <= 2x (avoid chaos days)
    max_gap_pct: float = 1.0       # skip huge gap days
    max_vix: float = 25.0          # used only if a 'vix' column exists
