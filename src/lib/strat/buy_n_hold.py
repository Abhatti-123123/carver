import pandas as pd

def buy_n_hold(df: pd.DataFrame) -> pd.Series:
    """
    Generate a buy-and-hold trade signal:
      • +1 on the very first bar   (enter long)
      • -1 on the very last bar     (exit long)
      •  0 everywhere else
    """
    # initialize a zero series with the same index as your data
    sig = pd.Series(0, index=df.index, name="signal")
    
    # entry on first bar
    sig.iloc[0] = 1
    
    # exit on last bar
    sig.iloc[-1] = -1
    
    return sig


# src/lib/strat/buy_n_hold_strategy.py
import pandas as pd
from .strategy_base import StrategyBase

class BuyAndHoldStrategy(StrategyBase):
    """
    Strategy 1 – fixed one‑contract buy‑and‑hold.
    """

    def __init__(self):
        super().__init__(target_vol=None, vol_window=None)

    def generate_signals(self, prices: pd.Series) -> pd.Series:
        if prices.empty:
            raise ValueError("Empty price series")
        signals = pd.Series(0.0, index=prices.index)
        signals.iloc[0]  = +1.0   # enter long
        signals.fillna(method="ffill")
        signals.iloc[-1] = -1.0   # exit
        return signals.cumsum()   # converts discrete trades → position size
