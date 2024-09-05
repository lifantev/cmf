import string, random
from dataclasses import dataclass
import marketdata as md

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


def generate_random_strategy(instruments: list[str], mode: str, length: int) -> Strategy:
    """
    Generates strategy that buys and sells random amount of contracts.

    Parameters
    -----------
    instruments: list[str]
        List of instruments to trade.
    mode: str
        Trading mode, either 'close' or 'average'.
    """
    if mode not in Strategy.valid_modes():
        raise ValueError(f"Invalid mode: {mode}. Valid modes: {Strategy.valid_modes()}")

    instruments = [md.DOGEUSDT, md.PEPEUSDT]

    actions_vector: list[Actions] = []
    for i in range(length):
        actions: Actions = {}

    return Strategy(
        name=''.join(random.choices(string.ascii_lowercase, k=5)),
        mode=mode,
        actions_vector=actions_vector,
    )