#!/usr/bin/env python
"""
Run the portfolio strategy on a price panel and print its statistics.

Usage
-----
python scripts/run_portfolio.py --panel data/panel_31.parquet                     # final system (S6/7)
python scripts/run_portfolio.py --panel data/panel_31.parquet --trend-mode none   # risk-scaled portfolio (S4)
python scripts/run_portfolio.py --panel data/panel_31.parquet --target-vol 0.4 --out results/s67_40.csv --plot
"""
import argparse
import json
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config.base import TRANSACTION_COST  # noqa: E402
from lib.strat.portfolio_risk_scaled_strategy import PortfolioRiskScaledStrategy  # noqa: E402
from lib.backtester.backtester import backtest_multi_asset  # noqa: E402
from lib.metrics import windows, distribution  # noqa: E402

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--panel", default="data/panel_31.parquet")
    p.add_argument("--trend-mode", default="strength", choices=["none", "strength"])
    p.add_argument("--target-vol", type=float, default=0.2)
    p.add_argument("--out", default="results/portfolio.csv")
    p.add_argument("--plot", action="store_true")
    a = p.parse_args()

    px = pd.read_parquet(a.panel)
    sig = PortfolioRiskScaledStrategy(trend_mode=a.trend_mode, target_vol=a.target_vol).generate_signals(px)
    r, _ = backtest_multi_asset(px, sig, TRANSACTION_COST)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    pd.DataFrame({"portfolio_return": r, "equity_curve": (1 + r).cumprod()}).to_csv(a.out, index_label="Date")
    print(json.dumps({"windows": windows(r), "distribution": distribution(r)}, indent=1,
                     default=lambda x: round(float(x), 4)))
    if a.plot:
        import matplotlib.pyplot as plt
        (1 + r).cumprod().plot(logy=True, title="Equity curve (log scale)", figsize=(12, 5))
        plt.tight_layout(); plt.savefig(a.out.replace(".csv", "_equity.png"), dpi=150)
    print(f"[ok] {a.out}")
