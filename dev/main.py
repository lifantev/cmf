import pprint
import marketdata as md
import candles as cnd
import strategies as strat
import simulator as sim

if __name__ == "__main__":

    data: dict[str, md.MarketData] = md.load_market_data('./')

    candles: dict[str, cnd.CandleSeries] = cnd.generate_candles(data, window_ms=600_000)
    length = len(candles[md.DOGEUSDT].data)

    random_strat = strat.generate_random_strategy({md.DOGEUSDT, md.PEPEUSDT}, strat.Strategy.AVERAGE, length)
    winning_strat = strat.generate_cooltoknowfuture_strategy(strat.Strategy.CLOSE, 'iamatradinggod', candles)

    tsim = sim.TradingSimulator(candles)    
    tsim.add_strategy(random_strat)
    tsim.add_strategy(winning_strat)

    stats: dict[str, sim.TradingStats] = tsim.run()

    pprint.pprint(stats, indent=4, depth=4)