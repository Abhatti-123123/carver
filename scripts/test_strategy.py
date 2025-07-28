# #!/usr/bin/env python
# # scripts/run_backtest.py

# import argparse
# import pandas as pd

# # ─── replace these imports with wherever your functions live ─────
# from lib.backtester.backtester import backtest_strategy
# from lib.strat.buy_n_hold   import buy_n_hold  # if you have a signal-gen fn
# # ──────────────────────────────────────────────────────────────────

# # 2) define a helper that will be applied per-column
# def _one_backtest(price_series: pd.Series, tc: float, signals: pd.Series):
#     """
#     Runs backtest_strategy on one column of prices + the common signals,
#     returns the metrics dict as a pd.Series.
#     """
#     results_df, metrics = backtest_strategy(
#         prices=price_series,
#         signals=signals,
#         transaction_cost= tc
#         )
#     return metrics, results_df

# def main(start_date: str, end_date: str, tc: float, out: str):
#     # 1) build your DataFrame of prices (and whatever else)
#     df = pd.read_parquet("data/panel.parquet")
    
#     # 2) build your signal series (or dict of signals)
#     #    e.g. if you have a single pd.Series of +1/–1
#     signals = buy_n_hold(df)
    
#     # 3) extract the price series your backtester expects
#     #    e.g. a pd.Series of closes:
    
#     # 4) run the backtest
#     # collect exactly what we want: a list of (metrics_dict, results_df)
#     raw = [
#         _one_backtest(df[col], tc, signals)
#         for col in df.columns
#     ]

#     # split into two sequences
#     metrics, results = zip(*raw)
#     print(metrics)
    
#     metrics_df = pd.DataFrame(metrics, index=df.columns)
#     print("=== Backtest metrics ===")
#     for sym, row in metrics_df.iterrows():
#         print(f"[{sym}]")
#         for name, val in row.items():
#             print(f"  {name:20s}: {val}")

#     # concatenate all the per-symbol trade-by-trade DataFrames
#     combined = pd.concat(
#         results,
#         axis=1,
#         keys=df.columns,
#         names=["symbol","series"]
#     )
#     combined.to_csv(out)
#     df.to_csv("data/prices.csv")
#     print(f"[✓] Detailed results saved to data/prices.csv")
#     print(f"[✓] Detailed results saved to {out}")

# if __name__ == "__main__":
#     p = argparse.ArgumentParser("Run dataset → signals → backtest")
#     p.add_argument("--start", type=str, default="2020-01-01",
#                    help="start date for dataset")
#     p.add_argument("--end",   type=str, default="2021-01-01",
#                    help="end   date for dataset")
#     p.add_argument("--tc",    type=float, default=0.001,
#                    help="round-trip transaction cost")
#     p.add_argument("--out",   type=str, default="results/backtest.csv",
#                    help="where to write the detailed results CSV")
#     args = p.parse_args()

#     # ensure your output dir exists
#     import os
#     os.makedirs(os.path.dirname(args.out), exist_ok=True)

#     main(args.start, args.end, args.tc, args.out)



#!/usr/bin/env python
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

"""
Generic dataset → signals → backtest runner.

USAGE EXAMPLES
--------------
# Strategy 1 (fixed size)
python scripts/run_backtest.py --strategy buy_and_hold

# Strategy 2 (risk‑scaled)
python scripts/run_backtest.py --strategy risk_scaled --tc 0.0005
"""
import argparse, os, pandas as pd
from lib import STRATEGY_REGISTRY           # <-- registry from __init__.py
from lib.backtester.backtester import backtest_strategy
# replace with your own loader; must return a dataframe of close prices

def backtest_single_symbol(series: pd.Series, strategy_cls, tc: float):
    """Generate signals with the chosen strategy and run the backtest."""
    strat   = strategy_cls()                       # instantiate
    signals = strat.generate_signals(series)       # pd.Series (positions)
    results_df, metrics = backtest_strategy(
        prices=series,
        signals=signals,
        transaction_cost=tc
    )
    return metrics, results_df                     # dict, pd.DataFrame

def main(start: str, end: str, tc: float,
         strategy_name: str, out_path: str) -> None:

    if strategy_name not in STRATEGY_REGISTRY:
        raise KeyError(f"Unknown strategy '{strategy_name}'. "
                       f"Choose from {list(STRATEGY_REGISTRY.keys())}")

    strategy_cls = STRATEGY_REGISTRY[strategy_name]
    price_df = pd.read_parquet("data/panel.parquet")
    print(f"[+] Loaded {price_df.shape[1]} symbols "
          f"from {price_df.index.min()} to {price_df.index.max()}")

    metrics_list, pnl_frames = zip(*[
        backtest_single_symbol(price_df[col], strategy_cls, tc)
        for col in price_df.columns
    ])

    # -- metrics summary -------------------------------------------------
    metrics_df = pd.DataFrame(metrics_list, index=price_df.columns)
    print("\n=== Backtest metrics ===")
    for sym, row in metrics_df.iterrows():
        print(f"[{sym}]  " +
              " | ".join(f"{k}: {v:.4g}" for k, v in row.items()))

    # -- persist results -------------------------------------------------
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    metrics_df.to_csv(out_path)
    print(f"[✓] Metrics saved → {out_path}")

    trade_detail = pd.concat(pnl_frames, axis=1,
                             keys=price_df.columns,
                             names=["symbol","series"])
    detail_path  = os.path.splitext(out_path)[0] + "_detail.csv"
    trade_detail.to_csv(detail_path)
    print(f"[✓] Trade‑by‑trade P&L saved → {detail_path}")

if __name__ == "__main__":
    p = argparse.ArgumentParser("Run strategy backtest")
    p.add_argument("--start",   default="2020-01-01", help="YYYY‑MM‑DD")
    p.add_argument("--end",     default="2021-01-01", help="YYYY‑MM‑DD")
    p.add_argument("--tc",      default=0.0005, type=float,
                                help="round‑trip transaction cost")
    p.add_argument("--strategy", default="buy_and_hold",
                   choices=list(STRATEGY_REGISTRY.keys()))
    p.add_argument("--out",     default="results/metrics.csv",
                   help="CSV for summary metrics")
    args = p.parse_args()

    main(args.start, args.end, args.tc, args.strategy, args.out)
