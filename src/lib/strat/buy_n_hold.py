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