"""Hand-checked slope sections."""

import pytest

from terrain.core import profile
from terrain.core.survey import Point

# A 10 m square on which the height equals x.
SQUARE = (
    Point(1, 0.0, 0.0, 0.0),
    Point(2, 10.0, 0.0, 10.0),
    Point(3, 10.0, 10.0, 10.0),
    Point(4, 0.0, 10.0, 0.0),
)
TRIANGLES = ((0, 1, 2), (0, 2, 3))


def test_sections_split_the_line_and_rise_as_far_as_they_run() -> None:
    """0 to 10 m in steps of 4: 0-4, 4-8, 8-10, each at 45° on z = x."""
    line = profile.samples(
        SQUARE,
        TRIANGLES,
        (0.0, 5.0),
        (10.0, 5.0),
        step=4.0,
    )
    sections = profile.sections(line)
    assert [(s.start.distance, s.end.distance) for s in sections] == [
        (0.0, 4.0),
        (4.0, 8.0),
        (8.0, 10.0),
    ]
    assert [s.rise for s in sections] == pytest.approx([4.0, 4.0, 2.0])
    assert [s.slope_deg for s in sections] == pytest.approx([45.0, 45.0, 45.0])


def test_shifted_moves_the_line_to_its_right() -> None:
    """Facing east along y = 0, 2 m to the right is y = -2."""
    start, end = profile.shifted((0.0, 0.0), (10.0, 0.0), 2.0)
    assert start == pytest.approx((0.0, -2.0))
    assert end == pytest.approx((10.0, -2.0))


def test_float_noise_does_not_add_an_empty_last_section() -> None:
    """3 x 0.1 is 0.30000000000000004: three sections, not a fourth of zero length."""
    sections = profile.sections(
        profile.samples(SQUARE, TRIANGLES, (0.0, 5.0), (3 * 0.1, 5.0), step=0.1)
    )
    assert len(sections) == 3
    assert [s.slope_deg for s in sections] == pytest.approx([45.0] * 3)
