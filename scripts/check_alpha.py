#!/usr/bin/env python
"""
Regress a strategy's monthly returns on a benchmark's to test for alpha (HAC standard errors).

Usage
-----
python scripts/check_alpha.py results/s67.csv results/s4.csv     # CSVs written by run_portfolio.py
"""
import argparse
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from lib.metrics import alpha  # noqa: E402

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("strategy_csv")
    p.add_argument("benchmark_csv")
    a = p.parse_args()
    load = lambda f: pd.read_csv(f, index_col=0, parse_dates=True)["portfolio_return"].astype(float)
    res = alpha(load(a.strategy_csv), load(a.benchmark_csv))
    print(f"Alpha: {res['alpha']:.4%} per month (t = {res['t']:.2f}, p = {res['p']:.4f})")
    print(f"Alpha (annualised): {(1 + res['alpha']) ** 12 - 1:.2%}")
    print(f"Beta:  {res['beta']:.2f}   R^2: {res['r2']:.3f}")
