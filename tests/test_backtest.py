import pandas as pd
from app.backtest import run_backtest, metrics
from app.config import Config
from app.data import synthetic, validate


def _day(prices):
    idx = pd.date_range("2025-03-03 09:15", periods=len(prices), freq="5min")
    return pd.DataFrame(prices, columns=["open", "high", "low", "close"], index=idx)


def test_synthetic_data_valid():
    assert validate(synthetic(5)) == []


def test_entry_is_next_bar_open_and_sl_first():
    cfg = Config(use_day_filter=False, min_risk=1, max_risk=1000, breakout_buffer=0, cost_points=0)
    # OR (3 bars) high 100 low 90. Bar 4 (09:30) closes 105 -> signal. Bar 5 opens 106 = entry.
    # Bar 5 range spans both SL (90) and target -> must count as SL.
    rows = [(95, 100, 90, 95)] * 3 + [(96, 106, 95, 105), (106, 200, 80, 150)] + [(150, 150, 150, 150)] * 10
    trades, _ = run_backtest(_day(rows), cfg)
    t = trades.iloc[0]
    assert t["entry"] == 106 and t["reason"] == "SL" and t["pnl_pts"] == (90 - 106)


def test_costs_reduce_pnl():
    df = synthetic(60)
    a, _ = run_backtest(df, Config(use_day_filter=False, cost_points=0))
    b, _ = run_backtest(df, Config(use_day_filter=False, cost_points=10))
    assert metrics(b)["net_pnl_rs"] < metrics(a)["net_pnl_rs"]


def test_api_health_never_live():
    from fastapi.testclient import TestClient
    from app.api import app
    r = TestClient(app).get("/health").json()
    assert r["live_orders"] is False
