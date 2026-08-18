"""Immutable Domain Value Objects and Entity Models for Equity Grants."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum


class GrantType(StrEnum):
    """Classification of equity grants."""

    GSU = "GSU"  # Standard Google Stock Unit
    PSU = "PSU"  # Performance Stock Unit with multiplier


class ScheduleType(StrEnum):
    """Standard corporate equity vesting schedules."""

    FRONT_LOADED_33_33_22_12 = "FRONT_LOADED_33_33_22_12"  # Google front-loaded schedule
    STANDARD_4_YEAR_CLIFF = "STANDARD_4_YEAR_CLIFF"        # 25% at month 12, then monthly
    EVEN_MONTHLY_4_YEAR = "EVEN_MONTHLY_4_YEAR"            # 1/48th per month
    EVEN_QUARTERLY_4_YEAR = "EVEN_QUARTERLY_4_YEAR"        # 1/16th per quarter


@dataclass(frozen=True)
class VestingTranche:
    """A single deterministic vesting event."""

    period_index: int
    month_offset: int
    shares: int
    target_weight: Decimal


@dataclass(frozen=True)
class EquityGrant:
    """An individual equity compensation grant awarded to an employee."""

    grant_id: str
    employee_id: str
    total_shares: int
    grant_type: GrantType = GrantType.GSU
    schedule_type: ScheduleType = ScheduleType.FRONT_LOADED_33_33_22_12
    grant_price_usd: Decimal = field(default_factory=lambda: Decimal("150.00"))
    performance_multiplier: Decimal = field(default_factory=lambda: Decimal("1.00"))

    def effective_shares(self) -> int:
        """Returns total shares adjusted by the performance multiplier (for PSUs)."""
        if self.grant_type == GrantType.PSU:
            adjusted = Decimal(self.total_shares) * self.performance_multiplier
            return int(adjusted)
        return self.total_shares


@dataclass(frozen=True)
class SimulationResult:
    """Aggregated portfolio valuation statistics across Monte Carlo paths."""

    portfolio_total_shares: int
    expected_value_usd: Decimal
    p10_value_usd: Decimal
    p50_value_usd: Decimal
    p90_value_usd: Decimal
    path_count: int
    execution_time_seconds: float
