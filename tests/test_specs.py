"""The input types are the only validation boundary — pin what they reject."""

import pytest

from house.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec


@pytest.mark.parametrize("pitch_deg", [0.0, 90.0, -5.0])
def test_pitch_outside_the_open_interval_is_rejected(pitch_deg: float) -> None:
    """0 < pitch < 90 is what makes tan and 1 / cos total for every calculation
    downstream, so the guard has to be here rather than in each function."""
    with pytest.raises(ValueError, match="pitch"):
        RoofSpec(pitch_deg=pitch_deg, overhang_eave=0.6, overhang_gable=0.4)


def test_no_attic_input_has_a_default() -> None:
    """Every field must be stated at every call site — knee wall and collar tie
    included, even to say there is none.

    docs/decisions.md forbids a default `h_min` until the Slovak norm is
    confirmed, and the build-ups carry the same rule for the same reason: a
    zero default silently restores the bare-structure headroom that over-stated
    the usable strip by roughly half. mypy would catch a call site omitting
    them, but not someone *adding* a default, so it is pinned here.
    """
    with pytest.raises(TypeError):
        AtticSpec()  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        AtticSpec(h_min=1.9)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        AtticSpec(  # type: ignore[call-arg]
            h_min=1.9, roof_buildup=0.3, floor_buildup=0.2
        )


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_dimensions_are_rejected(bad: float) -> None:
    """NaN compares False against everything, so a bare `<= 0` guard waves it
    through and it then turns every downstream number into NaN with nothing
    pointing at where it entered."""
    with pytest.raises(ValueError, match="footprint"):
        HouseSpec(width=bad, length=10.0)
    with pytest.raises(ValueError, match="h_min"):
        AtticSpec(
            h_min=bad,
            roof_buildup=0.3,
            floor_buildup=0.2,
            knee_height=0.0,
            collar_above_wall_top=None,
        )


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan")])
def test_non_positive_roof_rate_is_rejected(bad: float) -> None:
    """A zero rate prices the whole roof at nothing and still prints a plausible
    total — a cost category missing in silence. That is why the all-in rate has
    to be positive rather than merely non-negative."""
    with pytest.raises(ValueError, match="roof rate"):
        CostSpec(eur_per_m2=bad)
