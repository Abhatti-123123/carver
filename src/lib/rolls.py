"""Remove contract-roll jumps from Yahoo's stitched front-month series."""
import pandas as pd


def roll_adjust(px: pd.DataFrame, calendar: pd.DataFrame) -> pd.DataFrame:
    """
    Yahoo switches to the next contract around each expiry, so the price gap between contracts lands in one
    daily return. For every contract in the roll calendar, find the largest move (in units of recent vol)
    between first-notice (or last-trade) - 5 days and last-trade + 4 days, set that day's return to 0,
    clip any remaining impossible move to +/-25% (e.g. negative oil), and rebuild prices from the returns.
    """
    rets = px.pct_change(fill_method=None)
    z = (rets / rets.rolling(20, min_periods=10).std().shift(1)).abs()
    for tk in rets.columns:
        for _, c in calendar[calendar.ticker == tk].iterrows():
            lo = (c.first_notice if pd.notna(c.first_notice) else c.last_trade) - pd.Timedelta(days=5)
            window = z.loc[lo:c.last_trade + pd.Timedelta(days=4), tk].dropna()
            if len(window):
                rets.loc[window.idxmax(), tk] = 0.0
    rets = rets.clip(-0.25, 0.25)
    adj = (1 + rets.fillna(0.0)).cumprod() * px.bfill().iloc[0]
    return adj.where(px.notna().cummax())          # keep NaN before each market's history starts
