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

    `knee_top` is where the slopes spring from; with no knee wall it coincides
    with `wall_top`, which is why the renderer needs no separate no-knee case.
    """

    apex: Point
    wall_top: tuple[Point, Point]
    knee_top: tuple[Point, Point]
    eave_outer: tuple[Point, Point]
    headroom_line: tuple[Point, Point] | None


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
    # The slopes spring from the top of the knee wall and the eave overhang
    # continues them outward and *down* — so with no knee wall the eave sits
    # below the wall top, not level with it.
    eave_drop = roof.overhang_eave * math.tan(math.radians(roof.pitch_deg))
    eave_x = half_width + roof.overhang_eave
    usable = attic_calc.usable_width(house, roof, attic)
    return SectionGeometry(
        apex=Point(0.0, knee + roof_calc.ridge_height(house, roof)),
        wall_top=(Point(-half_width, 0.0), Point(half_width, 0.0)),
        knee_top=(Point(-half_width, knee), Point(half_width, knee)),
        eave_outer=(Point(-eave_x, knee - eave_drop), Point(eave_x, knee - eave_drop)),
        headroom_line=(
            (Point(-usable / 2, attic.h_min), Point(usable / 2, attic.h_min))
            if usable > 0
            else None
        ),
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
