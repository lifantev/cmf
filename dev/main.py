import pprint
import marketdata as md
import candles as cnd
import strategies as strat
import simulator as sim
import time
import concurrent.futures


def _parallel_strategy_generation(candles):
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [
            executor.submit(
                strat.generate_random_strategy, strat.Strategy.AVERAGE, candles
            ),
            executor.submit(
                strat.generate_knowfuture_strategy,
                strat.Strategy.CLOSE,
                "tradingpro",
                candles,
            ),
            executor.submit(
                strat.generate_knowfuture_strategy,
                strat.Strategy.AVERAGE,
                "tradingpro2",
                candles,
            ),
        ]
        random_strat_by_avg_price, w_strat_by_close_price, w_strat_by_avg_price = [
            future.result() for future in futures
        ]
    return random_strat_by_avg_price, w_strat_by_close_price, w_strat_by_avg_price


if __name__ == "__main__":
    # Expects the following files to be present in the specified path:
    #         bbo_1000pepeusdt.csv,
    #         trades_1000pepeusdt.csv,
    #         bbo_1000dogeusdt.csv,
    #         trades_1000dogeusdt.csv
    print("Loading market data")
    data: dict[str, md.MarketData] = md.load_market_data("./")

    print("Generating candles")
    candles: dict[str, cnd.CandleSeries] = cnd.generate_candles(data, window_ms=600_000)

    print("Generating strategies")
    start_time = time.time()
    random_strat_by_avg_price, w_strat_by_close_price, w_strat_by_avg_price = (
        _parallel_strategy_generation(candles)
    )

    tsim = sim.TradingSimulator(candles)
    tsim.add_strategy(random_strat_by_avg_price)
    tsim.add_strategy(w_strat_by_close_price)
    tsim.add_strategy(w_strat_by_avg_price)

    print("Running trading simulator")
    stats: dict[str, sim.TradingStats] = tsim.run()

    print("Results")
    pprint.pprint(stats, indent=4, depth=4)
