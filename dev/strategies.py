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
    CLOSE = 'close'
    AVERAGE = 'average'

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
    instruments: set[str],
    mode: str, 
    length: int, 
    max_quantity: int = 100,
    hold_probability: float = 0.33,
) -> Strategy:
    """
    Generates strategy that buys and sells contracts randomly.

    Parameters
    -----------
    instruments: set[str]
        List of instruments to trade.
    mode: str
        Trading mode, either 'close' or 'average'.
    length: int
        Length of actions vector.
    max_quantity: int
        Maximum quantity of contracts to buy or sell.
    hold_probability: float
        Probability of holding. Should be in range [0, 1].
    """
    if mode not in Strategy.valid_modes():
        raise ValueError(f"Invalid mode: {mode}. Valid modes: {Strategy.valid_modes()}")

    max_quantity = abs(max_quantity)
    hold_probability = hold_probability if 0 <= hold_probability <= 1 else 0.33
    actions_vector: list[Actions] = []

    for _ in range(length):
        actions: Actions = {}
        for instr in instruments:
            hold = 0 if random.random() < hold_probability else 1
            quantity = random.randint(-max_quantity, max_quantity)
            actions[instr] = Action(hold * quantity)
        actions_vector.append(actions)

    return Strategy(
        name=''.join(random.choices(string.ascii_lowercase, k=5)),
        mode=mode,
        actions_vector=actions_vector,
    )

def generate_cooltoknowfuture_strategy(
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
    """
    if mode not in Strategy.valid_modes():
        raise ValueError(f"Invalid mode: {mode}. Valid modes: {Strategy.valid_modes()}")

    candles_num = len(candles[list(candles.keys())[0]].data) if len(candles) > 0 else 0
    if any(len(candles[k].data) != candles_num for k in candles):
        raise ValueError('Candle series must have same length')

    actions_vector: list[Actions] = []
    curr_pos: dict[str, int] = {}
    next_pos: dict[str, int] = {}
    quantity = abs(quantity)

    for t in range(candles_num-1):
        actions: Actions = {}
        for instr, cndls in candles.items():
            if mode == Strategy.CLOSE:
                curr_pos[instr] = cndls.get_value_at(t, CandleSeries.CLOSE)
                next_pos[instr] = cndls.get_value_at(t+1, CandleSeries.CLOSE)
            elif mode == Strategy.AVERAGE:
                curr_pos[instr] = (cndls.get_value_at(t, CandleSeries.AVG_BUY_PRICE) + cndls.get_value_at(t, CandleSeries.AVG_SELL_PRICE)) / 2
                next_pos[instr]= (cndls.get_value_at(t+1, CandleSeries.AVG_BUY_PRICE) + cndls.get_value_at(t+1, CandleSeries.AVG_SELL_PRICE)) / 2
            
            if curr_pos[instr] <= next_pos[instr]:
                actions[instr] = Action(quantity)
            else:
                actions[instr] = Action(-quantity)
        actions_vector.append(actions)

    actions_vector.append({})

    return Strategy(
        name=name,
        mode=mode,
        actions_vector=actions_vector,
    )