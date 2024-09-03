import marketdata as md
import candles as cnd

if __name__ == "__main__":
    data: dict[str, md.MarketData] = md.load_market_data('./')

    cnd.process_market_data(data)

    candles = cnd.generate_candles(data, window_ms=60000)

    print(candles)
    print(len(candles[md.DOGEUSDT].data))
