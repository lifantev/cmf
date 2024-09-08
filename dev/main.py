import pprint
import marketdata as md
import candles as cnd
import strategies as strat
import simulator as sim

if __name__ == "__main__":

    data: dict[str, md.MarketData] = md.load_market_data("./")

    print("Generating candles")
    candles: dict[str, cnd.CandleSeries] = cnd.generate_candles(data, window_ms=600_000)

    print("Generating strategies")
    random_strat_by_avg_price = strat.generate_random_strategy(
        strat.Strategy.AVERAGE, candles
    )
    w_strat_by_close_price = strat.generate_cooltoknowfuture_strategy(
        strat.Strategy.CLOSE, "iamatradingpro", candles
    )
    w_strat_by_avg_price = strat.generate_cooltoknowfuture_strategy(
        strat.Strategy.AVERAGE, "iamatradingproisaid", candles
    )

    tsim = sim.TradingSimulator(candles)
    tsim.add_strategy(random_strat_by_avg_price)
    tsim.add_strategy(w_strat_by_close_price)
    tsim.add_strategy(w_strat_by_avg_price)

    print("Running trading simulator")
    stats: dict[str, sim.TradingStats] = tsim.run()

    print("Results")
    pprint.pprint(stats, indent=4, depth=4)
