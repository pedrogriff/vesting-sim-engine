"""Property-based verification of mathematical and financial invariants using Hypothesis."""

import unittest
from decimal import Decimal

from hypothesis import given, settings
from hypothesis import strategies as st

from vesting_sim.domain.models import EquityGrant, GrantType, ScheduleType
from vesting_sim.domain.schedules import generate_vesting_schedule


class TestPropertyBasedInvariants(unittest.TestCase):
    """Property tests mathematically verifying conservation of equity shares."""

    @settings(max_examples=200)
    @given(
        total_shares=st.integers(min_value=1, max_value=10_000_000),
        schedule_type=st.sampled_from(list(ScheduleType)),
        multiplier=st.sampled_from([Decimal("0.5"), Decimal("1.0"), Decimal("1.75"), Decimal("2.0")]),
    )
    def test_invariant_share_conservation(
        self,
        total_shares: int,
        schedule_type: ScheduleType,
        multiplier: Decimal,
    ) -> None:
        """Mathematical Invariant: Sum of all tranche shares must ALWAYS equal effective shares.

        Zero shares can be lost or created due to integer rounding across any grant size.
        """
        grant = EquityGrant(
            grant_id="P-TEST",
            employee_id="EMP-TEST",
            total_shares=total_shares,
            grant_type=GrantType.PSU,
            schedule_type=schedule_type,
            performance_multiplier=multiplier,
        )

        tranches = generate_vesting_schedule(grant)
        expected_shares = grant.effective_shares()

        total_vested_shares = sum(t.shares for t in tranches)
        self.assertEqual(
            total_vested_shares,
            expected_shares,
            f"Invariant violated for {total_shares} shares on {schedule_type}",
        )


if __name__ == "__main__":
    unittest.main()
