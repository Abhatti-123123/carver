# lib/loaders.py  ───────────────────────────────────────────
"""
Pull daily continuous-futures prices from CHRIS (Nasdaq Data Link).
Bloomberg support can be added later.
"""
from __future__ import annotations
import nasdaqdatalink as ndl
import requests
import pandas as pd
import re
import yfinance as yf

from config.api import POLYGON_API_KEY, CHRIS_API_KEY
from config.universe import VENDOR, SYMBOLS, SYMBOLS_POLY, YF_TICKERS

ndl.ApiConfig.api_key = CHRIS_API_KEY

BASE_URL = "https://api.polygon.io"

def _to_polygon_symbol(code: str) -> str:
    """
    Convert internal symbol like 'CME_ES1' to Polygon continuous symbol 'C:ES'.
    Strips vendor prefix and trailing digit, maps to 'C:<ROOT>'.
    """
    # Expect format VENDOR_ROOT#: e.g. 'CME_ES1'
    parts = code.split("_")
    if len(parts) != 2:
        raise ValueError(f"Invalid SYMBOL format: {code}")
    root_with_num = parts[1]
    # Remove trailing digit
    root = re.sub(r"\d$", "", root_with_num)
    return f"C:{root}"


def get_futures_aggregates(symbol: str,
                           multiplier: int,
                           timespan: str,
                           from_date: str,
                           to_date: str,
                           adjusted: bool = True,
                           limit: int = 50000) -> pd.DataFrame:
    """
    Fetch OHLCV aggregates for a futures symbol via Polygon API.

    Returns an empty DataFrame with a DatetimeIndex if no data is returned.
    Raises RuntimeError on HTTP errors (e.g., 403 for insufficient plan).
    """
    url = (
        f"{BASE_URL}/v2/aggs/ticker/{symbol}/range/"
        f"{multiplier}/{timespan}/{from_date}/{to_date}"
    )
    params = {
        "apiKey": POLYGON_API_KEY,
        "adjusted": str(adjusted).lower(),
        "sort": "asc",
        "limit": limit
    }
    try:
        resp = requests.get(url, params=params)
        resp.raise_for_status()
    except requests.exceptions.HTTPError as e:
        # Attempt to extract error message from response
        try:
            err = resp.json().get("message", resp.text)
        except Exception:
            err = resp.text
        raise RuntimeError(
            f"Polygon API error {resp.status_code} for symbol {symbol}: {err}. "
            f"Check your subscription permissions or timeframe."
        )
    bars = resp.json().get("results", [])

    # Transform bars into list of dicts
    records = [
        {
            "timestamp": pd.to_datetime(b["t"], unit="ms"),
            "open": b["o"],
            "high": b["h"],
            "low": b["l"],
            "close": b["c"],
            "volume": b["v"]
        }
        for b in bars
    ]
    # If no data, return empty DataFrame with appropriate index
    if not records:
        empty_index = pd.DatetimeIndex([], name="timestamp")
        return pd.DataFrame([], index=empty_index,
                            columns=["open", "high", "low", "close", "volume"])

    df = pd.DataFrame.from_records(records)
    df.set_index("timestamp", inplace=True)
    return df

def _chris_single(code: str, field: str = "Settle") -> pd.Series:
    df = ndl.get(code)[[field]]
    df.index = pd.to_datetime(df.index)
    return df[field]


def _chris_multi(symbols: list[str]) -> pd.DataFrame:
    frame_dict = {sym.split("_")[-1]: _chris_single("CHRIS/" + sym)
                  for sym in symbols}
    return pd.concat(frame_dict, axis=1).sort_index()


def _polygon_multi(symbols: list[str],
                   start_date: str,
                   end_date: str,
                   multiplier: int = 1,
                   timespan: str = "day",
                   adjusted: bool = True) -> pd.DataFrame:
    """
    Fetch multiple futures symbols via Polygon and concat.
    SYMBOLS should contain codes like "C:ES" or specific contract tickers.
    """
    dfs = {}
    for sym in symbols:
        df = get_futures_aggregates(
            symbol=sym,
            multiplier=multiplier,
            timespan=timespan,
            from_date=start_date,
            to_date=end_date,
            adjusted=adjusted
        )
        dfs[sym] = df["close"]
    # align on timestamp index
    return pd.concat(dfs, axis=1).sort_index()


# def load_prices(start_date: str, end_date: str) -> pd.DataFrame:
#     """
#     Load price series based on configured VENDOR.
#     - CHRIS: uses nasdaq-datalink continuous futures codes
#     - POLYGON: uses Polygon aggregates
#     """
#     if VENDOR == "CHRIS":
#         return _chris_multi(SYMBOLS)
#     elif VENDOR == "POLYGON":
#         return _polygon_multi(
#             symbols=SYMBOLS_POLY,
#             start_date=start_date,
#             end_date=end_date
#         )
#     else:
#         raise NotImplementedError(f"Vendor {VENDOR} not yet supported")

# Map internal SYMBOLS to Yahoo Finance tickers

def load_prices(start_date: str, end_date: str) -> pd.DataFrame:
    """
    Download daily Close prices via yfinance for each ticker in YF_TICKERS.
    Returns a DataFrame indexed by date, columns are the tickers.
    """
    closes: dict[str, pd.Series] = {}

    for ticker in YF_TICKERS:
        try:
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False,
                auto_adjust=False,
                actions=False
            )
            # Extract Close series if available
            series = data["Close"].copy()
        except Exception as e:
            print(f"Warning: failed to download {ticker}: {e}")
            series = pd.Series(dtype=float)

        # Ensure the series name is the ticker (avoids rename errors)
        series.name = ticker
        closes[ticker] = series

    # Combine all series into a single DataFrame
    df = pd.concat(closes.values(), axis=1)
    df.columns = list(closes.keys())
    return df