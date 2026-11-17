# APEX 2 (fresh start)

Paper-only research + backtest system for Indian index scalping. **It cannot place real orders.**

## Phase 1 (this repo now)
- Opening Range Breakout (ORB) backtester on index points
- Day filter ("aaj trade karna hai ya nahi"), with/without comparison
- Costs + slippage, next-bar entry, SL-first on ambiguous bars, skip reasons logged
- FastAPI `/health`, `/config`, `/backtest/demo`; optional MongoDB logging

## Run locally
    pip install -r requirements.txt
    python run_backtest.py --demo                 # synthetic data, code check only
    python run_backtest.py --csv data/nifty_5m.csv
    pytest
    uvicorn app.api:app --reload

CSV columns: timestamp, open, high, low, close (optional: volume, vix). 1-min or 5-min NIFTY/BANKNIFTY, 1-2 years.
Set `lot_size` and `cost_points` in `app/config.py` (verify the current lot size from NSE).

## Deploy (all free)
1. GitHub: `git init && git add . && git commit -m "apex2" && git remote add origin <your repo> && git push -u origin main`
2. MongoDB Atlas: create a free M0 cluster, create a DB user, allow network access, copy the connection string.
3. Render: New > Blueprint > pick the repo (uses `render.yaml`). Add `MONGODB_URI` in the dashboard (never in git).
4. Open `<render-url>/health` - it should say `PAPER_ONLY`.

Render free sleeps after ~15 min idle, so a live scanner needs an external trigger (e.g. GitHub Actions cron) - Phase 2.

## Roadmap
1. Real data + honest backtest (compare filter on/off, parameter sweep, out-of-sample split)
2. Option-premium modelling (theta/IV/spread) - current results are an upper bound
3. Paper scanner with decision + rejection logging, daily report
4. Dashboard
5. Live only after 100+ paper trades with positive expectancy after costs
