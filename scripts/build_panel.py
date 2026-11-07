#!/usr/bin/env python
"""
Download a universe from Yahoo Finance, clean it, and neutralise contract-roll days.

Usage
-----
python scripts/build_roll_calendar.py --out data/roll_calendar.csv
python scripts/build_panel.py --universe 31 --out data/panel_31.parquet
python scripts/build_panel.py --universe crypto --start 2023-01-01 --end 2025-11-28 --out data/panel_crypto.parquet
"""
import argparse
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from config.base import START_DATE, END_DATE  # noqa: E402
from config.universe import UNIVERSES  # noqa: E402
from lib.loaders import load_prices, clean_panel  # noqa: E402
from lib.rolls import roll_adjust  # noqa: E402

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--universe", default="31", choices=list(UNIVERSES))
    p.add_argument("--start", default=START_DATE)
    p.add_argument("--end", default=END_DATE)
    p.add_argument("--calendar", default="data/roll_calendar.csv")
    p.add_argument("--out", default="data/panel_31.parquet")
    a = p.parse_args()

    px = clean_panel(load_prices(UNIVERSES[a.universe], a.start, a.end), keep_all=a.universe.startswith("35"))
    if a.universe != "crypto":                       # spot crypto has no contract rolls
        cal = pd.read_csv(a.calendar, parse_dates=["first_notice", "last_trade", "roll_date"])
        px = roll_adjust(px, cal)
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    px.to_parquet(a.out)
    print(f"[ok] {px.shape[1]} markets, {px.index[0].date()} -> {px.index[-1].date()} -> {a.out}")
