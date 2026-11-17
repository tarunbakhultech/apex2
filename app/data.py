import numpy as np
import pandas as pd


def load_csv(path: str) -> pd.DataFrame:
    """CSV with columns: timestamp/datetime, open, high, low, close[, volume, vix]."""
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    ts = "timestamp" if "timestamp" in df.columns else "datetime"
    df[ts] = pd.to_datetime(df[ts])
    df = df.set_index(ts).sort_index()
    df = df[~df.index.duplicated(keep="first")]
    return df


def resample(df: pd.DataFrame, rule: str = "5min") -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    if "volume" in df.columns:
        agg["volume"] = "sum"
    if "vix" in df.columns:
        agg["vix"] = "last"
    return df.resample(rule).agg(agg).dropna(subset=["open", "close"])


def validate(df: pd.DataFrame) -> list[str]:
    """Return a list of data problems. Never trade/backtest on bad data."""
    issues = []
    if df.empty:
        return ["empty data"]
    if (df["high"] < df[["open", "close"]].max(axis=1)).any():
        issues.append("high below open/close on some bars")
    if (df["low"] > df[["open", "close"]].min(axis=1)).any():
        issues.append("low above open/close on some bars")
    if df[["open", "high", "low", "close"]].isna().any().any():
        issues.append("NaN prices")
    return issues


def synthetic(days: int = 120, seed: int = 7, start: float = 22000.0) -> pd.DataFrame:
    """RANDOM-WALK data for testing the code only. Results on it mean NOTHING."""
    rng = np.random.default_rng(seed)
    rows, price = [], start
    for d in pd.bdate_range("2025-01-01", periods=days):
        price *= 1 + rng.normal(0, 0.003)  # overnight gap
        for i in range(75):  # 09:15 -> 15:30, 5-min bars
            ts = d + pd.Timedelta(hours=9, minutes=15 + 5 * i)
            o = price
            c = o * (1 + rng.normal(0, 0.0007))
            h = max(o, c) + abs(rng.normal(0, 0.0003)) * o
            l = min(o, c) - abs(rng.normal(0, 0.0003)) * o
            rows.append((ts, o, h, l, c))
            price = c
    return pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close"]).set_index("timestamp")
