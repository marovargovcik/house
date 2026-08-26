"""Orthographic views of the gable roof (sedlová strecha), in metres.

Pure — see `docs/spec.md` §3. These are the coordinates a drawing is made of,
which makes them numbers like any other: they come from the same
`roof.ridge_height` and `attic.usable_width` the sweep table uses, so a picture
and the row printed beside it cannot drift apart.

Two frames, each centred on the house so a renderer never needs the footprint to
place anything:

- section (priečny rez): `x` across the width, `y` up from the wall top (datum 0)
- plan (pôdorys): `x` along the length, `y` across the width
"""

import math
from dataclasses import dataclass
from typing import NamedTuple, Self

from house.core import attic as attic_calc
from house.core import roof as roof_calc
from house.core.specs import AtticSpec, HouseSpec, RoofSpec


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
    """Gable-end section. Origin is the centre of the wall top.

    Carries the structure *and* the finished surfaces, because they are not the
    same line and the difference is what headroom is made of: `apex` is the
    structural ridge, `ceiling` is the plane you would actually hit, `floor` sits
    above the wall top by the floor build-up.

    `knee_top` is where the slopes spring from; with no knee wall it coincides
    with `wall_top`, which is why the renderer needs no separate no-knee case.
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
    # The slopes spring from the top of the knee wall and the eave overhang
    # continues them outward and *down* — so with no knee wall the eave sits
    # below the wall top, not level with it.
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
    """Where the collar tie (klieština) meets the finished ceiling, if there is one.

    Half-span comes from reading the ceiling plane backwards at the collar's
    height. A collar sitting at or above the ceiling apex has no span to draw —
    it would not be a collar.
    """
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
    """The cross-section you can actually stand in.

    Floor strip up to `h_min`, then the finished ceiling on to the ridge — capped
    flat by the collar where there is one, because you walk into a collar the
    same way you walk into a ceiling. Its base is exactly `usable_width`, so the
    shape on the drawing and the number in the table are one fact drawn twice.
    """
    usable = attic_calc.usable_width(house, roof, attic)
    if usable <= 0:
        return None
    floor_y = attic.floor_buildup
    top = floor_y + attic.h_min
    collar = _collar(house, roof, attic, attic_calc.ceiling_drop(roof, attic))

    # Right to left along the top. A knee wall tall enough that the ceiling
    # already clears h_min at the wall turns the corner at the ceiling's ends
    # instead of on the slope.
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
