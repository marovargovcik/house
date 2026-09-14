"""Hand-checked plot sides and area."""

import pytest

from terrain.core import boundary
from terrain.core.survey import Point

# A 10 x 5 m rectangle on a slope.
NUMBERED = {
    1: Point(1, 0.0, 0.0, 270.0),
    2: Point(2, 10.0, 0.0, 275.0),
    3: Point(3, 10.0, 5.0, 275.0),
    4: Point(4, 0.0, 5.0, 270.0),
}


def test_sides_and_area_are_measured_flat() -> None:
    """Sides 10, 5, 10, 5 m and 50 m², whatever the heights."""
    sides = boundary.sides(NUMBERED, (1, 2, 3, 4))
    assert [(s.start, s.end) for s in sides] == [(1, 2), (2, 3), (3, 4), (4, 1)]
    assert [s.length for s in sides] == pytest.approx([10.0, 5.0, 10.0, 5.0])
    assert boundary.area(NUMBERED, (1, 2, 3, 4)) == pytest.approx(50.0)


def test_gap_takes_the_nearest_house_corner_or_side_end() -> None:
    """A 6 x 2 m house 3 m above a side along y = 0. A side ending under the middle
    of the house is 3 m from its bottom edge, though 4.24 m from any corner."""
    house = ((2.0, 3.0), (8.0, 3.0), (8.0, 5.0), (2.0, 5.0))
    assert boundary.gap((0.0, 0.0), (10.0, 0.0), house) == pytest.approx(3.0)
    assert boundary.gap((5.0, 0.0), (5.0, -10.0), house) == pytest.approx(3.0)


def test_contains_tells_inside_from_outside() -> None:
    ring = ((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0))
    assert boundary.contains(ring, (5.0, 5.0))
    assert not boundary.contains(ring, (15.0, 5.0))


def test_outline_gap_is_the_space_between_two_outlines() -> None:
    """Two 1 m squares side by side with 2 m between them."""
    left = ((0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0))
    right = ((3.0, 0.0), (4.0, 0.0), (4.0, 1.0), (3.0, 1.0))
    assert boundary.outline_gap(left, right) == pytest.approx(2.0)


def test_nearest_pairs_the_house_corner_with_the_side() -> None:
    house = ((2.0, 3.0), (8.0, 3.0), (8.0, 5.0), (2.0, 5.0))
    near, far = boundary.nearest((0.0, 0.0), (10.0, 0.0), house)
    assert near == pytest.approx((2.0, 3.0))
    assert far == pytest.approx((2.0, 0.0))


def test_shifted_toward_moves_the_side_towards_the_given_point() -> None:
    up_a, up_b = boundary.shifted_toward((0.0, 0.0), (10.0, 0.0), 2.5, (5.0, 5.0))
    down_a, down_b = boundary.shifted_toward((0.0, 0.0), (10.0, 0.0), 2.5, (5.0, -5.0))
    assert [*up_a, *up_b] == pytest.approx([0.0, 2.5, 10.0, 2.5])
    assert [*down_a, *down_b] == pytest.approx([0.0, -2.5, 10.0, -2.5])


def test_setback_draws_the_limit_line_and_the_way_across() -> None:
    """On flat ground, a house 3 m in from a side, with a 2.5 m limit."""
    flat = (
        Point(1, 0.0, 0.0, 270.0),
        Point(2, 10.0, 0.0, 270.0),
        Point(3, 10.0, 10.0, 270.0),
        Point(4, 0.0, 10.0, 270.0),
    )
    house = ((2.0, 3.0), (8.0, 3.0), (8.0, 5.0), (2.0, 5.0))
    setback = boundary.setback(
        flat, ((0, 1, 2), (0, 2, 3)), (0.0, 0.0), (10.0, 0.0), house, 2.5, step=1.0
    )
    first, last = setback.limit_line[0], setback.limit_line[-1]
    across_from, across_to = setback.measure[0], setback.measure[-1]
    assert setback.gap == pytest.approx(3.0)
    assert [first.x, first.y, last.x, last.y] == pytest.approx([0.0, 2.5, 10.0, 2.5])
    assert [across_from.x, across_from.y, across_to.x, across_to.y] == pytest.approx(
        [2.0, 0.0, 2.0, 3.0]
    )
