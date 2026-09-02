"""Benchmark: Parallel Multi-Process Simulation Engine vs. Single-Threaded Execution.

Measures Monte Carlo simulation throughput across thousands of employee equity portfolios.
"""

from __future__ import annotations

import os
import random
import time
from decimal import Decimal

from vesting_sim.domain.models import EquityGrant, GrantType, ScheduleType
from vesting_sim.engine.batch_processor import BatchSimulationEngine
from vesting_sim.engine.monte_carlo import MonteCarloSimulator


def generate_synthetic_workforce(n: int) -> list[EquityGrant]:
    """Generates a realistic synthetic enterprise workforce equity portfolio."""
    schedules = list(ScheduleType)
    types = [GrantType.RSU, GrantType.RSU, GrantType.RSU, GrantType.PSU]
    grants: list[EquityGrant] = []

    for i in range(n):
        shares = random.randint(100, 5_000)
        sched = random.choice(schedules)
        g_type = random.choice(types)
        multiplier = Decimal("1.25") if g_type == GrantType.PSU else Decimal("1.0")

        grants.append(
            EquityGrant(
                grant_id=f"G-SYNTH-{i:06d}",
                employee_id=f"EMP-{i:06d}",
                total_shares=shares,
                grant_type=g_type,
                schedule_type=sched,
                grant_price_usd=Decimal("175.50"),
                performance_multiplier=multiplier,
            )
        )
    return grants


def run_benchmark() -> None:
    num_grants = 2_000
    paths_per_grant = 200
    cpu_cores = os.cpu_count() or 4

    print("=" * 75)
    print("VestingSim: High-Throughput Monte Carlo Simulation Benchmark")
    print("=" * 75)
    print(f"Workforce Portfolios: {num_grants:,d} employees")
    print(f"Paths per Portfolio:  {paths_per_grant:,d} trajectories (48 months each)")
    print(f"Total Path Steps:     {num_grants * paths_per_grant * 48:,d} discrete step valuations")
    print(f"Available CPU Cores:  {cpu_cores}")
    print("-" * 75)

    grants = generate_synthetic_workforce(num_grants)

    # 1. Single-Threaded Sequential Simulation
    simulator = MonteCarloSimulator()
    t0 = time.perf_counter()
    for idx, g in enumerate(grants):
        _ = simulator.simulate_grant(g, num_paths=paths_per_grant, base_seed=100 + idx)
    seq_time = time.perf_counter() - t0

    # 2. Parallel Multi-Process Simulation
    engine = BatchSimulationEngine(max_workers=cpu_cores)
    _, par_time = engine.run_batch_simulation(
        grants,
        num_paths_per_grant=paths_per_grant,
        base_seed=100,
    )

    speedup = seq_time / par_time if par_time > 0 else 0
    seq_throughput = num_grants / seq_time
    par_throughput = num_grants / par_time

    print(f"{'Execution Mode':<30} | {'Elapsed Time (s)':<18} | {'Throughput (grants/s)':<20}")
    print("-" * 75)
    print(f"{'1. Sequential (Single-Thread)':<30} | {seq_time:<18.4f} | {seq_throughput:<20.1f}")
    print(f"{'2. Parallel (Multi-Core Pool)':<30} | {par_time:<18.4f} | {par_throughput:<20.1f}")
    print("-" * 75)
    print(f"Concurrency Speedup: {speedup:.2f}x faster using {cpu_cores} worker processes!")
    print("=" * 75)


if __name__ == "__main__":
    run_benchmark()
