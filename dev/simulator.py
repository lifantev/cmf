from collections import defaultdict
from dataclasses import dataclass
import numpy as np
from candles import CandleSeries
from strategies import Strategy


@dataclass
class TradingStats:
    pnl: float
    traded_volume: int
    max_drawdown: float
    holding_time_percent: dict[str, float]  # Fraction: hold time / total time
    position_flips: dict[str, int]
    sharpe_ratio: float
    sortino_ratio: float


class TradingSimulator:
    """
    TradingSimulator simulates trading based on added strategies and market data.
    """

    def __init__(self, candles: dict[str, CandleSeries]):
        """
        Parameters
        -----------
        candles: dict[str, CandleSeries]
           Candle series for each instrument. Series must be not empty.
        """
        if not candles:
            raise ValueError("Candle series must be provided")

        self.candles = candles
        self.strategies: dict[str, Strategy] = {}  # {strategy_name: strategy}

    def add_strategy(self, strategy: Strategy):
        """
        Add strategy to the simulator. Uniq by strategy name.

        Parameters
        -----------
        strategy: Strategy
            Strategy to add for the simulator.
        """
        if strategy.mode not in Strategy.valid_modes():
            raise ValueError(
                f"Unsupported mode '{strategy.mode}'. Supported modes are: {Strategy.valid_modes()}"
            )

        if strategy.name not in self.strategies:
            self.strategies[strategy.name] = strategy

    def delete_strategy(self, strategy_name: str):
        """
        Delete strategy from the simulator.

        Parameters
        -----------
        strategy_name: str
            Name of the strategy to delete.
        """
        if strategy_name in self.strategies:
            del self.strategies[strategy_name]

    def run(self) -> dict[str, TradingStats]:
        """
        Run simulation for all added strategies to obtain trading statistics.

        Returns
        --------
        retval: dict[str, TradingStats]
            Dictionary of TradingStats by each strategy name.
        """
        results: dict[str, TradingStats] = {}
        for name, strategy in self.strategies.items():
            results[name] = self._simulate_strategy(strategy)

        return results

    def _simulate_strategy(self, strategy: Strategy) -> TradingStats:
        """
        Simulate a single strategy.
        """
        pnl: float = 0
        max_pnl: float = 0
        traded_volume: int = 0
        max_drawdown: float = 0
        position_flips: dict[str, int] = defaultdict(int)
        avg_holding_time: dict[str, int] = defaultdict(int)
        curr_position: dict[str, int] = defaultdict(int)

        length = min(
            max([cndls.length for cndls in self.candles.values()]),
            len(strategy.actions_vector),
        )
        pnl_series = np.zeros(length, dtype=np.float64)

        for t in range(length - 1):  # iterate over candles
            actions = strategy.actions_vector[t]
            _pnl: float = 0.0

            # Iterate over instruments within this candle and apply actions
            for instr, action in actions.items():
                if not self._is_action_within_candles(instr, t + 1):
                    continue

                action_price = self._action_price(
                    instr, strategy.mode, action.quantity, t
                )
                # NOTE: Assumption: if action price is None, then action is not executed
                if action_price == 0:
                    avg_holding_time[instr] += 1

                traded_volume += abs(action.quantity)
                # NOTE: "Last Traded Price". Since close price is used for action of CLOSE strategy, use next candles price.
                ltp = self._action_price(instr, strategy.mode, action.quantity, t + 1)

                if action.quantity > 0:  # buy
                    _pnl += (ltp - action_price) * action.quantity
                    if curr_position[instr] <= 0:
                        curr_position[instr] = 1
                        position_flips[instr] += 1
                elif action.quantity < 0:  # sell
                    _pnl += (ltp - action_price) * action.quantity
                    if curr_position[instr] >= 0:
                        curr_position[instr] = -1
                        position_flips[instr] += 1
                else:  # hold
                    avg_holding_time[instr] += 1

            pnl += _pnl
            pnl_series[t] = _pnl
            max_pnl = max(max_pnl, pnl)
            max_drawdown = max(max_drawdown, max_pnl - pnl)

        sharpe_ratio = _calc_sharpe_ratio(pnl_series)
        sortino_ratio = _calc_sortino_ratio(pnl_series)

        return TradingStats(
            pnl=pnl,
            traded_volume=traded_volume,
            max_drawdown=max_drawdown,
            position_flips=position_flips,
            holding_time_percent={
                instr: (
                    holds
                    / min(self.candles[instr].length, len(strategy.actions_vector))
                )
                for instr, holds in avg_holding_time.items()
            },
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
        )

    # Helper to check if action has candles for its instrument at given T
    def _is_action_within_candles(self, instrument: str, t: int) -> bool:
        if instrument not in self.candles:
            raise ValueError(
                f"Instrument '{instrument}' is not contained in trading simulator candles"
            )
        return t < self.candles[instrument].length

    def _action_price(self, instrument: str, mode: str, quantity: int, t: int) -> float:
        """
        Get trading price for instrument's candle at index T based on mode and quantity.
        """
        if mode == Strategy.CLOSE:
            return self.candles[instrument].get_value_at(t, CandleSeries.CLOSE)
        elif mode == Strategy.AVERAGE:
            if quantity > 0:  # buy
                return self.candles[instrument].get_value_at(
                    t, CandleSeries.AVG_BUY_PRICE
                )
            elif quantity < 0:  # sell
                return self.candles[instrument].get_value_at(
                    t, CandleSeries.AVG_SELL_PRICE
                )
            return 0

        raise ValueError(
            f"Unsupported mode '{mode}'. Supported modes are: {Strategy.valid_modes()}"
        )


# Calculates Sharpe Ratio
def _calc_sharpe_ratio(pnls) -> float:
    if not len(pnls):
        return 0
    return np.mean(pnls) / np.std(pnls) if np.std(pnls) != 0 else 0


# Calculates Sortino Ratio
def _calc_sortino_ratio(pnls) -> float:
    if not len(pnls):
        return 0
    downside_pnls = [p for p in pnls if p < 0]
    if not len(downside_pnls):
        return float("+inf")
    downside_std = np.std(pnls)
    return np.mean(pnls) / downside_std if downside_std != 0 else 0
