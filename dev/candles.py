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
    - open
    - high
    - low
    - close
    - avg_buy_price
    - avg_sell_price
    - buy_volume
    - sell_volume
    """

    OPEN = "open"
    CLOSE = "close"
    HIGH = "high"
    LOW = "low"
    AVG_BUY_PRICE = "avg_buy_price"
    AVG_SELL_PRICE = "avg_sell_price"
    BUY_VOLUME = "buy_volume"
    SELL_VOLUME = "sell_volume"

    data: pd.DataFrame
    window_ms: int
    length: int

    def get_candle_at(self, index: int) -> pd.Series:
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
        mdata.trades["timestamp"] = pd.to_datetime(
            mdata.trades["local_timestamp"], unit="us"
        )
        # mdata.lob['timestamp'] = pd.to_datetime(mdata.lob['local_timestamp'], unit='us')

        mdata.trades.set_index("timestamp", inplace=True)
        # mdata.lob.set_index('timestamp', inplace=True)

    return data


def generate_candles(
    data: dict[str, MarketData], window_ms: int
) -> dict[str, CandleSeries]:
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
            instr: candles
            for instr, candles in zip(
                data.keys(),
                executor.map(_gen_cnd, data.values(), [window_ms] * len(data)),
            )
        }


# Helper to generate candles for single instrument
def _gen_cnd(md: MarketData, window_ms: int) -> CandleSeries:
    data: pd.DataFrame = _generate_candles_dataframe(md, window_ms)
    return CandleSeries(
        data=data,
        window_ms=window_ms,
        length=len(data),
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

    # Resample data to calculate OHLC for each window
    ohlc = data.trades.resample(f"{window_ms}ms").agg(
        {
            "price": ["first", "max", "min", "last"],
        }
    )
    # NOTE: assumtion
    # Fill NaN values with 0, e.g. when no trades occurred in a window
    ohlc = ohlc.fillna(0)

    # Rename OHLC
    ohlc.columns = pd.Index(["open", "high", "low", "close"])

    # Calculate buy and sell volumes
    buy_volume = (
        data.trades[data.trades["side"] == "buy"]
        .resample(f"{window_ms}ms")["amount"]
        .sum()
    )
    sell_volume = (
        data.trades[data.trades["side"] == "sell"]
        .resample(f"{window_ms}ms")["amount"]
        .sum()
    )

    # Calculate average buy and sell prices
    avg_buy_price = (
        data.trades[data.trades["side"] == "buy"]
        .resample(f"{window_ms}ms")["price"]
        .mean()
    )
    avg_sell_price = (
        data.trades[data.trades["side"] == "sell"]
        .resample(f"{window_ms}ms")["price"]
        .mean()
    )

    # NOTE: assumtion
    # Fill NaN values with 0, e.g. when no trades occurred in a window
    buy_volume = buy_volume.fillna(0)
    sell_volume = sell_volume.fillna(0)
    avg_buy_price = avg_buy_price.fillna(0)
    avg_sell_price = avg_sell_price.fillna(0)

    # Combine all data
    candles = pd.concat(
        [ohlc, buy_volume, sell_volume, avg_buy_price, avg_sell_price], axis=1
    )

    candles.columns = pd.Index(
        [
            CandleSeries.OPEN,
            CandleSeries.HIGH,
            CandleSeries.LOW,
            CandleSeries.CLOSE,
            CandleSeries.BUY_VOLUME,
            CandleSeries.SELL_VOLUME,
            CandleSeries.AVG_BUY_PRICE,
            CandleSeries.AVG_SELL_PRICE,
        ]
    )

    return candles
