"""Hand-checked view coordinates."""

import pytest

from terrain.core import views
from terrain.core.survey import Point

A = Point(number=1, x=0.0, y=0.0, z=270.0)
B = Point(number=2, x=10.0, y=5.0, z=272.0)
NUMBERED = {1: A, 2: B}


def test_raised_lifts_each_point_by_the_same_height() -> None:
    lifted = views.raised(NUMBERED, (1, 2), 1.2)
    assert [(x, y) for x, y, _ in lifted] == [(0.0, 0.0), (10.0, 5.0)]
    assert [z for _, _, z in lifted] == pytest.approx([271.2, 273.2])


def test_posts_run_from_the_ground_up() -> None:
    assert views.posts(NUMBERED, (2,), 5.0) == (
        ((10.0, 5.0, 272.0), (10.0, 5.0, 277.0)),
    )


def test_extent_leaves_room_for_the_compass_and_aspect_keeps_true_scale() -> None:
    """10 m by 5 m plus 5 m all round is 20 by 15; from 270 up to a 274 roof top,
    doubled: 1 : 0.75 : 0.4."""
    box = views.extent((A, B), highest=274.0)
    assert [*box.x, *box.y, *box.z] == pytest.approx(
        [-5.0, 15.0, -5.0, 10.0, 270.0, 274.0]
    )
    assert views.aspect(box, exaggeration=2.0) == pytest.approx((1.0, 0.75, 0.4))


def test_midpoint_sits_halfway_above_the_ground() -> None:
    assert views.midpoint(A, B, 2.0) == pytest.approx((5.0, 2.5, 273.0))


def test_compass_sits_beyond_each_edge_above_the_ground() -> None:
    """5 m beyond a 10 m by 5 m survey whose highest point is 272: labels at 273,
    the arrow 4 m long."""
    c = views.compass((A, B))
    assert [*c.north, *c.south] == pytest.approx([5.0, 10.0, 273.0, 5.0, -5.0, 273.0])
    assert [*c.east, *c.west] == pytest.approx([15.0, 2.5, 273.0, -5.0, 2.5, 273.0])
    assert c.arrow_tail == pytest.approx((5.0, 6.0, 273.0))
