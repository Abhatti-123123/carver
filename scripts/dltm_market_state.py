#!/usr/bin/env python
"""
Does market-wide long memory predict the futures book's left tail?

State = average walk-forward d* (dLTM) across S&P 500 stocks each day. Headline definition: the state
minus its trailing 1-year mean (removes the slow upward drift), bucketed into terciles using only
history available at the time. Robustness: raw state with expanding terciles and with rolling 3-year
terciles. For each month-end state, report the next month of the final system's daily returns, then
test a rule: halve the book the day after the state is in its top tercile.

Usage
-----
python scripts/dltm_market_state.py --dltm <folder with series_14y_est_n2800/> --panel data/panel_31.parquet
"""
import argparse
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config.base import TRANSACTION_COST  # noqa: E402
from lib.strat.portfolio_risk_scaled_strategy import PortfolioRiskScaledStrategy  # noqa: E402
from lib.backtester.backtester import backtest_multi_asset  # noqa: E402
from lib.metrics import perf  # noqa: E402

COVID = ("2020-02-15", "2020-04-30")


def terciles(x, window=None, min_periods=252):
    roll = x.expanding(min_periods) if window is None else x.rolling(window, min_periods=min_periods)
    lo, hi = roll.quantile(1 / 3).shift(1), roll.quantile(2 / 3).shift(1)
    b = pd.Series(np.where(x > hi, "high", np.where(x < lo, "low", "mid")), index=x.index)
    return b[hi.notna()]


def next_month(r, buckets):
    me = buckets.resample("ME").last()
    out = {}
    for b in ("low", "mid", "high"):
        chunks = [r.loc[m + pd.Timedelta(days=1): m + pd.offsets.MonthEnd(1)] for m in me.index[me == b]]
        days = pd.concat(chunks)
        months = pd.Series([(1 + c).prod() - 1 for c in chunks if len(c)])
        out[b] = {"months": len(chunks), "skew": st.skew(days), "worst_month": months.min(),
                  "sharpe": days.mean() / days.std() * np.sqrt(252)}
    return out


def derisk(r, buckets):
    k = pd.Series(np.where(buckets == "high", 0.5, 1.0), index=buckets.index).shift(1).fillna(1.0)
    r = r.loc[k.index]
    return {name: dict(perf(x), skew=st.skew(x)) for name, x in (("as_is", r), ("derisked", r * k))}


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dltm", required=True)
    p.add_argument("--panel", default="data/panel_31.parquet")
    p.add_argument("--out", default="results/dltm_market_state.json")
    a = p.parse_args()
    files = glob.glob(os.path.join(a.dltm, "series_14y_est_n2800", "*_n2800_series.parquet"))
    state = pd.concat({Path(f).name.split("_n2800")[0]: pd.read_parquet(f)["dstar"] for f in files}, axis=1)
    state = state.mean(axis=1).dropna()

    px = pd.read_parquet(a.panel)
    r, _ = backtest_multi_asset(px, PortfolioRiskScaledStrategy().generate_signals(px), TRANSACTION_COST)
    state = state.reindex(r.index).ffill().loc[state.index[0]:]
    definitions = {"detrended": terciles((state - state.rolling(252).mean()).dropna()),
                   "expanding": terciles(state), "rolling_3y": terciles(state, window=756)}
    no_covid = ~r.index.isin(r.loc[COVID[0]:COVID[1]].index)
    out = {"stocks": len(files), "state_live_from": str(state.index[0].date())}
    for name, b in definitions.items():
        out[name] = {"window": f"{b.index[0].date()} -> {b.index[-1].date()}",
                     "next_month": next_month(r, b),
                     "next_month_ex_covid": next_month(r[no_covid], b[b.index.isin(r.index[no_covid])]),
                     "rule": derisk(r, b)}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    for name in definitions:
        nm, ru = out[name]["next_month"], out[name]["rule"]
        print(f"{name:10s} skew low/mid/high {nm['low']['skew']:+.2f} / {nm['mid']['skew']:+.2f} / {nm['high']['skew']:+.2f}"
              f" | rule Sharpe {ru['as_is']['sharpe']:.2f} -> {ru['derisked']['sharpe']:.2f},"
              f" MDD {ru['as_is']['mdd']:.1%} -> {ru['derisked']['mdd']:.1%}")
