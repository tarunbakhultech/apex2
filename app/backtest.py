"""Opening Range Breakout backtester on index points.

Honesty rules baked in:
- Signal on bar close, entry at NEXT bar's open (no look-ahead).
- If SL and target both fall inside one bar, assume SL hit first (conservative).
- Costs/slippage charged on every trade.
- One trade per day. Every skipped day gets a logged reason.
NOTE: this tests the *underlying index*. Real option premium P&L (theta, IV,
spread) is NOT modelled yet, so treat results as an upper bound.
"""
import pandas as pd

from .config import Config
from .day_filter import day_ok


def _t(s: str):
    return pd.Timestamp(s).time()


def run_backtest(df: pd.DataFrame, cfg: Config):
    or_end, last_entry, force_exit = _t(cfg.or_end), _t(cfg.last_entry), _t(cfg.force_exit)
    trades, skipped, or_hist = [], [], []
    prev_close = None

    for day, bars in df.groupby(df.index.date):
        bars = bars.sort_index()
        times = bars.index.time
        or_bars = bars[[t < or_end for t in times]]
        if len(or_bars) < 2:
            skipped.append((day, "incomplete opening range"))
            prev_close = bars["close"].iloc[-1]
            continue
        or_high, or_low = or_bars["high"].max(), or_bars["low"].min()
        or_range = or_high - or_low
        gap = 0.0 if prev_close is None else (bars["open"].iloc[0] - prev_close) / prev_close * 100
        vix = bars["vix"].iloc[0] if "vix" in bars.columns else None

        ok, reason = day_ok(cfg, or_range, or_hist, gap, vix)
        or_hist.append(or_range)
        prev_close = bars["close"].iloc[-1]
        if not ok:
            skipped.append((day, reason))
            continue

        post = bars[[t >= or_end for t in times]]
        entered = False
        for i in range(len(post) - 1):
            bar = post.iloc[i]
            if post.index[i].time() > last_entry:
                break
            if bar["close"] > or_high + cfg.breakout_buffer:
                side, sl = 1, or_low
            elif bar["close"] < or_low - cfg.breakout_buffer:
                side, sl = -1, or_high
            else:
                continue
            entry = post.iloc[i + 1]["open"]            # next bar open
            risk = (entry - sl) if side == 1 else (sl - entry)
            if risk < cfg.min_risk:
                skipped.append((day, f"stop too tight ({risk:.0f} pts)")); entered = True; break
            if risk > cfg.max_risk:
                skipped.append((day, f"stop too wide ({risk:.0f} pts)")); entered = True; break
            target = entry + side * cfg.rr * risk
            exit_px, exit_reason, exit_time = None, None, None
            for j in range(i + 1, len(post)):
                b = post.iloc[j]
                hit_sl = b["low"] <= sl if side == 1 else b["high"] >= sl
                hit_tg = b["high"] >= target if side == 1 else b["low"] <= target
                if hit_sl:                                  # SL first if both
                    exit_px, exit_reason, exit_time = sl, "SL", post.index[j]; break
                if hit_tg:
                    exit_px, exit_reason, exit_time = target, "TARGET", post.index[j]; break
                if post.index[j].time() >= force_exit:
                    exit_px, exit_reason, exit_time = b["close"], "TIME", post.index[j]; break
            if exit_px is None:
                b = post.iloc[-1]; exit_px, exit_reason, exit_time = b["close"], "TIME", post.index[-1]
            pts = side * (exit_px - entry) - cfg.cost_points
            trades.append({
                "date": day, "side": "LONG" if side == 1 else "SHORT",
                "entry_time": post.index[i + 1], "entry": entry, "sl": sl, "target": target,
                "exit_time": exit_time, "exit": exit_px, "reason": exit_reason,
                "risk_pts": risk, "pnl_pts": pts, "pnl_rs": pts * cfg.lot_size,
            })
            entered = True
            break
        if not entered:
            skipped.append((day, "no breakout signal"))

    return pd.DataFrame(trades), pd.DataFrame(skipped, columns=["date", "reason"])


def metrics(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"trades": 0}
    pnl = trades["pnl_rs"]
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    equity = pnl.cumsum()
    dd = (equity - equity.cummax()).min()
    monthly = trades.assign(m=pd.to_datetime(trades["date"]).dt.to_period("M").astype(str)).groupby("m")["pnl_rs"].sum()
    return {
        "trades": int(len(trades)),
        "win_rate_pct": round(len(wins) / len(trades) * 100, 1),
        "profit_factor": round(wins.sum() / abs(losses.sum()), 2) if losses.sum() != 0 else None,
        "expectancy_rs": round(pnl.mean(), 1),
        "avg_win_rs": round(wins.mean(), 1) if len(wins) else 0,
        "avg_loss_rs": round(losses.mean(), 1) if len(losses) else 0,
        "net_pnl_rs": round(pnl.sum(), 1),
        "max_drawdown_rs": round(dd, 1),
        "monthly_pnl_rs": {k: round(v, 1) for k, v in monthly.items()},
        "enough_trades_to_judge": bool(len(trades) >= 100),
    }
