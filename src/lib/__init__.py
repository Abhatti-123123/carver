from lib.strat.buy_n_hold   import BuyAndHoldStrategy
from lib.strat.risk_scaled_strategy   import RiskScaledBuyAndHoldStrategy
from lib.strat.variable_risk_scaled_strategy import VariableRiskScaledBuyAndHoldStrategy
from lib.strat.portfolio_risk_scaled_strategy import PortfolioRiskScaledStrategy

STRATEGY_REGISTRY = {
    "buy_and_hold":  BuyAndHoldStrategy,
    "risk_scaled":   RiskScaledBuyAndHoldStrategy,
    "variable_risk_scaled": VariableRiskScaledBuyAndHoldStrategy,
    "portfolio_risk_scaled": PortfolioRiskScaledStrategy
}