#!/usr/bin/env python
# scripts/run_backtest.py

import argparse
import pandas as pd

# ─── replace these imports with wherever your functions live ─────
from lib.backtester.backtester import backtest_strategy
from lib.strat.buy_n_hold   import buy_n_hold  # if you have a signal-gen fn
# ──────────────────────────────────────────────────────────────────

# 2) define a helper that will be applied per-column
def _one_backtest(price_series: pd.Series, tc: float, signals: pd.Series):
    """
    Runs backtest_strategy on one column of prices + the common signals,
    returns the metrics dict as a pd.Series.
    """
    results_df, metrics = backtest_strategy(
        prices=price_series,
        signals=signals,
        transaction_cost= tc
        )
    return metrics, results_df

def main(start_date: str, end_date: str, tc: float, out: str):
    # 1) build your DataFrame of prices (and whatever else)
    df = pd.read_parquet("data/panel.parquet")
    
    # 2) build your signal series (or dict of signals)
    #    e.g. if you have a single pd.Series of +1/–1
    signals = buy_n_hold(df)
    
    # 3) extract the price series your backtester expects
    #    e.g. a pd.Series of closes:
    
    # 4) run the backtest
    # collect exactly what we want: a list of (metrics_dict, results_df)
    raw = [
        _one_backtest(df[col], tc, signals)
        for col in df.columns
    ]

    # split into two sequences
    metrics, results = zip(*raw)
    print(metrics)
    
    metrics_df = pd.DataFrame(metrics, index=df.columns)
    print("=== Backtest metrics ===")
    for sym, row in metrics_df.iterrows():
        print(f"[{sym}]")
        for name, val in row.items():
            print(f"  {name:20s}: {val}")

    # concatenate all the per-symbol trade-by-trade DataFrames
    combined = pd.concat(
        results,
        axis=1,
        keys=df.columns,
        names=["symbol","series"]
    )
    combined.to_csv(out)
    df.to_csv("data/prices.csv")
    print(f"[✓] Detailed results saved to data/prices.csv")
    print(f"[✓] Detailed results saved to {out}")

if __name__ == "__main__":
    p = argparse.ArgumentParser("Run dataset → signals → backtest")
    p.add_argument("--start", type=str, default="2020-01-01",
                   help="start date for dataset")
    p.add_argument("--end",   type=str, default="2021-01-01",
                   help="end   date for dataset")
    p.add_argument("--tc",    type=float, default=0.001,
                   help="round-trip transaction cost")
    p.add_argument("--out",   type=str, default="results/backtest.csv",
                   help="where to write the detailed results CSV")
    args = p.parse_args()

    # ensure your output dir exists
    import os
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    main(args.start, args.end, args.tc, args.out)
