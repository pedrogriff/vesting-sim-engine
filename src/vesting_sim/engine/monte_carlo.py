"""High-Performance Monte Carlo Geometric Brownian Motion (GBM) Simulation."""

from __future__ import annotations

import math
import random
import time
from decimal import Decimal

from vesting_sim.domain.models import EquityGrant, SimulationResult
from vesting_sim.domain.schedules import generate_vesting_schedule


class MonteCarloSimulator:
    """Simulates equity price trajectories and calculates portfolio risk distributions."""

    def __init__(
        self,
        annual_drift: float = 0.08,        # Expected annual growth rate (e.g. 8%)
        annual_volatility: float = 0.25,   # Annualized standard deviation (e.g. 25%)
        months: int = 48,
    ) -> None:
        """Initializes simulation parameters."""
        self.annual_drift = annual_drift
        self.annual_volatility = annual_volatility
        self.months = months
        self.dt = 1.0 / 12.0  # Monthly time step in years

    def generate_price_path(self, initial_price: float, seed: int | None = None) -> list[float]:
        """Generates a single 48-month Geometric Brownian Motion price trajectory."""
        rng = random.Random(seed)
        prices = [initial_price]

        # Drift and diffusion constants
        drift_term = (self.annual_drift - 0.5 * (self.annual_volatility**2)) * self.dt
        vol_term = self.annual_volatility * math.sqrt(self.dt)

        curr = initial_price
        for _ in range(1, self.months + 1):
            # Standard Gaussian random variable Z ~ N(0, 1) via Box-Muller / normalvariate
            z = rng.normalvariate(0.0, 1.0)
            curr = curr * math.exp(drift_term + vol_term * z)
            prices.append(curr)

        return prices

    def simulate_grant(
        self,
        grant: EquityGrant,
        num_paths: int = 1_000,
        base_seed: int | None = 42,
    ) -> SimulationResult:
        """Simulates grant across num_paths and computes distribution statistics."""
        t_start = time.perf_counter()
        tranches = generate_vesting_schedule(grant)
        total_shares = grant.effective_shares()

        if total_shares == 0 or num_paths <= 0:
            return SimulationResult(
                portfolio_total_shares=0,
                expected_value_usd=Decimal("0.00"),
                p10_value_usd=Decimal("0.00"),
                p50_value_usd=Decimal("0.00"),
                p90_value_usd=Decimal("0.00"),
                path_count=0,
                execution_time_seconds=0.0,
            )

        initial_price = float(grant.grant_price_usd)
        path_values: list[float] = []

        # Vectorized path calculation
        for p in range(num_paths):
            seed = (base_seed + p) if base_seed is not None else None
            price_path = self.generate_price_path(initial_price, seed=seed)

            total_path_value = 0.0
            for tranche in tranches:
                # month_offset is 1-indexed in price_path (0 is month 0)
                m = tranche.month_offset
                price_at_vest = price_path[m] if m < len(price_path) else price_path[-1]
                total_path_value += tranche.shares * price_at_vest

            path_values.append(total_path_value)

        # Compute percentiles
        path_values.sort()
        expected = sum(path_values) / len(path_values)

        p10_idx = int(0.10 * len(path_values))
        p50_idx = int(0.50 * len(path_values))
        p90_idx = int(0.90 * len(path_values))

        t_elapsed = time.perf_counter() - t_start

        return SimulationResult(
            portfolio_total_shares=total_shares,
            expected_value_usd=Decimal(f"{expected:.2f}"),
            p10_value_usd=Decimal(f"{path_values[p10_idx]:.2f}"),
            p50_value_usd=Decimal(f"{path_values[p50_idx]:.2f}"),
            p90_value_usd=Decimal(f"{path_values[p90_idx]:.2f}"),
            path_count=num_paths,
            execution_time_seconds=t_elapsed,
        )
