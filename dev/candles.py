from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from typing import *
import pandas as pd
from marketdata import MarketData

@dataclass
class CandleSeries:
    """
    Candle represents OLHC candle. CandleSeries stores pandas.DataFrame with trading statistics.  
    Columns in DataFrame:
    - timestamp
    - open
    - high
    - low
    - close
    - avg_buy_price
    - avg_sell_price
    - buy_volume
    - sell_volume
    """
    TIMESTAMP = 'timestamp'
    OPEN = 'open'
    CLOSE = 'close'
    HIGH = 'high'
    LOW = 'low'
    AVG_BUY_PRICE = 'avg_buy_price'
    AVG_SELL_PRICE = 'avg_sell_price'
    BUY_VOLUME = 'buy_volume'
    SELL_VOLUME = 'sell_volume'

    data: pd.DataFrame
    window_ms: int

    def get_candle_at(self, index: int, column: str) -> pd.Series: 
        return self.data.iloc[index]

    def get_value_at(self, index: int, column: str) -> Any:
        return self.data.iloc[index][column]


def _process_market_data(data: dict[str, MarketData]):
    """
    Process the market data by converting the local_timestamp column in microseconds to a datetime object
    and setting it as the index of the DataFrame.

    Parameters
    --------
    data: dict[str, marketdata.MarketData] 
        Dictionary of MarketData, indexed by trading insrument name.
    """
    for mdata in data.values():
        mdata.trades['timestamp'] = pd.to_datetime(mdata.trades['local_timestamp'], unit='us')
        # mdata.lob['timestamp'] = pd.to_datetime(mdata.lob['local_timestamp'], unit='us')

        mdata.trades.set_index('timestamp', inplace=True)
        # mdata.lob.set_index('timestamp', inplace=True)

    return data


def generate_candles(data: dict[str, MarketData], window_ms: int) -> dict[str, CandleSeries]:
    """
    Generate CandleSeries from market data for provided trading instruments.

    Parameters
    --------
    data: dict[str, marketdata.MarketData]
        Market data for trading insruments.
    window_ms: int 
        Window size for data sampling in milliseconds.

    Returns
    --------
    retval: dict[str, CandleSeries]
        Dictionary of CandleSeries, indexed by trading insrument name.
    """
    data = _process_market_data(data)

    with ProcessPoolExecutor() as executor:
        # Generate candles for each instrument in parallel
        return {
            instr:candles 
            for instr, candles in zip(
                data.keys(), 
                executor.map(_gen_cnd, data.values(), [window_ms]*len(data))
            )
        }

# helper to generate candles for single instrument
def _gen_cnd(md: MarketData, window_ms: int) -> CandleSeries:
    return CandleSeries(
        data=_generate_candles_dataframe(md, window_ms),
        window_ms=window_ms,
    )

def _generate_candles_dataframe(data: MarketData, window_ms: int) -> pd.DataFrame:
    """
    Generate pandas.DataFrame for CandleSeries.

    Parameters
    --------
    data: marketdata.MarketData 
        Market data for trading insrument.
    window_ms: int 
        Window size for data sampling in milliseconds.

    Returns
    --------
    retval: pandas.DataFrame
        Data for CandleSeries.
    """
    sampled_trades = data.trades.resample(f'{window_ms}ms')

    ohlc_data = sampled_trades['price'].ohlc()
    
    buy_avg_price = sampled_trades.apply(lambda x: np.average(x['price'][x['side'] == 'buy'], weights=x['amount'][x['side'] == 'buy']))
    sell_avg_price = sampled_trades.apply(lambda x: np.average(x['price'][x['side'] == 'sell'], weights=x['amount'][x['side'] == 'sell']))
    buy_volume = sampled_trades.apply(lambda x: x['amount'][x['side'] == 'buy'].sum())
    sell_volume = sampled_trades.apply(lambda x: x['amount'][x['side'] == 'sell'].sum())

    candles = pd.concat([ohlc_data, buy_avg_price, sell_avg_price, buy_volume, sell_volume], axis=1)
    candles.columns = pd.Index([
        CandleSeries.OPEN, CandleSeries.HIGH, CandleSeries.LOW, CandleSeries.CLOSE,  
        CandleSeries.AVG_BUY_PRICE, CandleSeries.AVG_SELL_PRICE, 
        CandleSeries.BUY_VOLUME, CandleSeries.SELL_VOLUME,
    ])

    return candles