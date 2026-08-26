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


def test_empty_layer_stack_is_rejected() -> None:
    """An empty stack prices roofing at 0 and still prints a plausible total next
    to real krov and gutter figures — a whole cost category missing in silence."""
    with pytest.raises(ValueError, match="layers"):
        CostSpec(layers=(), krov_eur_per_m2=60.0, gutter_eur_per_m=30.0)
