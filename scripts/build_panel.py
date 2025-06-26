#!/usr/bin/env python
"""
Usage
-----
python scripts/build_panel.py --out data/panel.parquet
"""
import argparse
import pandas as pd

from lib.loaders  import load_prices
from lib.adjust   import back_adjust
from lib.filters  import trim_dates, fill_nas
from config.base import BACK_ADJ_METH, START_DATE, END_DATE
from config.universe import SYMBOLS
import os

# scripts/build_panel.py

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="data/panel.parquet")
    args = p.parse_args()

    raw  = load_prices(START_DATE, END_DATE)

    # adj  = back_adjust(raw, method=BACK_ADJ_METH)
    # panel = fill_nas(trim_dates(raw))
    panel = raw.copy()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    panel.to_parquet(args.out)
    print(f"[✓] Saved {panel.shape[1]} contracts, {len(panel)} rows  →  {args.out}")

