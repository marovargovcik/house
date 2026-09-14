"""What the input types reject."""

import pytest

from roof.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec, collar_from_input


@pytest.mark.parametrize("pitch_deg", [0.0, 90.0, -5.0])
def test_pitch_outside_the_open_interval_is_rejected(pitch_deg: float) -> None:
    """0 < pitch < 90 keeps tan and 1 / cos safe downstream."""
    with pytest.raises(ValueError, match="pitch"):
        RoofSpec(pitch_deg=pitch_deg, overhang_eave=0.6, overhang_gable=0.4)


def test_no_attic_input_has_a_default() -> None:
    """No attic field has a default. mypy catches a missing argument, not an added
    default."""
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
    """NaN slips past a bare `<= 0` check and poisons every number after it."""
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
    """A zero rate would still print a plausible-looking total."""
    with pytest.raises(ValueError, match="roof rate"):
        CostSpec(eur_per_m2=bad)


@pytest.mark.parametrize("collar", [0.5, 0.4])
def test_a_collar_at_or_below_the_knee_top_is_rejected(collar: float) -> None:
    """The rafters spring from the knee top, so a collar there ties nothing."""
    with pytest.raises(ValueError, match="knee wall the rafters spring from"):
        AtticSpec(
            h_min=1.9,
            roof_buildup=0.3,
            floor_buildup=0.2,
            knee_height=0.5,
            collar_above_wall_top=collar,
        )


def test_collar_from_input_reads_zero_and_absence_as_the_same_thing() -> None:
    """0 and `None` mean no collar; anything else passes through unvalidated."""
    assert collar_from_input(0) is None
    assert collar_from_input(None) is None
    assert collar_from_input(2.4) == 2.4
    assert collar_from_input(-1) == -1
