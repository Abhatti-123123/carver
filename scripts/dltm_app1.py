#!/usr/bin/env python
"""
dLTM extension: long memory as an asset-level skew signal.

1. Cross-section: at each month-end, regress every stock's forward 21-day realized skew on its walk-forward d*
   (same date, so the calendar era cannot drive it); average the slopes (Fama-MacBeth, Newey-West t).
2. Application: the final system on a sector-balanced 30-name S&P 500 universe (3 names x 10 sectors; 15+ years
   of history and 50%+ dLTM coverage), with each position tilted x1.5 when d* >= 0.7 and x0.5 when d* < 0.3,
   rescaled every day to average 1 across names so total risk is unchanged (a pure tilt, no added leverage).
   Tested with Diebold-Mariano on the daily return differential, Newey-West bandwidth 21.

Inputs (--dltm folder): log_prices_sp500_2010_2025.parquet, gics_map.json, series_14y_est_n2800/<TICKER>_n2800_series.parquet

Usage
-----
python scripts/dltm_app1.py --dltm <dltm folder> --out results/dltm.json
"""
import argparse
import glob
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config.base import TRANSACTION_COST  # noqa: E402
from lib.strat.portfolio_risk_scaled_strategy import PortfolioRiskScaledStrategy  # noqa: E402
from lib.backtester.backtester import backtest_multi_asset  # noqa: E402

D_LOW, D_HIGH, UP, DOWN = 0.3, 0.7, 1.5, 0.5


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


def cross_section(dstar, logpx):
    """Monthly slope of forward 21-day skew on d*, and the high-minus-low-tercile skew spread (same date)."""
    fwd_skew = logpx.diff()[::-1].rolling(21, min_periods=18).skew()[::-1].shift(-1)
    slopes, spreads = {}, {}
    for dt in dstar.resample("ME").last().index:
        dt = dstar.index[dstar.index <= dt].max()
        if dt not in fwd_skew.index:
            continue
        d = dstar.loc[dt].dropna()
        y = fwd_skew.loc[dt].reindex(d.index).dropna()
        x = d[y.index]
        if len(x) < 100:
            continue
        slopes[dt] = np.polyfit(x, y, 1)[0]
        spreads[dt] = y[x >= x.quantile(2 / 3)].mean() - y[x <= x.quantile(1 / 3)].mean()
    out = {}
    for name, ser in (("slope", pd.Series(slopes)), ("high_minus_low", pd.Series(spreads))):
        nw = sm.OLS(ser.values, np.ones(len(ser))).fit(cov_type="HAC", cov_kwds={"maxlags": 6})
        out[name] = {"mean": float(ser.mean()), "nw_t": float(nw.tvalues[0]), "months": len(ser),
                     "share_negative": float((ser < 0).mean()),
                     "by_period": {f"{a}-{b}": {"mean": float(ser.loc[a:b].mean()),
                                                "t": float(ser.loc[a:b].mean() / (ser.loc[a:b].std() / np.sqrt(len(ser.loc[a:b]))))}
                                   for a, b in (("2011", "2019"), ("2020", "2025"))}}
    return out


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dltm", required=True)
    p.add_argument("--out", default="results/dltm.json")
    a = p.parse_args()
    logpx = pd.read_parquet(os.path.join(a.dltm, "log_prices_sp500_2010_2025.parquet"))
    all_d = pd.concat({Path(f).name.split("_n2800")[0]: pd.read_parquet(f)["dstar"]
                       for f in glob.glob(os.path.join(a.dltm, "series_14y_est_n2800", "*_n2800_series.parquet"))}, axis=1)

    uni = pick_universe(a.dltm, logpx)
    px = np.exp(logpx[uni.ticker]).loc[:"2025-12-31"].ffill()
    px = px.loc[px.notna().all(axis=1).idxmax():]                 # start when all 30 names trade
    d = all_d[uni.ticker].reindex(px.index).ffill(limit=5)
    mult = pd.DataFrame(np.where(d >= D_HIGH, UP, np.where(d < D_LOW, DOWN, 1.0)), index=d.index, columns=d.columns)
    tilt_mult = mult.div(mult.mean(axis=1), axis=0)                # average 1 across names: tilt only
    live = slice(d.notna().any(axis=1).idxmax(), None)

    sig = PortfolioRiskScaledStrategy().generate_signals(px)
    base, _ = backtest_multi_asset(px, sig, TRANSACTION_COST)
    tilt, _ = backtest_multi_asset(px, sig * tilt_mult, TRANSACTION_COST)
    out = {"cross_section": cross_section(all_d, logpx),
           "tilt": {"universe": uni.ticker.tolist(), "live_from": str(live.start.date()),
                    "sharpe": {"base": sharpe(base.loc[live]), "tilt": sharpe(tilt.loc[live])},
                    "vol": {"base": float(base.loc[live].std() * np.sqrt(252)),
                            "tilt": float(tilt.loc[live].std() * np.sqrt(252))},
                    "dm": dm_test(tilt.loc[live], base.loc[live])}}
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=lambda x: round(float(x), 4)))
