#!/usr/bin/env python
"""
Robustness check: the risk-scaled portfolio (S4) on liquid crypto, with the futures parameters unchanged.

Usage
-----
python scripts/build_panel.py --universe crypto --start 2023-01-01 --end 2025-11-28 --out data/panel_crypto.parquet
python scripts/crypto_run.py --panel data/panel_crypto.parquet
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config.base import TRANSACTION_COST  # noqa: E402
from lib.loaders import clean_panel  # noqa: E402
from lib.strat.portfolio_risk_scaled_strategy import PortfolioRiskScaledStrategy  # noqa: E402
from lib.backtester.backtester import backtest_multi_asset  # noqa: E402
from lib.metrics import perf, distribution  # noqa: E402

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--panel", default="data/panel_crypto.parquet")
    a = p.parse_args()
    px = clean_panel(pd.read_parquet(a.panel))
    r, _ = backtest_multi_asset(px, PortfolioRiskScaledStrategy(trend_mode="none").generate_signals(px), TRANSACTION_COST)
    d = distribution(r)
    print(f"{px.shape[1]} coins, {px.index[0].date()} -> {px.index[-1].date()}")
    print(json.dumps(dict(perf(r), sortino=d["sortino"], tail_ratio=d["tail_ratio"]), indent=1,
                     default=lambda x: round(float(x), 4)))
