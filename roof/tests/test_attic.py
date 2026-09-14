"""Hand-checked references for usable attic area."""

import math

import pytest

from roof.core import attic
from roof.core.specs import AtticSpec, HouseSpec, RoofSpec

HOUSE = HouseSpec(width=9.0, length=10.0)
# Headroom is measured inside the walls, so overhangs don't matter here.
NO_OVERHANG = {"overhang_eave": 0.0, "overhang_gable": 0.0}
BARE = AtticSpec(
    h_min=1.9,
    roof_buildup=0.0,
    floor_buildup=0.0,
    knee_height=0.0,
    collar_above_wall_top=None,
)
BUILT = AtticSpec(
    h_min=1.9,
    roof_buildup=0.30,
    floor_buildup=0.20,
    knee_height=0.0,
    collar_above_wall_top=None,
)


def test_bare_structure_widths() -> None:
    """Build-ups zeroed: 9 m at 30° → 2.4182 m, at 40° → 4.4713 m."""
    assert attic.usable_width(
        HOUSE, RoofSpec(pitch_deg=30.0, **NO_OVERHANG), BARE
    ) == pytest.approx(2.4182, abs=1e-4)
    assert attic.usable_width(
        HOUSE, RoofSpec(pitch_deg=40.0, **NO_OVERHANG), BARE
    ) == pytest.approx(4.4713, abs=1e-4)


def test_roof_buildup_costs_more_headroom_the_steeper_the_pitch() -> None:
    """0.30 m perpendicular is 0.3464 m vertical at 30°, 0.4243 m at 45°."""
    assert attic.ceiling_drop(
        RoofSpec(pitch_deg=30.0, **NO_OVERHANG), BUILT
    ) == pytest.approx(0.30 / math.cos(math.radians(30.0)))
    assert attic.ceiling_drop(
        RoofSpec(pitch_deg=45.0, **NO_OVERHANG), BUILT
    ) == pytest.approx(0.4243, abs=1e-4)


def test_buildups_take_most_of_the_usable_strip() -> None:
    """9 m at 30°: 2.4182 m → 0.5254 m with 0.30 m roof and 0.20 m floor build-up.
    Each side loses (1.9 + 0.3464 + 0.2) / tan 30°."""
    assert attic.usable_width(
        HOUSE, RoofSpec(pitch_deg=30.0, **NO_OVERHANG), BUILT
    ) == pytest.approx(0.5254, abs=1e-4)


def test_a_shallow_pitch_leaves_no_standing_height_at_all() -> None:
    """9 m at 25°: the 2.0984 m ridge is 1.5674 m clear, under 1.9 m — no attic."""
    result = attic.estimate(HOUSE, RoofSpec(pitch_deg=25.0, **NO_OVERHANG), BUILT)
    assert result.clear_ridge_height == pytest.approx(1.5674, abs=1e-4)
    assert result.usable_width == 0.0
    assert result.usable_area == 0.0


def test_a_collar_gates_the_attic_rather_than_narrowing_it() -> None:
    """At 45° the strip is 3.9515 m. A collar at 2.5 m leaves 2.3 m clear and
    changes nothing; at 2.0 m it leaves 1.8 m and blocks the attic. 2.1 m is the
    minimum."""
    at_45 = RoofSpec(pitch_deg=45.0, **NO_OVERHANG)
    clears = AtticSpec(
        h_min=1.9,
        roof_buildup=0.30,
        floor_buildup=0.20,
        knee_height=0.0,
        collar_above_wall_top=2.5,
    )
    too_low = AtticSpec(
        h_min=1.9,
        roof_buildup=0.30,
        floor_buildup=0.20,
        knee_height=0.0,
        collar_above_wall_top=2.0,
    )

    assert attic.usable_width(HOUSE, at_45, BUILT) == pytest.approx(3.9515, abs=1e-4)
    assert attic.usable_width(HOUSE, at_45, clears) == pytest.approx(3.9515, abs=1e-4)
    assert attic.usable_width(HOUSE, at_45, too_low) == 0.0
    assert attic.min_collar_height(BUILT) == pytest.approx(2.1)

    # It caps the clear ridge too: 3.8757 m under the ceiling, 2.3 m under it.
    assert attic.clear_ridge_height(HOUSE, at_45, BUILT) == pytest.approx(
        3.8757, abs=1e-4
    )
    assert attic.clear_ridge_height(HOUSE, at_45, clears) == pytest.approx(2.3)


def test_knee_wall_buys_width() -> None:
    """A 0.5 m nadmurovka at 30° widens the strip 0.5254 m → 2.2574 m."""
    kneed = AtticSpec(
        h_min=1.9,
        roof_buildup=0.30,
        floor_buildup=0.20,
        knee_height=0.5,
        collar_above_wall_top=None,
    )
    result = attic.estimate(HOUSE, RoofSpec(pitch_deg=30.0, **NO_OVERHANG), kneed)
    assert result.usable_width == pytest.approx(2.2574, abs=1e-4)
