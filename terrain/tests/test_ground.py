"""Hand-checked ground heights."""

import pytest

from terrain.core import ground
from terrain.core.survey import Point

# One triangle on which the height equals x.
POINTS = (Point(1, 0.0, 0.0, 0.0), Point(2, 10.0, 0.0, 10.0), Point(3, 0.0, 10.0, 0.0))
TRIANGLES = ((0, 1, 2),)


def test_height_is_linear_inside_a_triangle_and_none_outside() -> None:
    """(5, 0) → 5 on an edge, (2, 2) → 2 inside; (20, 20) is off the ground."""
    assert ground.height(POINTS, TRIANGLES, 5.0, 0.0) == pytest.approx(5.0)
    assert ground.height(POINTS, TRIANGLES, 2.0, 2.0) == pytest.approx(2.0)
    assert ground.height(POINTS, TRIANGLES, 20.0, 20.0) is None
