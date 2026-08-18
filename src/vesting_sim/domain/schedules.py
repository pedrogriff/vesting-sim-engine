"""Deterministic Equity Vesting Schedule Generators with Exact Share Conservation."""

from __future__ import annotations

from decimal import Decimal

from vesting_sim.domain.models import EquityGrant, ScheduleType, VestingTranche


def _distribute_integer_shares(total_shares: int, weights: list[Decimal]) -> list[int]:
    """Distributes total_shares across weights using the Largest Remainder Method."""
    if total_shares <= 0 or not weights:
        return [0] * len(weights)

    num_tranches = len(weights)
    allocated: list[int] = []
    remainders: list[tuple[Decimal, int]] = []
    total_allocated = 0

    for idx, weight in enumerate(weights):
        ideal_decimal = Decimal(total_shares) * weight
        floor_val = int(ideal_decimal)
        rem = ideal_decimal - Decimal(floor_val)

        allocated.append(floor_val)
        remainders.append((rem, idx))
        total_allocated += floor_val

    unallocated = total_shares - total_allocated
    remainders.sort(key=lambda x: (-x[0], x[1]))

    for i in range(unallocated):
        idx = remainders[i % num_tranches][1]
        allocated[idx] += 1

    return allocated


def generate_vesting_schedule(grant: EquityGrant) -> list[VestingTranche]:
    """Generates deterministic vesting tranches using hierarchical Largest Remainder Method.

    Guarantees the Mathematical Invariant: sum(tranche.shares) == grant.effective_shares()
    """
    total_shares = grant.effective_shares()
    if total_shares <= 0:
        return []

    tranches: list[VestingTranche] = []

    if grant.schedule_type == ScheduleType.FRONT_LOADED_33_33_22_12:
        # Hierarchical distribution: 1. Split across 4 years (33%, 33%, 22%, 12%)
        year_weights = [Decimal("0.33"), Decimal("0.33"), Decimal("0.22"), Decimal("0.12")]
        year_shares = _distribute_integer_shares(total_shares, year_weights)

        # 2. Split each year's shares across its 12 months
        period_idx = 0
        monthly_equal_weight = Decimal("1.0") / Decimal("12")
        month_weights_12 = [monthly_equal_weight] * 12

        for y_idx, y_total in enumerate(year_shares):
            m_shares = _distribute_integer_shares(y_total, month_weights_12)
            y_base_month = y_idx * 12

            for m_idx, shares in enumerate(m_shares):
                month_offset = y_base_month + m_idx + 1
                tranches.append(
                    VestingTranche(
                        period_index=period_idx,
                        month_offset=month_offset,
                        shares=shares,
                        target_weight=year_weights[y_idx] / Decimal("12"),
                    )
                )
                period_idx += 1

    elif grant.schedule_type == ScheduleType.STANDARD_4_YEAR_CLIFF:
        # 1-year cliff: 25% at month 12, then remaining 75% across 36 monthly tranches
        cliff_shares = int(Decimal(total_shares) * Decimal("0.25"))
        remaining_shares = total_shares - cliff_shares

        # Month 12 cliff
        tranches.append(
            VestingTranche(
                period_index=0,
                month_offset=12,
                shares=cliff_shares,
                target_weight=Decimal("0.25"),
            )
        )

        # 36 monthly post-cliff tranches
        month_weights_36 = [Decimal("1.0") / Decimal("36")] * 36
        post_cliff_shares = _distribute_integer_shares(remaining_shares, month_weights_36)

        for idx, shares in enumerate(post_cliff_shares):
            tranches.append(
                VestingTranche(
                    period_index=idx + 1,
                    month_offset=13 + idx,
                    shares=shares,
                    target_weight=Decimal("0.75") / Decimal("36"),
                )
            )

    elif grant.schedule_type == ScheduleType.EVEN_MONTHLY_4_YEAR:
        month_weights_48 = [Decimal("1.0") / Decimal("48")] * 48
        allocated = _distribute_integer_shares(total_shares, month_weights_48)
        for idx, shares in enumerate(allocated):
            tranches.append(
                VestingTranche(
                    period_index=idx,
                    month_offset=idx + 1,
                    shares=shares,
                    target_weight=Decimal("1.0") / Decimal("48"),
                )
            )

    elif grant.schedule_type == ScheduleType.EVEN_QUARTERLY_4_YEAR:
        quarter_weights_16 = [Decimal("1.0") / Decimal("16")] * 16
        allocated = _distribute_integer_shares(total_shares, quarter_weights_16)
        for idx, shares in enumerate(allocated):
            tranches.append(
                VestingTranche(
                    period_index=idx,
                    month_offset=(idx + 1) * 3,
                    shares=shares,
                    target_weight=Decimal("1.0") / Decimal("16"),
                )
            )

    return tranches
