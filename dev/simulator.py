from collections import defaultdict
from dataclasses import dataclass
import numpy as np
from candles import CandlesSeries
from strategies import Strategy

@dataclass
class TradingStats:
    pnl: float
    traded_volume: int
    max_drawdown: float
    avg_holding_time: dict[str, float] 
    position_flips: dict[str, int]
    sharpe_ratio: float 
    sortino_ratio: float 

class TradingSimulator:
    """
    TradingSimulator simulates trading based on added strategies and market data.
    """

    def __init__(self, candles: dict[str, CandlesSeries]):
        """
        Parameters
        -----------
        candles: dict[str, CandlesSeries]
           Candle series for each instrument. Series must be not empty.
        """
        if not candles:
            raise ValueError('Candle series must be provided')

        candles_num = len(candles[list(candles.keys())[0]])
        if candles_num < 1:
            raise ValueError('Candle series must have at least one candle')
        if any(len(candles[k])!= candles_num for k in candles):
            raise ValueError('Candle series must have same length')

        self.candles = candles
        self.candles_number = candles_num
        self.strategies: dict[str, Strategy] = {} # {strategy_name: strategy}


    def add_strategy(self, strategy: Strategy):
        """
        Add strategy to the simulator. Uniq by strategy name.

        Parameters
        -----------
        strategy: Strategy
            Strategy to add for the simulator.
        """
        if strategy.mode not in Strategy.valid_modes():
            raise ValueError(f"Unsupported mode '{strategy.mode}'. Supported modes are: {Strategy.valid_modes()}")
        if len(strategy.actions_vector)!= self.candles_number:
            raise ValueError(
                f"Invalid actions number for strategy. Expected {self.candles_number}, got {len(strategy.actions_vector)}"
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
            results[name] = self.__simulate_strategy__(strategy)

        return results


    def __simulate_strategy__(self, strategy: Strategy) -> TradingStats:
        """
        Simulate a single strategy.
        """
        pnl = 0
        pnl_series = np.zeros(self.candles_number)
        traded_volume = 0
        max_drawdown = 0
        position_flips = defaultdict(int)
        avg_holding_time = defaultdict(int)
        curr_positions = defaultdict(int)

        for t in range(self.candles_number): # iterate over candles
            actions = strategy.actions_vector[t]

            for instr, action in actions.items(): # iterate over instruments and their action within this candle
                price = self.__trading_price__(instr, strategy.mode, action.quantity, t)             
                traded_volume += action.quantity

                if action.quantity > 0: # buy
                    pnl -= price * action.quantity 
                    if curr_positions[instr] <= 0:
                        curr_positions[instr] = 1
                        position_flips[instr] += 1
                elif action.quantity < 0: # sell
                    pnl += price * action.quantity 
                    if curr_positions[instr] >= 0:
                        curr_positions[instr] = -1
                        position_flips[instr] += 1
                else:  # hold
                    avg_holding_time[instr] += 1 
        
            max_pnl = max(max_pnl, pnl)
            max_drawdown = max(max_drawdown, max_pnl - pnl)
            pnl_series[t] = pnl

        sharpe_ratio = calc_sharpe_ratio(pnl_series)
        sortino_ratio = calc_sortino_ratio(pnl_series)

        return TradingStats(
            pnl=pnl,
            traded_volume=traded_volume,
            max_drawdown=max_drawdown,
            position_flips=position_flips,
            avg_holding_time={instr: (holds/self.candles_num) for instr, holds in avg_holding_time},
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio
        )


    def __trading_price__(self, instrument: str, mode: str, quantity: int, t: int) -> float:
        """
        Get trading price for instrument's candle at index T based on mode and quantity.
        """
        if instrument not in self.candles:
            raise ValueError(f"Instrument '{instrument}' is not contained in trading simulator candles")

        if mode == Strategy.CLOSE:
            return self.candles[instrument][t][CandlesSeries.CLOSE]
        elif mode == Strategy.AVERAGE:
            if quantity > 0: # buy
                return self.candles[instrument][t][CandlesSeries.AVG_BUY_PRICE]
            elif quantity < 0: # sell
                return self.candles[instrument][t][CandlesSeries.AVG_SELL_PRICE]
            return 0

        raise ValueError(f"Unsupported mode '{mode}'. Supported modes are: {Strategy.valid_modes()}")


def calc_sharpe_ratio(pnl):
    return np.mean(pnl) / np.std(pnl) if np.std(pnl) != 0 else 0

def calc_sortino_ratio(pnl):
    downside_std = np.std([p for p in pnl if p < 0])
    return np.mean(pnl) / downside_std if downside_std != 0 else 0
