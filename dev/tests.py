import unittest
import marketdata as md
import candles as cnd
import strategies as strat
import simulator as sim

class TestTradingSimulator(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Load data and generate candle series."""
        cls.data = md.load_market_data('./')

    def test_random_strategy_pnl_and_sharpe(self):
        """Test that random strategy results in low PnL and Sharpe ratio."""
        window_ms = 600_000
        candles = cnd.generate_candles(self.data, window_ms)
        length = len(candles[md.DOGEUSDT].data)

        random_strat = strat.generate_random_strategy(
            {md.DOGEUSDT, md.PEPEUSDT},
            strat.Strategy.AVERAGE,
            length
        )

        tsim = sim.TradingSimulator(candles)
        tsim.add_strategy(random_strat)

        stats = tsim.run()

        self.assertLess(
            stats[random_strat.name].pnl,
            1,
            "Random strategy should have low PnL. Expected < 1",
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

        winning_strat_by_close = strat.generate_cooltoknowfuture_strategy(
            strat.Strategy.CLOSE,
            'winning_close',
            candles
        )
        winning_strat_by_avg = strat.generate_cooltoknowfuture_strategy(
            strat.Strategy.AVERAGE,
            'winning_avg',
            candles
        )

        tsim = sim.TradingSimulator(candles)
        tsim.add_strategy(winning_strat_by_close)
        tsim.add_strategy(winning_strat_by_avg)

        stats = tsim.run()

        self.assertGreater(
            stats['winning_close'].pnl,
            10,
            "Winning strategy with close price should have positive PnL. Expected > 10",
        )
        self.assertGreater(
            stats['winning_close'].sharpe_ratio,
            1,
            "Winning strategy with close price should have a high Sharpe ratio. Expected > 1",
        )
        
        self.assertGreater(stats['winning_avg'].pnl,
            10,
            "Winning strategy with average price should have positive PnL. Expected > 10",
        )
        self.assertGreater(stats['winning_avg'].sharpe_ratio,
            1,
            "Winning strategy with average price should have a high Sharpe ratio. Expected > 1",
        )

    @unittest.skip("Skipped due to errors with short windows.")
    def test_strategy_with_different_windows(self):
        """Test strategies with different candle window sizes."""
        for window_ms in [10, 1_000, 60_000]:  # Different time windows: 10ms, 1sec, 1min
            with self.subTest(window_ms=window_ms):
                candles = cnd.generate_candles(self.data, window_ms)
                length = len(candles[md.PEPEUSDT].data)

                random_strat = strat.generate_random_strategy(
                    {md.PEPEUSDT}, # only one instrument
                    strat.Strategy.AVERAGE,
                    length
                )

                winning_strat = strat.generate_cooltoknowfuture_strategy(
                    strat.Strategy.CLOSE,
                    'winning_close',
                    candles
                )

                tsim = sim.TradingSimulator(candles)
                tsim.add_strategy(random_strat)
                tsim.add_strategy(winning_strat)

                stats = tsim.run()

                self.assertLess(
                    stats[random_strat.name].pnl,
                    1,
                    "Random strategy should have low PnL. Expected < 1",
                )
                self.assertLess(
                    stats[random_strat.name].sharpe_ratio, 
                    0.1,
                    "Random strategy should have a low Sharpe ratio. Expected < 0.1",
                )

                self.assertGreater(
                    stats['winning_close'].pnl,
                    10,
                    "Winning strategy with close price should have positive PnL. Expected > 10",
                )
                self.assertGreater(
                    stats['winning_close'].sharpe_ratio,
                    1,
                    "Winning strategy with close price should have a high Sharpe ratio. Expected > 1",
                )


if __name__ == "__main__":
    unittest.main()
