"""The input types are the only validation boundary — pin what they reject."""

import pytest

from house.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec, collar_from_input


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


@pytest.mark.parametrize("collar", [0.5, 0.4])
def test_a_collar_at_or_below_the_knee_top_is_rejected(collar: float) -> None:
    """The rafters spring from the knee top, so a collar there ties nothing.

    Both fields are `AtticSpec`'s own, so the spec catches this itself — which is
    what keeps `views` free of a clamp for a shape that cannot occur. A collar
    higher than the *roof* needs the width and pitch too; that lives in
    `core/validate.py`.
    """
    with pytest.raises(ValueError, match="knee wall the rafters spring from"):
        AtticSpec(
            h_min=1.9,
            roof_buildup=0.3,
            floor_buildup=0.2,
            knee_height=0.5,
            collar_above_wall_top=collar,
        )


def test_collar_from_input_reads_zero_and_absence_as_the_same_thing() -> None:
    """The one place the "0 means no klieština" convention lives.

    Both entry points route through it, so a change here changes both. Any other
    number passes straight to `AtticSpec`, which is what still rejects a collar
    at or below the wall top — this function does not validate.
    """
    assert collar_from_input(0) is None
    assert collar_from_input(None) is None
    assert collar_from_input(2.4) == 2.4
    assert collar_from_input(-1) == -1
