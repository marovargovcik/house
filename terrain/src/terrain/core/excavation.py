"""Earth dug out for the house and shed, and fill under the floors. Pure."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from terrain.core import ground
from terrain.core.ground import Triangle
from terrain.core.house import HouseSpec, ShedSpec, locate
from terrain.core.profile import Position
from terrain.core.survey import Point

CELL = 0.25  # metres between ground samples


@dataclass(frozen=True, slots=True)
class DigSpec:
    """`floor_buildup` runs from the finished floor to the bottom of the gravel under
    the slab; footings go `footing_depth` below that. `working_space` is dug beyond
    buried walls for waterproofing."""

    floor_buildup: float
    footing_width: float
    footing_depth: float
    working_space: float

    def __post_init__(self) -> None:
        sizes = (self.floor_buildup, self.footing_width, self.footing_depth)
        if not all(math.isfinite(size) and size > 0 for size in sizes):
            raise ValueError("floor build-up and footing sizes must be positive")
        if not (math.isfinite(self.working_space) and self.working_space >= 0):
            raise ValueError(
                f"working space must not be negative, got {self.working_space}"
            )


@dataclass(frozen=True, slots=True)
class Area:
    """`front` to `back` up the slope lines, `north` to `south` beside the first."""

    front: float
    back: float
    north: float
    south: float


@dataclass(frozen=True, slots=True)
class Pit:
    name: str
    area: Area
    formation: float
    footing_length: float
    cut: float
    fill: float
    footings: float


def volumes(
    points: Sequence[Point],
    triangles: Sequence[Triangle],
    start: Position,
    end: Position,
    area: Area,
    formation: float,
    cell: float,
) -> tuple[float, float]:
    """Cut and fill against `formation`, from the ground at each cell's centre."""
    along = max(1, round((area.back - area.front) / cell))
    across = max(1, round((area.south - area.north) / cell))
    step_along = (area.back - area.front) / along
    step_across = (area.south - area.north) / across

    def depth(i: int, j: int) -> float:
        position = locate(
            start,
            end,
            area.front + (i + 0.5) * step_along,
            area.north + (j + 0.5) * step_across,
        )
        z = ground.height(points, triangles, *position)
        if z is None:
            raise ValueError("the excavation reaches beyond the survey")
        return z - formation

    depths = [depth(i, j) for i in range(along) for j in range(across)]
    cell_area = step_along * step_across
    return (
        sum(d for d in depths if d > 0) * cell_area,
        -sum(d for d in depths if d < 0) * cell_area,
    )


def pits(
    points: Sequence[Point],
    triangles: Sequence[Triangle],
    start: Position,
    end: Position,
    house: HouseSpec,
    shed: ShedSpec,
    dig: DigSpec,
    cell: float,
) -> tuple[Pit, ...]:
    """Garage level and shed dug with working space round them; the rest of the
    house levelled within its walls. Footings under outer walls only."""
    space = dig.working_space
    north, south = house.offset - house.width / 2, house.offset + house.width / 2
    garage_back = house.start + house.lower_depth
    parts = (
        (
            "garage level",
            Area(
                house.start - space, garage_back + space, north - space, south + space
            ),
            house.garage_floor,
            2 * house.lower_depth + 2 * house.width,
        ),
        (
            "rest of the house",
            Area(garage_back + space, house.start + house.length, north, south),
            house.upper_floor,
            2 * (house.length - house.lower_depth) + house.width,
        ),
        (
            "garden shed",
            Area(
                shed.start,
                shed.start + shed.depth + space,
                shed.offset - shed.length / 2 - space,
                shed.offset + shed.length / 2 + space,
            ),
            shed.floor,
            2 * shed.depth + shed.length,
        ),
    )

    def pit(name: str, area: Area, floor: float, footing_length: float) -> Pit:
        formation = floor - dig.floor_buildup
        cut, fill = volumes(points, triangles, start, end, area, formation, cell)
        return Pit(
            name=name,
            area=area,
            formation=formation,
            footing_length=footing_length,
            cut=cut,
            fill=fill,
            footings=footing_length * dig.footing_width * dig.footing_depth,
        )

    return tuple(pit(*part) for part in parts)


def totals(pits: Sequence[Pit]) -> tuple[float, float]:
    """Cut including footing trenches, and fill."""
    return sum(p.cut + p.footings for p in pits), sum(p.fill for p in pits)
