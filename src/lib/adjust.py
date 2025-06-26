# lib/adjust.py  ────────────────────────────────────────────
"""
Back-adjust continuous futures to remove roll gaps.

Supported methods
-----------------
diff    : subtract price jumps  (point-preserving)
ratio   : divide by jump ratio  (return-preserving)
panama  : classical Panama additive adjustment
          (same algebra as diff, but labelled explicitly)
"""
from __future__ import annotations
import pandas as pd

# ---------------------------------------------------------------------
# 1. Roll-date detector
# ---------------------------------------------------------------------
def _detect_roll(series: pd.Series,
                 thresh: float = 5.0) -> list[pd.Timestamp]:
    """
    Heuristic: a roll occurs when the *absolute* daily move exceeds
    (thresh × 10-day ATR).  Works ~90 % of the time for CHRIS generics.
    Because of time and resource limititations we don't use fixed calender dates or OI to find rolls
    and use heurestics instead.
    More robust techniques will be used in future work.
    """
    atr10 = series.diff().abs().rolling(10).mean()
    mask  = (series.diff().abs() > thresh * atr10).fillna(False)
    return list(series.index[mask])


# ---------------------------------------------------------------------
# 2. Adjustment kernels
# ---------------------------------------------------------------------
# def _diff_adjust(s: pd.Series) -> pd.Series:
#     adj = s.copy()
#     for rd in _detect_roll(s):
#         gap = adj.loc[rd] - adj.loc[rd - pd.Timedelta(days=1)]
#         adj.loc[: rd - pd.Timedelta(days=1)] -= gap
#     return adj

def _diff_adjust(series: pd.Series) -> pd.Series:
    """
    Back-adjust by subtracting each roll-gap from all prior prices.
    Operates only on the non-NaN portion of `series`.
    """
    # Work on the contiguous part
    s = series.dropna().copy()
    if s.empty:
        # nothing to do
        return series * float("nan")

    # Detect roll points
    rolls = _detect_roll(s)

    # Start from the raw series
    adj = s.copy()
    for rd in rolls:
        # find the bar immediately before rd
        idx = s.index.get_loc(rd)
        prev = s.index[idx - 1]
        gap  = adj.loc[rd] - adj.loc[prev]
        # subtract that gap from *all* prices up to and including prev
        adj.loc[:prev] = adj.loc[:prev] - gap

    # re-index back to the original full index (NaNs outside s)
    print(len(rolls))
    return adj.reindex(series.index)


def _ratio_adjust(s: pd.Series) -> pd.Series:
    adj = s.copy()
    for rd in _detect_roll(s):
        ratio = adj.loc[rd] / adj.loc[rd - pd.Timedelta(days=1)]
        adj.loc[: rd - pd.Timedelta(days=1)] /= ratio
    return adj


# Panama additive adjustment is numerically identical to _diff_adjust;
# we expose a separate name for clarity.
def _panama_adjust(s: pd.Series) -> pd.Series:
    return _diff_adjust(s)


# ---------------------------------------------------------------------
# 3. Public gateway
# ---------------------------------------------------------------------
_METHOD_MAP = {
    "diff":   _diff_adjust,
    "ratio":  _ratio_adjust,
    "panama": _panama_adjust,
}

def back_adjust(df: pd.DataFrame,
                method: str = "diff") -> pd.DataFrame:
    """
    Parameters
    ----------
    df      : raw continuous-contract prices (columns = symbols)
    method  : "diff", "ratio", or "panama"

    Returns
    -------
    pd.DataFrame  back-adjusted prices
    """
    try:
        fn = _METHOD_MAP[method.lower()]
    except KeyError as e:
        raise ValueError(f"Unknown back-adjust method '{method}'") from e
    return df.apply(fn, axis=0)
