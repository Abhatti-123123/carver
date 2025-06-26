# lib/filters.py  ───────────────────────────────────────────
import pandas as pd
from config.base import START_DATE, END_DATE


def trim_dates(df: pd.DataFrame) -> pd.DataFrame:
    return df.loc[START_DATE:END_DATE]


def fill_nas(df: pd.DataFrame) -> pd.DataFrame:
    return df.ffill().dropna()
