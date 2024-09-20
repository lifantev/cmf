from collections import defaultdict
import string, random
from dataclasses import dataclass
from candles import CandleSeries


@dataclass
class Action:
    """
    Trading action.
    Quantity is positive for buying and negative for selling, zero for holding.
    """

    quantity: int


# Action by instrument within single OHLC candle.
type Actions = dict[str, Action]


@dataclass
class Strategy:
    """
    Strategy represents a trading strategy.
    Mode is a trading mode, either 'close' or 'average'.
    All actions in actions vector with index T will be executed within OHLC candle with same index T.
    """

    CLOSE = "close"
    AVERAGE = "average"

    name: str
    mode: str
    actions_vector: list[Actions]

    @staticmethod
    def valid_modes() -> set[str]:
        """
        Valid trading modes.

        Returns
        --------
        retval: set[str]
            Valid modes.
        """
        return {Strategy.CLOSE, Strategy.AVERAGE}


def generate_random_strategy(
    mode: str,
    candles: dict[str, CandleSeries],
    max_quantity: int = 100,
    hold_probability: float = 0.33,
) -> Strategy:
    """
    Generates strategy that buys and sells contracts randomly.

    Parameters
    -----------
    mode: str
        Trading mode, either 'close' or 'average'.
    candles: dict[str, CandleSeries]
        Candles for all instruments.
    max_quantity: int
        Maximum quantity of contracts to buy or sell.
    hold_probability: float
        Probability of holding. Should be in range [0, 1].

    Returns
    --------
    retval: Strategy
    """
    if mode not in Strategy.valid_modes():
        raise ValueError(f"Invalid mode: {mode}. Valid modes: {Strategy.valid_modes()}")

    max_quantity = abs(max_quantity)
    hold_probability = hold_probability if 0 <= hold_probability <= 1 else 0.33
    # Find the maximum length among all candles
    max_length = max(candle.length for candle in candles.values())
    # Random name for the strategy
    strategy_name = "".join(random.choices(string.ascii_lowercase, k=5))

    # Generate random actions for each candle
    actions_vector: list[Actions] = [
        {
            instr: Action(
                0
                if random.random() < hold_probability
                else random.randint(-max_quantity, max_quantity)
            )
            for instr, candle in candles.items()
            if t < candle.length
        }
        for t in range(max_length)
    ]

    return Strategy(
        name=strategy_name,
        mode=mode,
        actions_vector=actions_vector,
    )


def generate_knowfuture_strategy(
    mode: str,
    name: str,
    candles: dict[str, CandleSeries],
    quantity: int = 100,
) -> Strategy:
    """
    Generates strategy that buys and sells contracts to maximize benefits. Knows the next OHLC candle state.

    Parameters
    -----------
    instruments: set[str]
        List of instruments to trade.
    mode: str
        Trading mode, either 'close' or 'average'.
    name: str
        Name of strategy.
    candles: dict[str, CandleSeries]
        Candles for each instrument.
    quantity: int
        Quantity of contracts to buy or sell.

    Returns
    --------
    retval: Strategy
    """
    if mode not in Strategy.valid_modes():
        raise ValueError(f"Invalid mode: {mode}. Valid modes: {Strategy.valid_modes()}")

    quantity = abs(quantity)
    # Get maximum candles length among all instruments
    max_length = max(candle.length for candle in candles.values())
    actions_vector: list[Actions] = []

    # Iterate through series
    for t in range(max_length - 1):
        actions: Actions = {}

        # Process each instrument's candles
        for instr, cndls in candles.items():
            if t >= cndls.length - 1:
                continue

            # Get the current and next position based on the trading mode
            if mode == Strategy.CLOSE:
                curr_val = cndls.get_value_at(t, CandleSeries.CLOSE)
                next_val = cndls.get_value_at(t + 1, CandleSeries.CLOSE)
            elif mode == Strategy.AVERAGE:
                # Raw average
                curr_val = (
                    cndls.get_value_at(t, CandleSeries.AVG_BUY_PRICE)
                    + cndls.get_value_at(t, CandleSeries.AVG_SELL_PRICE)
                ) / 2
                next_val = (
                    cndls.get_value_at(t + 1, CandleSeries.AVG_BUY_PRICE)
                    + cndls.get_value_at(t + 1, CandleSeries.AVG_SELL_PRICE)
                ) / 2

            actions[instr] = Action(quantity if curr_val <= next_val else -quantity)

        actions_vector.append(actions)

    return Strategy(
        name=name,
        mode=mode,
        actions_vector=actions_vector,
    )
