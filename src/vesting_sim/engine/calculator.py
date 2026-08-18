"""Deterministic Valuation and Cashflow Calculator."""

from __future__ import annotations

from decimal import Decimal

from vesting_sim.domain.models import EquityGrant
from vesting_sim.domain.schedules import generate_vesting_schedule


def calculate_realized_grant_value(
    grant: EquityGrant,
    monthly_prices: dict[int, Decimal],
) -> Decimal:
    """Calculates total dollar value realized from an equity grant over time.

    Args:
        grant: The equity grant to evaluate.
        monthly_prices: Mapping from month_offset (1..48) to stock price in USD.

    Returns:
        Total dollar payout with exact decimal precision.
    """
    tranches = generate_vesting_schedule(grant)
    total_realized = Decimal("0.00")

    for tranche in tranches:
        price = monthly_prices.get(tranche.month_offset, grant.grant_price_usd)
        tranche_value = Decimal(tranche.shares) * price
        total_realized += tranche_value

    return total_realized
