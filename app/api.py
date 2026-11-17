import os
from dataclasses import asdict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .backtest import metrics, run_backtest
from .config import Config
from .data import synthetic
from .storage import save_run

app = FastAPI(title="APEX 2")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o],
    allow_methods=["*"], allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "PAPER_ONLY",
        "live_orders": False,          # hard-coded: this build cannot place real orders
        "mongo_configured": bool(os.getenv("MONGODB_URI")),
        "data_provider": os.getenv("MARKET_DATA_PROVIDER", "none (CSV backtest only)"),
    }


@app.get("/config")
def config():
    return asdict(Config())


@app.get("/backtest/demo")
def backtest_demo(use_day_filter: bool = True):
    """SYNTHETIC data. Proves the pipeline runs; says nothing about profitability."""
    cfg = Config(use_day_filter=use_day_filter)
    trades, skipped = run_backtest(synthetic(), cfg)
    result = {"warning": "synthetic random data - meaningless results", "metrics": metrics(trades)}
    result["saved_to_mongo"] = save_run("backtest_demo", {"metrics": result["metrics"]})
    return result
