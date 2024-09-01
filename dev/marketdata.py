from dataclasses import dataclass
import pandas as pd

PEPEUSDT = 'pepeusdt'
DOGEUSDT = 'dogeusdt'

@dataclass
class MarketData:
    """
    LOB and Trades dataframes of trading instrument.
    """
    lob: pd.DataFrame
    trades: pd.DataFrame

def load_market_data(path: str) -> dict[str, MarketData]:
    """
    Load market data in provided directory.

    Parameters
    --------
    path: str 
        Path to directory containing market data files.

    Returns
    --------
    retval: dict[str, MarketData]
        Dictionary of MarketData, indexed by trading insrument name.

    NOTES:
    --------
    Expects the following files to be present in the specified path:
        bbo_1000pepeusdt.csv, 
        trades_1000pepeusdt.csv, 
        bbo_1000dogeusdt.csv, 
        trades_1000dogeusdt.csv 
    """
    pepe_lob_file = "bbo_1000pepeusdt.csv"
    doge_lob_file = "bbo_dogeusdt.csv"
    pepe_trades_file = "trades_1000pepeusdt.csv"
    doge_trades_file = "trades_dogeusdt.csv"

    data = {}
    data[PEPEUSDT] = MarketData(
        lob=pd.read_csv(path + pepe_lob_file),
        trades=pd.read_csv(path + pepe_trades_file),
    )
    data[DOGEUSDT] = MarketData(
        lob=pd.read_csv(path + doge_lob_file),
        trades=pd.read_csv(path + doge_trades_file),
    )

    return data
