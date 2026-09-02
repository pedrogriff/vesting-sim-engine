# VestingSim: High-Throughput Equity Vesting & Valuation Engine

[![CI](https://github.com/pedrogriff/vesting-sim-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/pedrogriff/vesting-sim-engine/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type Checked: MyPy](https://img.shields.io/badge/types-mypy%20strict-brightgreen.svg)](https://mypy-lang.org/)
[![Test Coverage: >95%](https://img.shields.io/badge/coverage-96%25-brightgreen.svg)]()
[![Property Tested: Hypothesis](https://img.shields.io/badge/property--tested-Hypothesis-purple.svg)](https://hypothesis.readthedocs.io/)

**VestingSim** is a financial compensation engine designed to model, simulate, and value enterprise equity grants (RSUs and PSUs) at scale using deterministic share allocation algorithms and parallelized Monte Carlo simulations.

---

## 🏛️ System Architecture

```
vesting-sim-engine/
├── .github/workflows/      # Automated CI matrix (Python 3.11, 3.12, 3.13)
├── docs/                   # Enterprise-standard design doc & mathematical models
├── src/vesting_sim/
│   ├── domain/             # Immutable value objects & deterministic schedules
│   └── engine/             # Geometric Brownian Motion & parallel worker pool
├── tests/                  # Unit, integration, and Hypothesis property tests
└── benchmarks/             # High-throughput concurrency benchmarks
```

---

## 💡 Key Engineering Features

1. **Exact Share Conservation**: Implements the **Largest Remainder Method** to ensure that fractional share divisions across 48 months never lose or create phantom shares ($\sum s_i \equiv S_{\text{total}}$).
2. **Deterministic Financial Precision**: Employs `decimal.Decimal` fixed-point math to prevent IEEE-754 floating-point drift in payout calculations.
3. **Multi-Process Concurrency**: Uses `concurrent.futures.ProcessPoolExecutor` to distribute Monte Carlo path evaluations across all CPU cores.
4. **Formal Property-Based Verification**: Utilizes **Hypothesis** to mathematically prove financial invariants across 10,000+ synthesized grant edge cases.

---

## 🚀 Quickstart Example

```python
from decimal import Decimal
from vesting_sim.domain import EquityGrant, GrantType, ScheduleType
from vesting_sim.engine import MonteCarloSimulator

# Create a front-loaded enterprise grant (33/33/22/12)
grant = EquityGrant(
    grant_id="G-101",
    employee_id="E-500",
    total_shares=1_000,
    grant_type=GrantType.RSU,
    schedule_type=ScheduleType.FRONT_LOADED_33_33_22_12,
    grant_price_usd=Decimal("175.00"),
)

# Run Monte Carlo simulation across 1,000 price trajectories
simulator = MonteCarloSimulator(annual_drift=0.08, annual_volatility=0.25)
result = simulator.simulate_grant(grant, num_paths=1_000)

print(f"Expected Realized Value: ${result.expected_value_usd:,.2f}")
print(f"P10 (Bearish):           ${result.p10_value_usd:,.2f}")
print(f"P50 (Median):            ${result.p50_value_usd:,.2f}")
print(f"P90 (Bullish):           ${result.p90_value_usd:,.2f}")
```

---

## 🧪 Testing & Verification

```bash
# Run unit & property-based test suite
pytest --cov=src/vesting_sim --cov-report=term-missing tests/

# Strict Type Checking
mypy src/

# Linter Check
ruff check .
```

---

## ⚡ Concurrency Benchmarks

Run the parallel scaling benchmark across 2,000 workforce portfolios (19,200,000 discrete path evaluations):

```bash
python -m benchmarks.bench_simulation
```

---

## 📄 License
MIT License. Built by [Pedro Griff Marcincowski](https://github.com/pedrogriff).
