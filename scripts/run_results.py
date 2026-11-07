#!/usr/bin/env python
"""
Every futures number in the presentation.

  ladder     S1-S3 (single-market strategies, averaged over markets), S4 risk-scaled portfolio, S6/7 final system
  alpha      S6/7 regressed on S4 (2005-25 and since 2020)
  dial       final system at 20% / 40% / 60% vol target
  universes  final system on 21, 31, 35-with-bonds and 35-without-bonds markets
  detail     distribution, calendar years and crisis episodes of the final system

Usage
-----
python scripts/run_results.py --data data --out results/final.json
"""
import argparse
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

SRC = str(Path(__file__).resolve().parents[1] / "src")
sys.path.insert(0, SRC)
from config.base import TRANSACTION_COST as TC  # noqa: E402
from lib.metrics import perf, windows, distribution, alpha  # noqa: E402

EPISODES = {"gfc": ("2008-01-01", "2009-03-31"), "euro_crisis": ("2011-07-01", "2011-12-31"),
            "commodity_bust": ("2014-07-01", "2016-02-29"), "covid_crash": ("2020-02-15", "2020-04-30"),
            "reflation_2021": ("2021-01-01", "2021-12-31"), "rate_hikes_2022": ("2022-01-01", "2022-12-31")}


def run(args):
    name, panel, params = args
    sys.path.insert(0, SRC)
    from lib.strat.portfolio_risk_scaled_strategy import PortfolioRiskScaledStrategy
    from lib.backtester.backtester import backtest_multi_asset
    px = pd.read_parquet(panel)
    r, per_market = backtest_multi_asset(px, PortfolioRiskScaledStrategy(**params).generate_signals(px), TC)
    return name, r, per_market


def single_market(kind, panel):
    """S1-S3 are single-market strategies: report the average market."""
    sys.path.insert(0, SRC)
    from lib import STRATEGY_REGISTRY
    from lib.backtester.backtester import compute_strategy_returns
    px = pd.read_parquet(panel)
    rows = []
    for c in px.columns:
        sig = STRATEGY_REGISTRY[kind]().generate_signals(px[c]).astype(float)
        r = compute_strategy_returns(px[c], sig, TC).fillna(0.0)
        rows.append(perf(r.loc[r.ne(0).idxmax():]))
    return kind, pd.DataFrame(rows).mean().to_dict()


def diversification(per_market):
    sr = per_market.mean() / per_market.std() * np.sqrt(252)
    share = per_market.std() / per_market.std().sum()
    c = per_market.corr().values
    n = c.shape[0]
    avg_sr = float((sr * share).sum())
    return {"markets": n, "avg_correlation": (np.nansum(c) - n) / (n * (n - 1)), "avg_market_sharpe": avg_sr,
            "effective_bets": float(1 / (share ** 2).sum()),
            "diversification_gain": perf(per_market.sum(axis=1))["sharpe"] / avg_sr}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data")
    p.add_argument("--out", default="results/final.json")
    a = p.parse_args()
    P = lambda u: os.path.join(a.data, f"panel_{u}.parquet")
    jobs = [("S4", P("31"), dict(trend_mode="none")), ("final", P("31"), {}),
            ("final_t40", P("31"), dict(target_vol=0.4)), ("final_t60", P("31"), dict(target_vol=0.6)),
            ("u21", P("21"), {}), ("u35_bonds", P("35_bonds"), {}), ("u35_nobonds", P("35_nobonds"), {})]
    with ProcessPoolExecutor(max_workers=len(jobs) + 3) as ex:
        singles = [ex.submit(single_market, k, P("31")) for k in ("buy_and_hold", "risk_scaled", "variable_risk_scaled")]
        res = {n: (r, pm) for n, r, pm in ex.map(run, jobs)}
        singles = dict(f.result() for f in singles)
    R = {n: r for n, (r, _) in res.items()}
    final = R["final"]
    out = {
        "ladder": {"S1": singles["buy_and_hold"], "S2": singles["risk_scaled"], "S3": singles["variable_risk_scaled"],
                   "S4": windows(R["S4"]), "S6/7": windows(final)},
        "alpha_S67_vs_S4": {"2005-25": alpha(final, R["S4"]), "since_2020": alpha(final.loc["2020":], R["S4"].loc["2020":])},
        "vol_target_dial": {"20%": perf(final), "40%": perf(R["final_t40"]), "60%": perf(R["final_t60"])},
        "universes": {u: dict(diversification(res[n][1]), **windows(R[n]))
                      for u, n in (("21", "u21"), ("31", "final"), ("35_bonds", "u35_bonds"),
                                   ("35_nobonds", "u35_nobonds"))},
        "detail": dict(distribution(final),
                       calendar_years=((1 + final).groupby(final.index.year).prod() - 1).round(4).to_dict(),
                       episodes={k: float((1 + final.loc[s:e]).prod() - 1) for k, (s, e) in EPISODES.items()}),
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps({k: out[k] for k in ("ladder", "alpha_S67_vs_S4")}, indent=1, default=lambda x: round(float(x), 3)))
