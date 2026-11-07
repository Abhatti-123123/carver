#!/usr/bin/env python
"""
How the final settings were chosen: compare variants on 2006-2016 only, then check 2017-2025.

Grid: covariance windows x scale-factor smoothing for the risk-scaled portfolio (S4), and long-only vs
long/short x forecast scalar for trend-strength sizing (S6/7). Scored from 2006 so the longest
covariance warm-up does not bias the comparison.

Usage
-----
python scripts/select_settings.py --panel data/panel_31.parquet --out results/select_settings.csv
"""
import argparse
import itertools
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

SRC = str(Path(__file__).resolve().parents[1] / "src")
sys.path.insert(0, SRC)
from config.base import TRANSACTION_COST  # noqa: E402

START, IS_END, OOS_START = "2006-01-01", "2016-12-31", "2017-01-01"
S4_GRID = [dict(trend_mode="none", short_lookback=s, long_lookback=l, scale_halflife=h)
           for (s, l), h in itertools.product([(20, 60), (60, 120), (60, 250), (120, 250)], [None, 20, 60])]
S67_GRID = [dict(trend_mode="strength", short_lookback=s, long_lookback=l, scale_halflife=h, long_only=lo,
                 forecast_scalar=k)
            for (s, l, h), lo, k in itertools.product([(20, 60, None), (60, 120, 20)], [False, True], [1.0, 1.9])]


def run_one(args):
    panel, params = args
    sys.path.insert(0, SRC)
    from lib.strat.portfolio_risk_scaled_strategy import PortfolioRiskScaledStrategy
    from lib.backtester.backtester import backtest_multi_asset
    from lib.metrics import perf
    px = pd.read_parquet(panel)
    r, _ = backtest_multi_asset(px, PortfolioRiskScaledStrategy(**params).generate_signals(px), TRANSACTION_COST)
    r = r.loc[START:]
    return dict(params, **{f"{tag}_{k}": v for tag, part in (("is", r.loc[:IS_END]), ("oos", r.loc[OOS_START:]),
                                                            ("full", r))
                          for k, v in perf(part).items()})


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--panel", default="data/panel_31.parquet")
    p.add_argument("--out", default="results/select_settings.csv")
    a = p.parse_args()
    grid = S4_GRID + S67_GRID
    with ProcessPoolExecutor(max_workers=min(len(grid), os.cpu_count() or 4)) as ex:
        rows = list(ex.map(run_one, [(a.panel, g) for g in grid]))
    out = pd.DataFrame(rows).sort_values(["trend_mode", "is_sharpe"], ascending=[True, False])
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    out.to_csv(a.out, index=False)
    print(out[["trend_mode", "short_lookback", "long_lookback", "scale_halflife", "long_only", "forecast_scalar",
               "is_sharpe", "oos_sharpe", "full_sharpe"]].round(3).to_string(index=False))
