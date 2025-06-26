import pandas as pd
import numpy as np

def backtest_strategy(prices, signals, transaction_cost=0.0, annualization=252):
    """
    Backtest a strategy given price series and discrete signals.

    Parameters:
    - prices (pd.Series): Price series indexed by date.
    - signals (pd.Series): Strategy signals (-1, 0, 1) indexed by date.
    - transaction_cost (float): Cost per trade as fraction of trade notional.
    - annualization (int): Number of trading periods in a year (e.g., 252).

    Returns:
    - pd.DataFrame: DataFrame with 'strategy_return' and 'cumulative_return'.
    - dict: Performance metrics.
    """
    assert isinstance(prices, pd.Series), "prices must be a pandas Series"
    assert isinstance(signals, pd.Series), "signals must be a pandas Series"
    # Compute period returns
    returns = prices.pct_change().fillna(0)

    # Align signals
    sig_events = signals.replace(0, np.nan)
    positions  = sig_events.shift(1).ffill().fillna(0)

    # Transaction costs: cost when position changes
    trades = positions.diff().abs().fillna(0)
    trade_cost = trades * transaction_cost

    # Strategy returns net of transaction costs
    strat_returns = positions * returns
    strat_returns[trades != 0] -= trade_cost[trades != 0]

    # Cumulative returns
    cum_returns = (1 + strat_returns).cumprod() - 1

    # Performance metrics
    total_return = cum_returns.iloc[-1]
    # CAGR
    periods = len(strat_returns)
    cagr = (1 + total_return) ** (annualization / periods) - 1 if periods > 0 else np.nan
    # Annualized volatility
    vol = strat_returns.std() * np.sqrt(annualization)
    # Sharpe ratio (assume risk-free ~0)
    sharpe = strat_returns.mean() / (strat_returns.std() + 1e-10) * np.sqrt(annualization)
    # Max drawdown
    running_max = cum_returns.cummax()
    drawdown = cum_returns - running_max
    max_drawdown = drawdown.min()
    # Total trades
    total_trades = int(trades.sum())
    # Hit rate: fraction of positive strategy returns when in market (positions !=0)
    mask = positions != 0
    hit_rate = strat_returns[mask].gt(0).sum() / mask.sum() if mask.sum() > 0 else np.nan
    # Average holding period (in periods)
    holdings = positions.copy()
    holdings[holdings != 0] = 1
    # Compute lengths of consecutive ones
    groups = (holdings != holdings.shift()).cumsum()
    lengths = holdings.groupby(groups).sum()[holdings.groupby(groups).first().eq(1)]
    avg_holding = lengths.mean() if not lengths.empty else 0

    metrics = {
        'total_return': total_return,
        'cagr': cagr,
        'volatility': vol,
        'sharpe': sharpe,
        'max_drawdown': max_drawdown,
        'total_trades': total_trades,
        'hit_rate': hit_rate,
        'avg_holding_period': avg_holding
    }

    results_df = pd.DataFrame({'strategy_return': strat_returns, 'cumulative_return': cum_returns})
    return results_df, metrics