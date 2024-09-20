import unittest
import marketdata as md
import candles as cnd
import strategies as strat
import simulator as sim


class TestTradingSimulator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load data and generate candle series."""
        cls.data = md.load_market_data("./")

    def test_random_strategy_pnl_and_sharpe(self):
        """Test that random strategy results in low PnL and Sharpe ratio."""
        window_ms = 10_000
        candles = cnd.generate_candles(self.data, window_ms)

        random_strat = strat.generate_random_strategy(strat.Strategy.AVERAGE, candles)

        tsim = sim.TradingSimulator(candles)
        tsim.add_strategy(random_strat)

        stats = tsim.run()

        self.assertLess(
            stats[random_strat.name].pnl,
            3,
            "Random strategy should have low PnL. Expected < 0",
        )
        self.assertLess(
            stats[random_strat.name].sharpe_ratio,
            0.1,
            "Random strategy should have a low Sharpe ratio. Expected < 0.1",
        )

    def test_winning_strategy_sharpe(self):
        """Test that winning strategy results in high Sharpe ratio and positive PnL."""
        window_ms = 600_000
        candles = cnd.generate_candles(self.data, window_ms)

        winning_strat_by_close = strat.generate_knowfuture_strategy(
            strat.Strategy.CLOSE, "winning_close", candles
        )
        winning_strat_by_avg = strat.generate_knowfuture_strategy(
            strat.Strategy.AVERAGE, "winning_avg", candles
        )

        tsim = sim.TradingSimulator(candles)
        tsim.add_strategy(winning_strat_by_close)
        tsim.add_strategy(winning_strat_by_avg)

        stats = tsim.run()

        self.assertGreater(
            stats["winning_close"].pnl,
            15,
            "Winning strategy with close price should have positive PnL. Expected > 15",
        )
        self.assertGreater(
            stats["winning_close"].sharpe_ratio,
            1,
            "Winning strategy with close price should have a high Sharpe ratio. Expected > 1",
        )

        self.assertGreater(
            stats["winning_avg"].pnl,
            15,
            "Winning strategy with average price should have positive PnL. Expected > 15",
        )
        self.assertGreater(
            stats["winning_avg"].sharpe_ratio,
            1,
            "Winning strategy with average price should have a high Sharpe ratio. Expected > 1",
        )


if __name__ == "__main__":
    unittest.main()
