"""The sweep wires pinned functions together; check the wiring."""

import math

import pytest

from roof.core import sweep
from roof.core.specs import AtticSpec, CostSpec

COSTS = CostSpec(eur_per_m2=110.0)


def test_row_matches_the_hand_checked_case_and_flags_unusable_pitches() -> None:
    """9 m / 30° matches the unit tests; 20° has no usable area and NaN per m².
    `clear_ridge_m` catches the two ridge figures being swapped."""
    rows = sweep.width_by_pitch(
        widths=[9.0],
        pitches_deg=[20.0, 30.0],
        length=10.0,
        attic=AtticSpec(
            h_min=1.9,
            roof_buildup=0.30,
            floor_buildup=0.20,
            knee_height=0.0,
            collar_above_wall_top=None,
        ),
        costs=COSTS,
        overhang_eave=0.6,
        overhang_gable=0.4,
    )

    assert len(rows) == 2
    shallow, row = rows
    assert row.roof_area_m2 == pytest.approx(127.2018, abs=1e-4)
    assert row.clear_ridge_m == pytest.approx(2.0517, abs=1e-4)
    assert row.usable_area_m2 == pytest.approx(5.2539, abs=1e-4)
    assert row.total_eur == pytest.approx(13992.1992, abs=1e-4)
    assert row.eur_per_usable_m2 == pytest.approx(2663.2196, abs=1e-4)
    assert row.usable_fraction == pytest.approx(0.0584, abs=1e-4)

    assert shallow.pitch_deg == 20.0
    assert shallow.usable_area_m2 == 0.0
    assert math.isnan(shallow.eur_per_usable_m2)


def test_knee_wall_raises_the_reported_ridge_by_its_own_height() -> None:
    """A knee wall raises the reported ridge by its own height."""

    def row(knee: float) -> sweep.SweepRow:
        rows = sweep.width_by_pitch(
            widths=[9.0],
            pitches_deg=[30.0],
            length=10.0,
            attic=AtticSpec(
                h_min=1.9,
                roof_buildup=0.30,
                floor_buildup=0.20,
                knee_height=knee,
                collar_above_wall_top=None,
            ),
            costs=COSTS,
            overhang_eave=0.6,
            overhang_gable=0.4,
        )
        return rows[0]

    assert row(0.0).ridge_above_wall_top_m == pytest.approx(2.5981, abs=1e-4)
    assert row(0.5).ridge_above_wall_top_m == pytest.approx(3.0981, abs=1e-4)
    assert row(0.5).usable_width_m == pytest.approx(2.2574, abs=1e-4)
