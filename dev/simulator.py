import numpy as np
import candles as cnd
from dataclasses import dataclass
import marketdata as md

CLOSE = 'close'
AVERAGE = 'average'

@dataclass
class Action:
    """
    Trading action.
    Quantity is positive for buying and negative for selling, zero for holding.
    """
    instrument: str
    quantity: int

# Actions to be executed within single OHLC candle.
type Actions = list[Action]

@dataclass
class Strategy:
    """
    Strategy represents a trading strategy.
    Mode is a trading mode, either 'close' or 'average'.
    All actions in actions vector with index T will be executed within OHLC candle with same index T.
    """
    name: str
    mode: str
    actions_vector: list[Actions]

@dataclass
class TradingStats:
    pnl: float
    traded_volume: int
    max_drawdown: int
    position_flips: int
    avg_holding_time_ms: int 
    sharpe_ratio: float 
    sortino_ratio: float 

class TradingSimulator:
    """
    TradingSimulator simulates trading based on added strategies and market data.
    """
    @staticmethod
    def valid_modes() -> set[str]: return {CLOSE, AVERAGE}

    def __init__(self, candles: dict[str, cnd.CandlesSeries]):
        self.candles = candles
        self.strategies: dict[str, Strategy] = {} # {strategy_name: strategy}


    def add_strategy(self, strategy: Strategy):
        """
        Add a strategy to the simulator. Uniq by strategy name.
        """
        if strategy.mode not in self.valid_modes():
            raise ValueError(f"Unsupported mode '{strategy.mode}'. Supported modes are: {self.valid_modes()}")

        if strategy.name not in self.strategies:
            self.strategies[strategy.name] = strategy
    

    def run(self) -> dict[str, TradingStats]:
        """
        Run the simulation to obtain trading statistics.

        Returns
        --------
        retval: dict[str, TradingStats]
            Dictionary of TradingStats by each strategy name.
        """
        results: dict[str, TradingStats] = {}
        for name, strategy in self.strategies.items():
            results[name] = self.simulate_strategy(strategy)

        return results


    def simulate_strategy(self, strategy_info):
        total_pnl = 0
        total_volume = 0
        max_drawdown = 0
        position_flips = 0
        holding_times = {}
        current_position = {}

        for instrument, actions in strategy_info['actions'].items():
            for action, candle in zip(actions, self.candles[instrument]):
                trade_price = candle.close if strategy_info['mode'] == 'close' else (
                    candle.avg_buy_price if action.quantity > 0 else candle.avg_sell_price
                )

                pnl_change = action.quantity * trade_price
                total_pnl += pnl_change
                total_volume += abs(action.quantity * trade_price)

                if instrument not in current_position:
                    current_position[instrument] = 0
                    holding_times[instrument] = 0

                if np.sign(action.quantity) != np.sign(current_position[instrument]):
                    position_flips += 1

                current_position[instrument] += action.quantity
                holding_times[instrument] += 1

                max_drawdown = min(max_drawdown, total_pnl)

        return total_pnl, total_volume, max_drawdown, position_flips, holding_times


    def calc_sharpe_ratio(self, pnl):
        return np.mean(pnl) / np.std(pnl) if np.std(pnl) != 0 else 0

    def calc_sortino_ratio(self, pnl):
        downside_std = np.std([p for p in pnl if p < 0])
        return np.mean(pnl) / downside_std if downside_std != 0 else 0
