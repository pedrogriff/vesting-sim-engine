"""Unit tests for deterministic valuation calculator."""

import unittest
from decimal import Decimal

from vesting_sim.domain.models import EquityGrant, ScheduleType
from vesting_sim.engine.calculator import calculate_realized_grant_value


class TestCalculator(unittest.TestCase):
    """Test suite for exact financial calculations."""

    def test_deterministic_payout(self) -> None:
        """Verifies realized payout calculation with fluctuating monthly prices."""
        grant = EquityGrant(
            grant_id="G-201",
            employee_id="E-601",
            total_shares=48,
            schedule_type=ScheduleType.EVEN_MONTHLY_4_YEAR,  # 1 share per month
        )

        # Mock price doubles at month 25 from $100 to $200
        prices = {}
        for m in range(1, 49):
            prices[m] = Decimal("100.00") if m <= 24 else Decimal("200.00")

        total_value = calculate_realized_grant_value(grant, prices)

        # 24 shares * $100 ($2400) + 24 shares * $200 ($4800) = $7200
        expected = Decimal("7200.00")
        self.assertEqual(total_value, expected)


if __name__ == "__main__":
    unittest.main()
