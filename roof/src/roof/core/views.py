"""Drawing coordinates in metres, from the same functions as the table. Pure.

Both frames are centred on the house:

- section (priečny rez): `x` across the width, `y` up from the wall top
- plan (pôdorys): `x` along the length, `y` across the width
"""

import math
from dataclasses import dataclass
from typing import NamedTuple, Self

from roof.core import attic as attic_calc
from roof.core import roof as roof_calc
from roof.core.specs import AtticSpec, HouseSpec, RoofSpec


class Point(NamedTuple):
    x: float
    y: float


@dataclass(frozen=True, slots=True)
class Rect:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @classmethod
    def centred(cls, x_span: float, y_span: float) -> Self:
        return cls(-x_span / 2, -y_span / 2, x_span / 2, y_span / 2)


@dataclass(frozen=True, slots=True)
class SectionGeometry:
    """Gable-end section; origin at the centre of the wall top.

    `apex` is the structure, `ceiling` and `floor` the finished surfaces. With no
    knee wall, `knee_top` equals `wall_top`.
    """

    apex: Point
    wall_top: tuple[Point, Point]
    knee_top: tuple[Point, Point]
    eave_outer: tuple[Point, Point]
    floor: tuple[Point, Point]
    ceiling: tuple[Point, Point, Point]
    collar: tuple[Point, Point] | None
    headroom_line: tuple[Point, Point] | None
    standing_room: tuple[Point, ...] | None


@dataclass(frozen=True, slots=True)
class PlanGeometry:
    """Roof in plan. Origin is the centre of the footprint."""

    walls: Rect
    roof_outline: Rect
    ridge: tuple[Point, Point]
    usable_strip: Rect | None


def section(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> SectionGeometry:
    half_width = house.width / 2
    knee = attic.knee_height
    slope = math.tan(math.radians(roof.pitch_deg))
    # The eave overhang continues the slope down, below the knee top.
    eave_x = half_width + roof.overhang_eave
    eave_y = knee - roof.overhang_eave * slope

    drop = attic_calc.ceiling_drop(roof, attic)
    floor_y = attic.floor_buildup
    apex = Point(0.0, knee + roof_calc.ridge_height(house, roof))
    ceiling_apex = Point(0.0, apex.y - drop)
    ceiling_ends = (
        Point(-half_width, knee - drop),
        Point(half_width, knee - drop),
    )

    return SectionGeometry(
        apex=apex,
        wall_top=(Point(-half_width, 0.0), Point(half_width, 0.0)),
        knee_top=(Point(-half_width, knee), Point(half_width, knee)),
        eave_outer=(Point(-eave_x, eave_y), Point(eave_x, eave_y)),
        floor=(Point(-half_width, floor_y), Point(half_width, floor_y)),
        ceiling=(ceiling_ends[0], ceiling_apex, ceiling_ends[1]),
        collar=_collar(house, roof, attic, drop),
        headroom_line=_headroom_line(house, roof, attic),
        standing_room=_standing_room(house, roof, attic, ceiling_apex, ceiling_ends),
    )


def _collar(
    house: HouseSpec, roof: RoofSpec, attic: AtticSpec, drop: float
) -> tuple[Point, Point] | None:
    """Where the collar tie (klieština) meets the ceiling; `None` if it doesn't."""
    if attic.collar_above_wall_top is None:
        return None
    height = attic.collar_above_wall_top
    inset = (height - attic.knee_height + drop) / math.tan(math.radians(roof.pitch_deg))
    half_span = house.width / 2 - inset
    if half_span <= 0:
        return None
    return (Point(-half_span, height), Point(half_span, height))


def _headroom_line(
    house: HouseSpec, roof: RoofSpec, attic: AtticSpec
) -> tuple[Point, Point] | None:
    """The `h_min` line, measured up from the *finished floor*."""
    usable = attic_calc.usable_width(house, roof, attic)
    if usable <= 0:
        return None
    height = attic.floor_buildup + attic.h_min
    return (Point(-usable / 2, height), Point(usable / 2, height))


def _standing_room(
    house: HouseSpec,
    roof: RoofSpec,
    attic: AtticSpec,
    ceiling_apex: Point,
    ceiling_ends: tuple[Point, Point],
) -> tuple[Point, ...] | None:
    """The region you can stand in: base `usable_width`, up to `h_min`, then the
    ceiling, capped flat by a collar."""
    usable = attic_calc.usable_width(house, roof, attic)
    if usable <= 0:
        return None
    floor_y = attic.floor_buildup
    top = floor_y + attic.h_min
    collar = _collar(house, roof, attic, attic_calc.ceiling_drop(roof, attic))

    # Right to left along the top. If the ceiling clears h_min at the wall, the
    # corners are the ceiling's ends.
    upper: list[Point] = []
    turns_at_the_wall = ceiling_ends[1].y - floor_y > attic.h_min
    if turns_at_the_wall:
        upper.append(ceiling_ends[1])
    if collar is not None and collar[1].y < ceiling_apex.y:
        upper += [collar[1], collar[0]]
    else:
        upper.append(ceiling_apex)
    if turns_at_the_wall:
        upper.append(ceiling_ends[0])

    return (
        Point(-usable / 2, floor_y),
        Point(usable / 2, floor_y),
        Point(usable / 2, top),
        *upper,
        Point(-usable / 2, top),
    )


def plan(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> PlanGeometry:
    """Plan view. The ridge runs the full length *including* the rake overhang."""
    usable = attic_calc.usable_width(house, roof, attic)
    ridge_half = house.length / 2 + roof.overhang_gable
    return PlanGeometry(
        walls=Rect.centred(house.length, house.width),
        roof_outline=Rect.centred(
            house.length + 2 * roof.overhang_gable,
            house.width + 2 * roof.overhang_eave,
        ),
        ridge=(Point(-ridge_half, 0.0), Point(ridge_half, 0.0)),
        usable_strip=Rect.centred(house.length, usable) if usable > 0 else None,
    )
