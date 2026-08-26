"""The input types are the only validation boundary — pin what they reject."""

import pytest

from house.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec


@pytest.mark.parametrize("pitch_deg", [0.0, 90.0, -5.0])
def test_pitch_outside_the_open_interval_is_rejected(pitch_deg: float) -> None:
    """0 < pitch < 90 is what makes tan and 1 / cos total for every calculation
    downstream, so the guard has to be here rather than in each function."""
    with pytest.raises(ValueError, match="pitch"):
        RoofSpec(pitch_deg=pitch_deg)


def test_h_min_has_no_default() -> None:
    """docs/decisions.md forbids a default until the Slovak norm is confirmed.

    mypy would catch a call site omitting it, but not someone *adding* a
    default — that regression would silently put an unverified number into
    every result, so it is pinned here.
    """
    with pytest.raises(TypeError):
        AtticSpec()  # type: ignore[call-arg]


@pytest.mark.parametrize("bad", [float("nan"), float("inf")])
def test_non_finite_dimensions_are_rejected(bad: float) -> None:
    """NaN compares False against everything, so a bare `<= 0` guard waves it
    through and it then turns every downstream number into NaN with nothing
    pointing at where it entered."""
    with pytest.raises(ValueError, match="footprint"):
        HouseSpec(width=bad, length=10.0)
    with pytest.raises(ValueError, match="h_min"):
        AtticSpec(h_min=bad)


@pytest.mark.parametrize("bad", [0.0, -1.0, float("nan")])
def test_non_positive_roof_rate_is_rejected(bad: float) -> None:
    """A zero rate prices the whole roof at nothing and still prints a plausible
    total — a cost category missing in silence. That is why the all-in rate has
    to be positive rather than merely non-negative."""
    with pytest.raises(ValueError, match="roof rate"):
        CostSpec(eur_per_m2=bad)
