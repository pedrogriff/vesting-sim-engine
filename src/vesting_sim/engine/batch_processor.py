"""Concurrent Multi-Process Batch Simulation Engine."""

from __future__ import annotations

import os
import time
from concurrent.futures import ProcessPoolExecutor

from vesting_sim.domain.models import EquityGrant, SimulationResult
from vesting_sim.engine.monte_carlo import MonteCarloSimulator


def _worker_simulate_chunk(
    grants: list[EquityGrant],
    num_paths_per_grant: int,
    base_seed: int,
) -> list[SimulationResult]:
    """Top-level worker function executing simulation on a chunk of grants."""
    simulator = MonteCarloSimulator()
    results: list[SimulationResult] = []
    for idx, grant in enumerate(grants):
        res = simulator.simulate_grant(
            grant,
            num_paths=num_paths_per_grant,
            base_seed=base_seed + idx,
        )
        results.append(res)
    return results


class BatchSimulationEngine:
    """Distributes large-scale portfolio simulations across CPU worker pools."""

    def __init__(self, max_workers: int | None = None) -> None:
        """Initializes with available CPU core count."""
        self.max_workers = max_workers or (os.cpu_count() or 4)

    def run_batch_simulation(
        self,
        grants: list[EquityGrant],
        num_paths_per_grant: int = 500,
        base_seed: int = 1000,
    ) -> tuple[list[SimulationResult], float]:
        """Simulates thousands of grants in parallel across all CPU cores.

        Returns:
            Tuple of (list of results, total elapsed seconds).
        """
        if not grants:
            return [], 0.0

        t0 = time.perf_counter()

        # Chunk the grants across workers
        chunk_size = max(1, len(grants) // self.max_workers)
        chunks = [
            grants[i : i + chunk_size]
            for i in range(0, len(grants), chunk_size)
        ]

        results: list[SimulationResult] = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [
                executor.submit(
                    _worker_simulate_chunk,
                    chunk,
                    num_paths_per_grant,
                    base_seed + (i * 10_000),
                )
                for i, chunk in enumerate(chunks)
            ]

            for future in futures:
                results.extend(future.result())

        elapsed = time.perf_counter() - t0
        return results, elapsed
