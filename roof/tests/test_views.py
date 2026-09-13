"""Hand-checked coordinates for the drawing geometry (`docs/spec.md` §3).

These are numeric outputs like any other, so they are pinned the same way. The
picture is only trustworthy if its points are — and since the drawing is what
shows *why* the usable strip is as narrow as it is, the finished floor and
ceiling matter here as much as the structure does.
"""

import math

import pytest

from roof.core import views
from roof.core.specs import AtticSpec, HouseSpec, RoofSpec
from roof.core.views import Point

HOUSE = HouseSpec(width=9.0, length=10.0)
BARE = AtticSpec(
    h_min=1.9,
    roof_buildup=0.0,
    floor_buildup=0.0,
    knee_height=0.0,
    collar_above_wall_top=None,
)
BUILT = AtticSpec(
    h_min=1.9,
    roof_buildup=0.30,
    floor_buildup=0.20,
    knee_height=0.0,
    collar_above_wall_top=None,
)
OVERHANGS = {"overhang_eave": 0.6, "overhang_gable": 0.4}
NO_OVERHANG = {"overhang_eave": 0.0, "overhang_gable": 0.0}


def test_45_degrees_puts_the_apex_at_half_the_width() -> None:
    """9 m wide at 45° → rise 4.5 m, and with no overhang the eave is the wall top."""
    section = views.section(HOUSE, RoofSpec(pitch_deg=45.0, **NO_OVERHANG), BARE)
    assert section.apex == pytest.approx(Point(0.0, 4.5))
    assert section.eave_outer[0] == pytest.approx(Point(-4.5, 0.0))
    assert section.eave_outer[1] == pytest.approx(Point(4.5, 0.0))
    assert section.knee_top[1] == pytest.approx(Point(4.5, 0.0))


def test_eave_overhang_descends_below_the_wall_top() -> None:
    """The overhang continues the slope outward, so it drops 0.6·tan30° ≈ 0.346 m.

    Drawing it level with the wall top is the plausible-looking mistake this
    pins against.
    """
    section = views.section(HOUSE, RoofSpec(pitch_deg=30.0, **OVERHANGS), BARE)
    left, right = section.eave_outer
    assert left == pytest.approx(Point(-5.1, -0.6 * math.tan(math.radians(30.0))))
    assert right.y == pytest.approx(-0.34641, abs=1e-5)


def test_finished_surfaces_sit_inside_the_structure() -> None:
    """At 30° the ceiling hangs 0.3464 m below the roof plane and the floor sits
    0.20 m above the wall top, so the drawing can show what eats the headroom.

    The ceiling is a *parallel* plane: its apex drops by the same vertical amount
    its eaves do, which is what makes the band between the two lines uniform.
    """
    section = views.section(HOUSE, RoofSpec(pitch_deg=30.0, **OVERHANGS), BUILT)
    drop = 0.30 / math.cos(math.radians(30.0))

    assert section.floor[1] == pytest.approx(Point(4.5, 0.20))
    assert section.ceiling[0] == pytest.approx(Point(-4.5, -drop))
    assert section.ceiling[2] == pytest.approx(Point(4.5, -drop))
    assert section.ceiling[1] == pytest.approx(Point(0.0, section.apex.y - drop))


def test_standing_room_stands_on_the_floor_and_stops_at_the_ceiling() -> None:
    """9 m at 30°: a 0.5254 m base on the finished floor at 0.20 m, corners at
    2.10 m (= floor + h_min) sitting exactly on the ceiling plane, apex at
    2.2517 m.

    The base is `usable_width` and the corners are on the ceiling — that pairing
    is the whole claim the drawing makes.
    """
    section = views.section(HOUSE, RoofSpec(pitch_deg=30.0, **OVERHANGS), BUILT)
    assert section.standing_room is not None
    base_left, base_right, right, apex, left = section.standing_room

    assert base_right.x - base_left.x == pytest.approx(0.5254, abs=1e-4)
    assert base_left.y == pytest.approx(0.20)
    assert right == pytest.approx(Point(0.2627, 2.1), abs=1e-4)
    assert left == pytest.approx(Point(-0.2627, 2.1), abs=1e-4)
    assert apex == pytest.approx(section.ceiling[1])
    assert section.headroom_line is not None
    assert section.headroom_line[0].y == pytest.approx(2.1)


def test_a_collar_caps_the_standing_room_flat() -> None:
    """A collar 2.5 m above the wall top cuts the peak off: the region runs up the
    ceiling to 2.5 m, then straight across between the collar's ends at ±1.5757 m.

    Leaving the apex in would draw standing room where a beam is.
    """
    kneed = AtticSpec(
        h_min=1.9,
        roof_buildup=0.30,
        floor_buildup=0.20,
        knee_height=0.0,
        collar_above_wall_top=2.5,
    )
    section = views.section(HOUSE, RoofSpec(pitch_deg=45.0, **OVERHANGS), kneed)

    assert section.collar is not None
    assert section.collar[1] == pytest.approx(Point(1.5757, 2.5), abs=1e-4)
    assert section.standing_room is not None
    assert len(section.standing_room) == 6
    assert section.standing_room[3] == pytest.approx(Point(1.5757, 2.5), abs=1e-4)
    assert section.standing_room[4] == pytest.approx(Point(-1.5757, 2.5), abs=1e-4)


def test_knee_wall_lifts_the_apex_and_the_springing_point() -> None:
    """A 0.5 m nadmurovka raises the ridge one-for-one and widens the strip."""
    roof = RoofSpec(pitch_deg=30.0, **OVERHANGS)
    kneed = AtticSpec(
        h_min=1.9,
        roof_buildup=0.30,
        floor_buildup=0.20,
        knee_height=0.5,
        collar_above_wall_top=None,
    )
    plain = views.section(HOUSE, roof, BUILT)
    lifted = views.section(HOUSE, roof, kneed)

    assert lifted.apex.y - plain.apex.y == pytest.approx(0.5)
    assert lifted.knee_top[1] == pytest.approx(Point(4.5, 0.5))
    assert lifted.wall_top[1] == pytest.approx(Point(4.5, 0.0))
    assert plain.headroom_line is not None
    assert lifted.headroom_line is not None
    assert lifted.headroom_line[1].x > plain.headroom_line[1].x


def test_a_ceiling_below_h_min_leaves_nothing_to_draw() -> None:
    """9 m at 25° clears only 1.5674 m at the ridge, so section and plan both
    come back empty — the case the bare-structure model drew a strip for."""
    roof = RoofSpec(pitch_deg=25.0, **OVERHANGS)
    section = views.section(HOUSE, roof, BUILT)
    assert section.headroom_line is None
    assert section.standing_room is None
    assert views.plan(HOUSE, roof, BUILT).usable_strip is None


def test_plan_ridge_runs_out_over_the_rake_overhang() -> None:
    """Roof outline is length+2·o_gable by width+2·o_eave, and the ridge spans it."""
    plan = views.plan(HOUSE, RoofSpec(pitch_deg=30.0, **OVERHANGS), BARE)
    assert (plan.roof_outline.x_min, plan.roof_outline.x_max) == (-5.4, 5.4)
    assert (plan.roof_outline.y_min, plan.roof_outline.y_max) == (-5.1, 5.1)
    assert (plan.walls.x_min, plan.walls.y_min) == (-5.0, -4.5)
    assert plan.ridge == (Point(-5.4, 0.0), Point(5.4, 0.0))
    assert plan.usable_strip is not None
    strip = plan.usable_strip
    assert strip.y_max - strip.y_min == pytest.approx(2.418207, abs=1e-6)
    assert (strip.x_min, strip.x_max) == (-5.0, 5.0)
