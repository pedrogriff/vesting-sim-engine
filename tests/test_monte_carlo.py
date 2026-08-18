"""Unit tests for Monte Carlo simulation and parallel batch processing."""

import unittest
from decimal import Decimal

from vesting_sim.domain.models import EquityGrant
from vesting_sim.engine.batch_processor import BatchSimulationEngine
from vesting_sim.engine.monte_carlo import MonteCarloSimulator


class TestMonteCarlo(unittest.TestCase):
    """Test suite for stochastic simulations and concurrency."""

    def test_gbm_price_path_properties(self) -> None:
        """Verifies price paths are positive and deterministic with fixed seed."""
        sim = MonteCarloSimulator(annual_drift=0.10, annual_volatility=0.20)
        path_1 = sim.generate_price_path(initial_price=100.0, seed=1234)
        path_2 = sim.generate_price_path(initial_price=100.0, seed=1234)

        self.assertEqual(len(path_1), 49)  # Month 0 + 48 months
        self.assertEqual(path_1, path_2)   # Seed reproducibility
        self.assertTrue(all(p > 0 for p in path_1))

    def test_single_grant_simulation(self) -> None:
        """Verifies percentile ordering (P10 <= P50 <= P90)."""
        grant = EquityGrant(
            grant_id="G-301",
            employee_id="E-701",
            total_shares=500,
            grant_price_usd=Decimal("150.00"),
        )
        sim = MonteCarloSimulator()
        result = sim.simulate_grant(grant, num_paths=200, base_seed=42)

        self.assertEqual(result.portfolio_total_shares, 500)
        self.assertEqual(result.path_count, 200)
        self.assertLessEqual(result.p10_value_usd, result.p50_value_usd)
        self.assertLessEqual(result.p50_value_usd, result.p90_value_usd)

    def test_parallel_batch_simulation(self) -> None:
        """Verifies multi-process execution produces expected results."""
        grants = [
            EquityGrant(grant_id=f"G-{i}", employee_id=f"E-{i}", total_shares=100 + i)
            for i in range(20)
        ]

        engine = BatchSimulationEngine(max_workers=2)
        results, elapsed = engine.run_batch_simulation(grants, num_paths_per_grant=50)

        self.assertEqual(len(results), 20)
        self.assertGreater(elapsed, 0.0)
        for i, res in enumerate(results):
            self.assertEqual(res.portfolio_total_shares, 100 + i)


if __name__ == "__main__":
    unittest.main()
