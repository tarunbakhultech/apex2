from .config import Config


def day_ok(cfg: Config, or_range: float, or_hist: list[float], gap_pct: float, vix=None):
    """Decide whether today is tradeable. Returns (ok, reason). Uses only info known at 09:30."""
    if not cfg.use_day_filter:
        return True, "filter off"
    if len(or_hist) < 3:
        return False, "not enough history"
    recent = or_hist[-cfg.or_hist_days:]
    avg = sum(recent) / len(recent)
    ratio = or_range / avg if avg else 0
    if ratio < cfg.min_or_ratio:
        return False, f"opening range too small ({ratio:.2f}x avg)"
    if ratio > cfg.max_or_ratio:
        return False, f"opening range too wild ({ratio:.2f}x avg)"
    if abs(gap_pct) > cfg.max_gap_pct:
        return False, f"gap too large ({gap_pct:.2f}%)"
    if vix is not None and vix > cfg.max_vix:
        return False, f"VIX too high ({vix:.1f})"
    return True, "ok"
