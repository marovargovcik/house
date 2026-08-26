"""Hand-checked coordinates for the drawing geometry (`docs/spec.md` §3).

These are numeric outputs like any other, so they are pinned the same way. The
picture is only trustworthy if its points are.
"""

import math

import pytest

from house.core import views
from house.core.specs import AtticSpec, HouseSpec, RoofSpec
from house.core.views import Point


def test_45_degrees_puts_the_apex_at_half_the_width() -> None:
    """9 m wide at 45° → rise 4.5 m, and with no overhang the eave is the wall top."""
    section = views.section(
        HouseSpec(width=9.0, length=10.0),
        RoofSpec(pitch_deg=45.0, overhang_eave=0.0, overhang_gable=0.0),
        AtticSpec(h_min=1.9),
    )
    assert section.apex == pytest.approx(Point(0.0, 4.5))
    assert section.eave_outer[0] == pytest.approx(Point(-4.5, 0.0))
    assert section.eave_outer[1] == pytest.approx(Point(4.5, 0.0))
    assert section.knee_top[1] == pytest.approx(Point(4.5, 0.0))


def test_eave_overhang_descends_below_the_wall_top() -> None:
    """The overhang continues the slope outward, so it drops 0.6·tan30° ≈ 0.346 m.

    Drawing it level with the wall top is the plausible-looking mistake this
    pins against.
    """
    section = views.section(
        HouseSpec(width=9.0, length=10.0),
        RoofSpec(pitch_deg=30.0, overhang_eave=0.6, overhang_gable=0.4),
        AtticSpec(h_min=1.9),
    )
    left, right = section.eave_outer
    assert left == pytest.approx(Point(-5.1, -0.6 * math.tan(math.radians(30.0))))
    assert right.y == pytest.approx(-0.34641, abs=1e-5)


def test_headroom_line_spans_the_usable_width() -> None:
    """9 m at 30°, h_min 1.9 → each side loses 1.9/tan30° ≈ 3.29 m (spec §3b)."""
    section = views.section(
        HouseSpec(width=9.0, length=10.0),
        RoofSpec(pitch_deg=30.0),
        AtticSpec(h_min=1.9),
    )
    assert section.headroom_line is not None
    left, right = section.headroom_line
    assert left.y == 1.9
    assert right.x - left.x == pytest.approx(2.418207, abs=1e-6)


def test_knee_wall_lifts_the_apex_and_the_springing_point() -> None:
    """A 0.5 m nadmurovka raises the ridge one-for-one and widens the strip."""
    house, roof = HouseSpec(width=9.0, length=10.0), RoofSpec(pitch_deg=30.0)
    plain = views.section(house, roof, AtticSpec(h_min=1.9))
    kneed = views.section(house, roof, AtticSpec(h_min=1.9, knee_height=0.5))

    assert kneed.apex.y - plain.apex.y == pytest.approx(0.5)
    assert kneed.knee_top[1] == pytest.approx(Point(4.5, 0.5))
    assert kneed.wall_top[1] == pytest.approx(Point(4.5, 0.0))
    assert plain.headroom_line is not None
    assert kneed.headroom_line is not None
    assert kneed.headroom_line[1].x > plain.headroom_line[1].x


def test_ridge_below_h_min_leaves_nothing_to_draw() -> None:
    """9 m at 15° → ridge 1.21 m, under h_min: no strip in section or plan."""
    house = HouseSpec(width=9.0, length=10.0)
    roof = RoofSpec(pitch_deg=15.0)
    attic = AtticSpec(h_min=1.9)
    assert views.section(house, roof, attic).headroom_line is None
    assert views.plan(house, roof, attic).usable_strip is None


def test_plan_ridge_runs_out_over_the_rake_overhang() -> None:
    """Roof outline is length+2·o_gable by width+2·o_eave, and the ridge spans it."""
    plan = views.plan(
        HouseSpec(width=9.0, length=10.0),
        RoofSpec(pitch_deg=30.0, overhang_eave=0.6, overhang_gable=0.4),
        AtticSpec(h_min=1.9),
    )
    assert (plan.roof_outline.x_min, plan.roof_outline.x_max) == (-5.4, 5.4)
    assert (plan.roof_outline.y_min, plan.roof_outline.y_max) == (-5.1, 5.1)
    assert (plan.walls.x_min, plan.walls.y_min) == (-5.0, -4.5)
    assert plan.ridge == (Point(-5.4, 0.0), Point(5.4, 0.0))
    assert plan.usable_strip is not None
    strip = plan.usable_strip
    assert strip.y_max - strip.y_min == pytest.approx(2.418207, abs=1e-6)
    assert (strip.x_min, strip.x_max) == (-5.0, 5.0)
