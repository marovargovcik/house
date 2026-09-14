"""Hand-checked house placement and heights."""

import pytest

from terrain.core import house
from terrain.core.survey import Point

# A 40 m square sloping up 0.1 m per metre eastward: z = 270 + 0.1 x.
PLANE = (
    Point(1, 0.0, 0.0, 270.0),
    Point(2, 40.0, 0.0, 274.0),
    Point(3, 40.0, 40.0, 274.0),
    Point(4, 0.0, 40.0, 270.0),
)
TRIANGLES = ((0, 1, 2), (0, 2, 3))
# Slope lines running due east along y = 20.
START, END = (0.0, 20.0), (40.0, 20.0)
SPEC = house.HouseSpec(
    start=10.0,
    offset=0.0,
    length=20.0,
    width=10.0,
    lower_depth=8.0,
    garage_floor=270.0,
    lower_height=3.0,
    upper_height=3.0,
    pitch_deg=45.0,
)


def test_storeys_stack_and_a_45_degree_ridge_rises_half_the_width() -> None:
    assert (SPEC.upper_floor, SPEC.wall_top) == (273.0, 276.0)
    assert SPEC.ridge == pytest.approx(281.0)


def test_corners_compare_the_ground_with_the_floor_there() -> None:
    """Front at x = 10 is 1 m above the garage floor, the lower level's back at
    x = 18 is 1.8 m, and the house's back at x = 30 is level with the upper floor.
    North is y = 25, south y = 15."""
    by_name = {c.name: c for c in house.corners(PLANE, TRIANGLES, START, END, SPEC)}
    assert by_name["front north"].position == pytest.approx((10.0, 25.0))
    assert by_name["back south"].position == pytest.approx((30.0, 15.0))
    assert [
        by_name[name].depth
        for name in ("front north", "lower back south", "back north")
    ] == pytest.approx([1.0, 1.8, 0.0])


def test_roof_ridge_runs_along_the_middle_of_the_house() -> None:
    lower, upper, roof = house.solids(START, END, SPEC)
    assert {z for _, _, z in lower.vertices} == {270.0, 273.0}
    assert {z for _, _, z in upper.vertices} == {273.0, 276.0}
    assert roof.vertices[4] == pytest.approx((10.0, 20.0, 281.0))
    assert roof.vertices[5] == pytest.approx((30.0, 20.0, 281.0))


def test_a_lower_level_deeper_than_the_house_is_refused() -> None:
    with pytest.raises(ValueError, match="deeper than the house"):
        house.HouseSpec(
            start=10.0,
            offset=0.0,
            length=20.0,
            width=10.0,
            lower_depth=21.0,
            garage_floor=270.0,
            lower_height=3.0,
            upper_height=3.0,
            pitch_deg=45.0,
        )


def test_shed_is_a_box_on_the_slope_lines() -> None:
    """10 m across, 2 m up the slope from x = 10; its floor 2 m above the ground at
    the front (x = 10, ground 271) and 1.8 m at the back (x = 12, ground 271.2)."""
    shed = house.ShedSpec(
        start=10.0, offset=0.0, depth=2.0, length=10.0, floor=273.0, height=2.5
    )
    outline = house.shed_outline(START, END, shed)
    assert [c for corner in outline for c in corner] == pytest.approx(
        [10.0, 25.0, 10.0, 15.0, 12.0, 15.0, 12.0, 25.0]
    )
    assert {z for _, _, z in house.shed_solid(outline, shed).vertices} == {273.0, 275.5}
    assert [
        c.depth
        for c in house.outline_corners(PLANE, TRIANGLES, "shed", outline, shed.floor)
    ] == pytest.approx([-2.0, -2.0, -1.8, -1.8])


def test_terrace_runs_along_the_south_wall_short_of_the_back() -> None:
    """The house's back wall is at x = 30 and its south wall at y = 15, so a 7 x 3 m
    terrace 1 m short of the back spans x 22-29 and y 15-12, its top at the upper
    floor (273): 0.8 m above the ground at x = 22, 0.1 m at x = 29."""
    terrace = house.TerraceSpec(length=7.0, width=3.0, from_back=1.0)
    outline = house.terrace_outline(START, END, SPEC, terrace)
    assert [c for corner in outline for c in corner] == pytest.approx(
        [22.0, 15.0, 22.0, 12.0, 29.0, 12.0, 29.0, 15.0]
    )
    heights = sorted({z for _, _, z in house.terrace_solid(outline, SPEC).vertices})
    assert heights == pytest.approx([272.8, 273.0])
    assert [
        c.depth
        for c in house.outline_corners(
            PLANE, TRIANGLES, "terrace", outline, SPEC.upper_floor
        )
    ] == pytest.approx([-0.8, -0.8, -0.1, -0.1])
