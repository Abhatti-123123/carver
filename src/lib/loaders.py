"""Download daily closes from Yahoo Finance and clean them into a price panel."""
import pandas as pd
import yfinance as yf


def load_prices(tickers: list[str], start: str, end: str) -> pd.DataFrame:
    """Daily close prices, one column per ticker (empty columns dropped)."""
    px = yf.download(tickers, start=start, end=end, progress=False, auto_adjust=False)["Close"]
    return px[[t for t in tickers if t in px.columns]].dropna(axis=1, how="all")


def clean_panel(px: pd.DataFrame, keep_all: bool = False) -> pd.DataFrame:
    """
    Default: drop markets with >10% missing days or >5 missing in the last 48 rows, then forward-fill.
    keep_all: keep every market; before a market lists it is held flat (back-filled price, zero return).
    """
    if keep_all:
        return px.ffill().bfill()
    px = px.loc[:, px.isnull().mean() <= 0.10]
    px = px.loc[:, px.tail(48).isnull().sum() <= 5]
    return px.ffill()
