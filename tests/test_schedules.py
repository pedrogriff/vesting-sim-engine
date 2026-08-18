"""Unit tests for vesting schedules and deterministic share conservation."""

import unittest
from decimal import Decimal

from vesting_sim.domain.models import EquityGrant, GrantType, ScheduleType
from vesting_sim.domain.schedules import generate_vesting_schedule


class TestVestingSchedules(unittest.TestCase):
    """Test suite verifying mathematical invariants of vesting schedules."""

    def test_front_loaded_schedule_exact_conservation(self) -> None:
        """Verifies Google 33/33/22/12 schedule distributes exactly 100% of shares."""
        grant = EquityGrant(
            grant_id="G-101",
            employee_id="E-500",
            total_shares=1_000,
            schedule_type=ScheduleType.FRONT_LOADED_33_33_22_12,
        )

        tranches = generate_vesting_schedule(grant)
        self.assertEqual(len(tranches), 48)

        # Invariant: Sum of tranche shares MUST equal total_shares exactly
        total_vested = sum(t.shares for t in tranches)
        self.assertEqual(total_vested, 1_000)

        # Verify Year 1 (months 1-12) has ~330 shares
        y1_shares = sum(t.shares for t in tranches if t.month_offset <= 12)
        y2_shares = sum(t.shares for t in tranches if 13 <= t.month_offset <= 24)
        y3_shares = sum(t.shares for t in tranches if 25 <= t.month_offset <= 36)
        y4_shares = sum(t.shares for t in tranches if 37 <= t.month_offset <= 48)

        self.assertEqual(y1_shares, 330)
        self.assertEqual(y2_shares, 330)
        self.assertEqual(y3_shares, 220)
        self.assertEqual(y4_shares, 120)

    def test_standard_4_year_cliff(self) -> None:
        """Verifies 1-year cliff delivers 25% at month 12 and remainder monthly."""
        grant = EquityGrant(
            grant_id="G-102",
            employee_id="E-501",
            total_shares=100,
            schedule_type=ScheduleType.STANDARD_4_YEAR_CLIFF,
        )

        tranches = generate_vesting_schedule(grant)
        self.assertEqual(len(tranches), 37)  # Month 12 cliff + 36 monthly tranches

        # Cliff at month 12 must have 25 shares
        cliff_tranche = tranches[0]
        self.assertEqual(cliff_tranche.month_offset, 12)
        self.assertEqual(cliff_tranche.shares, 25)

        # Total shares invariant
        self.assertEqual(sum(t.shares for t in tranches), 100)

    def test_performance_multiplier_psu(self) -> None:
        """Verifies PSU grants scale total shares by performance multiplier."""
        grant = EquityGrant(
            grant_id="G-103",
            employee_id="E-502",
            total_shares=100,
            grant_type=GrantType.PSU,
            performance_multiplier=Decimal("1.50"),  # 150% outperformance
        )

        self.assertEqual(grant.effective_shares(), 150)
        tranches = generate_vesting_schedule(grant)
        self.assertEqual(sum(t.shares for t in tranches), 150)

    def test_odd_share_count_preserves_every_single_share(self) -> None:
        """Verifies that odd / indivisible share counts lose zero fractional shares."""
        # 17 shares across 48 months
        grant = EquityGrant(
            grant_id="G-104",
            employee_id="E-503",
            total_shares=17,
            schedule_type=ScheduleType.FRONT_LOADED_33_33_22_12,
        )

        tranches = generate_vesting_schedule(grant)
        self.assertEqual(sum(t.shares for t in tranches), 17)


if __name__ == "__main__":
    unittest.main()
