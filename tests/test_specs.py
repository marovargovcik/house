"""The input types are the only validation boundary — pin what they reject."""

import pytest

from house.core.specs import AtticSpec, RoofSpec


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
