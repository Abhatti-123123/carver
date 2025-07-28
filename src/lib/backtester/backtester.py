import pandas as pd
import numpy as np

def compute_strategy_returns(prices: pd.Series,
                              signals: pd.Series,
                              transaction_cost: float,
                              annualization: int = 252):
    returns = prices.pct_change(fill_method=None).fillna(0.0)

    sig_events = signals.replace(0, np.nan)
    positions = sig_events.shift(1).ffill().fillna(0.0)

    trades = positions.diff().abs().fillna(0.0)
    trade_cost = trades * transaction_cost

    strat_returns = positions * returns
    strat_returns[trades != 0] -= trade_cost[trades != 0]

    equity_curve = (1 + strat_returns).cumprod()
    return strat_returns, equity_curve, positions, trades


def backtest_strategy(prices, signals, transaction_cost=0.0, annualization=252):
    strat_returns, equity_curve, positions, trades = compute_strategy_returns(
        prices, signals, transaction_cost, annualization
    )

    total_return = equity_curve.iloc[-1] - 1
    periods = len(strat_returns)
    cagr = equity_curve.iloc[-1]**(annualization / periods) - 1 if periods > 0 else np.nan
    vol = strat_returns.std() * np.sqrt(annualization)
    sharpe = strat_returns.mean() / (strat_returns.std() + 1e-10) * np.sqrt(annualization)

    drawdown = equity_curve / equity_curve.cummax() - 1
    max_drawdown = drawdown.min()
    total_trades = int(trades.sum())

    mask = positions != 0
    hit_rate = strat_returns[mask].gt(0).sum() / mask.sum() if mask.sum() > 0 else np.nan

    holdings = positions.copy()
    holdings[holdings != 0] = 1
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

    results_df = pd.DataFrame({
        'strategy_return': strat_returns,
        'equity_curve': equity_curve
    })

    return results_df, metrics


def backtest_multi_asset(prices: pd.DataFrame,
                         signals: pd.DataFrame,
                         transaction_cost: float = 0.0,
                         annualization: int = 252):
    """
    Portfolio-level backtest using individual asset strategy returns.
    Assumes signals are already scaled appropriately (i.e., fraction of capital per asset).
    """
    strat_returns = {}
    equity_curves = {}

    for col in prices.columns:
        sr, eq, _, _ = compute_strategy_returns(prices[col], signals[col], transaction_cost, annualization)
        strat_returns[col] = sr
        equity_curves[col] = eq

    ret_df = pd.DataFrame(strat_returns).fillna(0.0)

    # Total portfolio return (sum of weighted positions; assumes capital split)
    portfolio_ret = ret_df.sum(axis=1)
    equity_curve = (1 + portfolio_ret).cumprod()

    drawdown = equity_curve / equity_curve.cummax() - 1
    max_drawdown = drawdown.min()

    metrics = {
        "total_return": equity_curve.iloc[-1] - 1,
        "cagr": equity_curve.iloc[-1]**(annualization / len(portfolio_ret)) - 1,
        "volatility": portfolio_ret.std() * np.sqrt(annualization),
        "sharpe": portfolio_ret.mean() / (portfolio_ret.std() + 1e-10) * np.sqrt(annualization),
        "max_drawdown": max_drawdown,
        "total_trades": int(signals.diff().abs().sum().sum())
    }

    results_df = pd.DataFrame({
        "portfolio_return": portfolio_ret,
        "equity_curve": equity_curve
    })

    return results_df, metrics
