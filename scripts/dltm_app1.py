#!/usr/bin/env python
"""
dLTM extension: size the final system by each stock's long-memory regime.

Universe: sector-balanced 30-name S&P 500 set (3 names x 10 sectors; 15+ years of history and 50%+ dLTM
coverage; the sector with fewest eligible names is dropped, ties broken by coverage, history, ticker).
Overlay: position x1.5 when the walk-forward d* >= 0.7, x0.5 when d* < 0.3, unchanged otherwise.
Because high-d names far outnumber low-d ones the overlay adds leverage, so a leverage-neutral tilt
(multipliers rescaled to average 1 across names each day) is reported alongside it.
Test: Diebold-Mariano on the daily return differential, Newey-West bandwidth 21.

Inputs (--dltm folder): log_prices_sp500_2010_2025.parquet, gics_map.json, series_14y_est_n2800/<TICKER>_n2800_series.parquet

Usage
-----
python scripts/dltm_app1.py --dltm <dltm folder> --out results/dltm.json
"""
import argparse
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

D_LOW, D_HIGH, UP, DOWN = 0.3, 0.7, 1.5, 0.5
REGIMES = {"post_gfc_2011": ("2011-02-17", "2011-12-31"), "bull_2013_14": ("2013-01-01", "2014-12-31"),
           "q4_2018": ("2018-10-01", "2018-12-24"), "late_cycle_2019": ("2019-01-01", "2019-12-31"),
           "covid_crash": ("2020-02-19", "2020-03-23"), "covid_recovery": ("2020-03-24", "2021-12-31"),
           "rate_hikes_2022": ("2022-01-01", "2022-10-12"), "ai_rally_2023_24": ("2023-01-01", "2024-12-31")}


def series_path(dltm, t):
    return os.path.join(dltm, "series_14y_est_n2800", f"{t}_n2800_series.parquet")


def pick_universe(dltm, logpx):
    gics = json.load(open(os.path.join(dltm, "gics_map.json")))
    rows = [{"ticker": t, "sector": sec, "years": (logpx.index[-1] - logpx[t].first_valid_index()).days / 365.25,
             "cov": pd.read_parquet(series_path(dltm, t))["dstar"].notna().mean()}
            for t, sec in gics.items() if t in logpx.columns and os.path.exists(series_path(dltm, t))]
    df = pd.DataFrame(rows)
    df = df[(df.years >= 15) & (df["cov"] >= 0.5)]
    df = df[df.sector.isin(df.sector.value_counts().index[:10])]
    return (df.sort_values(["sector", "cov", "years", "ticker"], ascending=[True, False, False, True])
            .groupby("sector").head(3).reset_index(drop=True))


def sharpe(r):
    return float(r.mean() / r.std() * np.sqrt(252))


def dm_test(r_new, r_old, bw=21):
    d = (r_new - r_old).dropna().values
    u, T = d - d.mean(), len(d)
    lrv = u @ u / T + sum(2 * (1 - k / (bw + 1)) * (u[k:] @ u[:-k]) / T for k in range(1, bw + 1))
    stat = d.mean() / np.sqrt(lrv / T)
    return float(stat), float(2 * (1 - st.norm.cdf(abs(stat))))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dltm", required=True)
    p.add_argument("--out", default="results/dltm.json")
    a = p.parse_args()
    logpx = pd.read_parquet(os.path.join(a.dltm, "log_prices_sp500_2010_2025.parquet"))
    uni = pick_universe(a.dltm, logpx)
    px = np.exp(logpx[uni.ticker]).loc[:"2025-12-31"].ffill()
    px = px.loc[px.notna().all(axis=1).idxmax():]                 # start when all 30 names trade
    d = pd.DataFrame({t: pd.read_parquet(series_path(a.dltm, t))["dstar"] for t in uni.ticker}
                     ).reindex(px.index).ffill(limit=5)
    mult = pd.DataFrame(np.where(d >= D_HIGH, UP, np.where(d < D_LOW, DOWN, 1.0)), index=d.index, columns=d.columns)
    live = d.notna().any(axis=1).idxmax()

    sig = PortfolioRiskScaledStrategy().generate_signals(px)
    base, _ = backtest_multi_asset(px, sig, TRANSACTION_COST)
    over, _ = backtest_multi_asset(px, sig * mult, TRANSACTION_COST)
    # leverage-neutral version: multipliers rescaled to average 1 across names each day (tilt only)
    tilt, _ = backtest_multi_asset(px, sig * mult.div(mult.mean(axis=1), axis=0), TRANSACTION_COST)
    pre, post = slice(None, live - pd.Timedelta(days=1)), slice(live, None)
    k = base.loc[post].std() / over.loc[post].std()                # overlay de-levered to the base's vol after 2011
    dm, pv = dm_test(over, base)
    out = {"universe": uni.to_dict("records"), "dltm_live_from": str(live.date()),
           "share_high_d": float((d >= D_HIGH).stack().mean()), "share_low_d": float((d < D_LOW).stack().mean()),
           "base": perf(base), "overlay": perf(over),
           "live_sharpe": {"base": sharpe(base.loc[post]), "overlay": sharpe(over.loc[post]),
                           "neutral_tilt": sharpe(tilt.loc[post])},
           "live_vol": {k: float(x.loc[post].std() * np.sqrt(252)) for k, x in
                        (("base", base), ("overlay", over), ("neutral_tilt", tilt))},
           "dm_neutral_tilt": dm_test(tilt.loc[post], base.loc[post]),
           "pre_live_sharpe": sharpe(base.loc[pre]),
           "full_sharpe_overlay_delevered": sharpe(pd.concat([over.loc[pre], over.loc[post] * k])),
           "dm_stat": dm, "p_value": pv,
           "regimes": {n: {"base": sharpe(base.loc[s:e]), "overlay": sharpe(over.loc[s:e])}
                       for n, (s, e) in REGIMES.items()}}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps({k: v for k, v in out.items() if k != "universe"}, indent=1, default=lambda x: round(float(x), 3)))
