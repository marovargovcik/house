"""Hand-checked references for the usable-attic calculation (docs/spec.md §3b).

Headroom is clear height, so most of these pin what stands between the bare
structure and it: the roof build-up above, the floor build-up below, and a
collar tie across.
"""

import math

import pytest

from house.core import attic
from house.core.specs import AtticSpec, HouseSpec, RoofSpec

HOUSE = HouseSpec(width=9.0, length=10.0)
# Overhangs do not enter any of this — headroom is measured inside the walls —
# so they are zeroed rather than given values that would look load-bearing.
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


def test_bare_structure_reproduces_the_spec_worked_examples() -> None:
    """With both build-ups zeroed, docs/spec.md §3b still holds: 9 m at 30° leaves
    2.4182 m and at 40° leaves 4.4713 m.

    The backward-consistency check — it confirms the build-up terms are additions
    to the old formula rather than a rewrite of it.
    """
    assert attic.usable_width(
        HOUSE, RoofSpec(pitch_deg=30.0, **NO_OVERHANG), BARE
    ) == pytest.approx(2.4182, abs=1e-4)
    assert attic.usable_width(
        HOUSE, RoofSpec(pitch_deg=40.0, **NO_OVERHANG), BARE
    ) == pytest.approx(4.4713, abs=1e-4)


def test_roof_buildup_costs_more_headroom_the_steeper_the_pitch() -> None:
    """0.30 m perpendicular to the plane is 0.3464 m vertically at 30°, 0.4243 m
    at 45° — the 1 / cos θ that makes a steep roof pay twice.

    Reading the build-up as a vertical figure would under-state every steep
    pitch, the direction that flatters the answer.
    """
    assert attic.ceiling_drop(
        RoofSpec(pitch_deg=30.0, **NO_OVERHANG), BUILT
    ) == pytest.approx(0.30 / math.cos(math.radians(30.0)))
    assert attic.ceiling_drop(
        RoofSpec(pitch_deg=45.0, **NO_OVERHANG), BUILT
    ) == pytest.approx(0.4243, abs=1e-4)


def test_buildups_take_most_of_the_usable_strip() -> None:
    """9 m at 30° drops 2.4182 m -> 0.5254 m once 0.30 m of roof and 0.20 m of
    floor are counted. Each side now loses (1.9 + 0.3464 + 0.2) / tan 30°.

    The size of this gap is the reason the build-ups are required inputs rather
    than defaulted to zero.
    """
    assert attic.usable_width(
        HOUSE, RoofSpec(pitch_deg=30.0, **NO_OVERHANG), BUILT
    ) == pytest.approx(0.5254, abs=1e-4)


def test_a_shallow_pitch_leaves_no_standing_height_at_all() -> None:
    """9 m at 25°: a 2.0984 m structural ridge is only 1.5674 m clear, so not even
    the ridge clears 1.9 m and the whole attic is out — where the bare-structure
    model still reported 0.85 m of usable width.
    """
    result = attic.estimate(HOUSE, RoofSpec(pitch_deg=25.0, **NO_OVERHANG), BUILT)
    assert result.clear_ridge_height == pytest.approx(1.5674, abs=1e-4)
    assert result.usable_width == 0.0
    assert result.usable_area == 0.0


def test_a_collar_gates_the_attic_rather_than_narrowing_it() -> None:
    """A collar caps headroom everywhere at once, so it either rules the attic out
    or costs nothing.

    At 45° the strip is 3.9515 m. A collar 2.5 m above the wall top leaves 2.3 m
    clear and changes nothing; at 2.0 m it leaves 1.8 m and there is no habitable
    attic at any pitch — 2.1 m is the lowest that works.
    """
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


def test_knee_wall_buys_width() -> None:
    """A 0.5 m nadmurovka at 30° lifts the strip 0.5254 m -> 2.2574 m.

    Pins the knee-wall parameter that docs/decisions.md forbids deleting: it
    offsets the build-ups one-for-one, being the one term that pushes the other
    way.
    """
    kneed = AtticSpec(
        h_min=1.9,
        roof_buildup=0.30,
        floor_buildup=0.20,
        knee_height=0.5,
        collar_above_wall_top=None,
    )
    result = attic.estimate(HOUSE, RoofSpec(pitch_deg=30.0, **NO_OVERHANG), kneed)
    assert result.usable_width == pytest.approx(2.2574, abs=1e-4)
