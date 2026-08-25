"""Hand-checked references for the usable-attic calculation (docs/spec.md §3b)."""

import pytest

from house.core import attic
from house.core.specs import AtticSpec, HouseSpec, RoofSpec

HOUSE = HouseSpec(width=9.0, length=10.0)


def test_worked_examples_from_spec() -> None:
    """The two cases in docs/spec.md §3b, at h_min = 1.9 m and no knee wall.

    9 m wide at 30°: each side loses 1.9 / tan(30°) = 3.2909 m -> 2.4182 m left.
    At 40° each side loses 2.2643 m -> 4.4713 m left. The pitch more than
    doubles the usable strip for 10° more roof angle.
    """
    spec = AtticSpec(h_min=1.9)
    assert attic.usable_width(HOUSE, RoofSpec(pitch_deg=30.0), spec) == pytest.approx(
        2.4182, abs=1e-4
    )
    assert attic.usable_width(HOUSE, RoofSpec(pitch_deg=40.0), spec) == pytest.approx(
        4.4713, abs=1e-4
    )


def test_ridge_below_h_min_gives_no_usable_area() -> None:
    """9 m at 20° puts the ridge at 1.638 m — under 1.9 m, so nothing qualifies."""
    result = attic.estimate(HOUSE, RoofSpec(pitch_deg=20.0), AtticSpec(h_min=1.9))
    assert result.usable_width == 0.0
    assert result.usable_area == 0.0


def test_knee_wall_buys_width() -> None:
    """A 0.5 m nadmurovka at 30° lifts the usable strip 2.4182 m -> 4.1503 m.

    Pins the knee-wall parameter that docs/decisions.md forbids deleting.
    """
    result = attic.estimate(
        HOUSE, RoofSpec(pitch_deg=30.0), AtticSpec(h_min=1.9, knee_height=0.5)
    )
    assert result.usable_width == pytest.approx(4.1503, abs=1e-4)
    assert result.usable_area == pytest.approx(41.503, abs=1e-3)
