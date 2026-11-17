"""Usage:
  python run_backtest.py --demo                     # synthetic data, code check only
  python run_backtest.py --csv data/nifty_5m.csv    # your real data
"""
import argparse, json
from dataclasses import replace

from app.backtest import metrics, run_backtest
from app.config import Config
from app.data import load_csv, resample, synthetic, validate

p = argparse.ArgumentParser()
p.add_argument("--csv"); p.add_argument("--demo", action="store_true")
p.add_argument("--tf", default="5min")
a = p.parse_args()

if a.demo:
    df = synthetic(); print("!! SYNTHETIC random data: results are meaningless, this only tests the code.\n")
elif a.csv:
    df = resample(load_csv(a.csv), a.tf)
else:
    raise SystemExit("give --csv FILE or --demo")

issues = validate(df)
if issues:
    raise SystemExit(f"Bad data, refusing to backtest: {issues}")

base = Config()
for name, cfg in [("WITH day filter", base), ("WITHOUT day filter", replace(base, use_day_filter=False))]:
    trades, skipped = run_backtest(df, cfg)
    print(f"=== {name} ===")
    print(json.dumps(metrics(trades), indent=2, default=str))
    print("skip reasons:", skipped["reason"].str.replace(r"\(.*\)", "", regex=True).value_counts().to_dict(), "\n")
