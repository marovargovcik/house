"""House, shed and terrace blocks on the slope lines. Pure.

North and south are left and right facing up the slope lines.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from terrain.core import ground
from terrain.core.ground import Triangle
from terrain.core.profile import Position
from terrain.core.survey import Point
from terrain.core.views import Vertex

Footprint = tuple[Position, Position, Position, Position]

TERRACE_THICKNESS = 0.2

# Vertices 0-3 at the bottom, 4-7 on top. Faces: bottom, top, four walls.
BOX_FACES = (
    (0, 2, 1), (0, 3, 2),
    (4, 5, 6), (4, 6, 7),
    (0, 1, 5), (0, 5, 4),
    (1, 2, 6), (1, 6, 5),
    (2, 3, 7), (2, 7, 6),
    (3, 0, 4), (3, 4, 7),
)  # fmt: skip

# Vertices 0-3 at the eaves, 4-5 the ridge ends. Faces: bottom, roof, gables.
ROOF_FACES = (
    (0, 2, 1), (0, 3, 2),
    (1, 2, 5), (1, 5, 4),
    (3, 0, 4), (3, 4, 5),
    (0, 1, 4),
    (2, 3, 5),
)  # fmt: skip


@dataclass(frozen=True, slots=True)
class HouseSpec:
    """Front wall `start` up the slope lines, centre line `offset` beside the first."""

    start: float
    offset: float
    length: float
    width: float
    lower_depth: float
    garage_floor: float
    lower_height: float
    upper_height: float
    pitch_deg: float

    def __post_init__(self) -> None:
        sizes = (
            self.length,
            self.width,
            self.lower_depth,
            self.lower_height,
            self.upper_height,
        )
        if not all(math.isfinite(size) and size > 0 for size in sizes):
            raise ValueError("house sizes and storey heights must be positive")
        if self.lower_depth > self.length:
            raise ValueError(
                f"lower level ({self.lower_depth} m) is deeper than the house "
                f"({self.length} m)"
            )
        if not 0 < self.pitch_deg < 90:
            raise ValueError(
                f"pitch must be within (0, 90) degrees, got {self.pitch_deg}"
            )

    @property
    def upper_floor(self) -> float:
        return self.garage_floor + self.lower_height

    @property
    def wall_top(self) -> float:
        return self.upper_floor + self.upper_height

    @property
    def ridge(self) -> float:
        return self.wall_top + self.width / 2 * math.tan(math.radians(self.pitch_deg))


@dataclass(frozen=True, slots=True)
class ShedSpec:
    """Placed like the house; `depth` runs up the slope, `length` across it."""

    start: float
    offset: float
    depth: float
    length: float
    floor: float
    height: float

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(size) and size > 0
            for size in (self.depth, self.length, self.height)
        ):
            raise ValueError("shed sizes and height must be positive")


@dataclass(frozen=True, slots=True)
class TerraceSpec:
    """Along the house's south wall, ending `from_back` short of its back wall."""

    length: float
    width: float
    from_back: float

    def __post_init__(self) -> None:
        if not all(
            math.isfinite(size) and size > 0 for size in (self.length, self.width)
        ):
            raise ValueError("terrace length and width must be positive")
        if not (math.isfinite(self.from_back) and self.from_back >= 0):
            raise ValueError(
                "terrace distance from the back wall must not be negative, "
                f"got {self.from_back}"
            )


@dataclass(frozen=True, slots=True)
class Solid:
    vertices: tuple[Vertex, ...]
    faces: tuple[Triangle, ...]


@dataclass(frozen=True, slots=True)
class Corner:
    name: str
    position: Position
    floor: float
    ground: float

    @property
    def depth(self) -> float:
        """Ground above the floor; negative where the floor is above the ground."""
        return self.ground - self.floor


def locate(start: Position, end: Position, along: float, across: float) -> Position:
    """`along` towards `end`, then `across` to the right."""
    (x0, y0), (x1, y1) = start, end
    length = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    return (x0 + ux * along + uy * across, y0 + uy * along - ux * across)


def rectangle(
    start: Position,
    end: Position,
    front: float,
    back: float,
    north: float,
    south: float,
) -> Footprint:
    """Corners front north, front south, back south, back north."""
    return (
        locate(start, end, front, north),
        locate(start, end, front, south),
        locate(start, end, back, south),
        locate(start, end, back, north),
    )


def footprint(
    start: Position, end: Position, spec: HouseSpec, depth: float
) -> Footprint:
    return rectangle(
        start,
        end,
        spec.start,
        spec.start + depth,
        spec.offset - spec.width / 2,
        spec.offset + spec.width / 2,
    )


def shed_outline(start: Position, end: Position, spec: ShedSpec) -> Footprint:
    return rectangle(
        start,
        end,
        spec.start,
        spec.start + spec.depth,
        spec.offset - spec.length / 2,
        spec.offset + spec.length / 2,
    )


def terrace_outline(
    start: Position, end: Position, house_spec: HouseSpec, spec: TerraceSpec
) -> Footprint:
    back = house_spec.start + house_spec.length - spec.from_back
    south_wall = house_spec.offset + house_spec.width / 2
    return rectangle(
        start, end, back - spec.length, back, south_wall, south_wall + spec.width
    )


def _box(corners: Footprint, bottom: float, top: float) -> Solid:
    return Solid(
        vertices=(
            *((x, y, bottom) for x, y in corners),
            *((x, y, top) for x, y in corners),
        ),
        faces=BOX_FACES,
    )


def _roof(corners: Footprint, wall_top: float, ridge: float) -> Solid:
    front_north, front_south, back_south, back_north = corners
    return Solid(
        vertices=(
            *((x, y, wall_top) for x, y in corners),
            (
                (front_north[0] + front_south[0]) / 2,
                (front_north[1] + front_south[1]) / 2,
                ridge,
            ),
            (
                (back_north[0] + back_south[0]) / 2,
                (back_north[1] + back_south[1]) / 2,
                ridge,
            ),
        ),
        faces=ROOF_FACES,
    )


def solids(
    start: Position, end: Position, spec: HouseSpec
) -> tuple[Solid, Solid, Solid]:
    whole = footprint(start, end, spec, spec.length)
    return (
        _box(
            footprint(start, end, spec, spec.lower_depth),
            spec.garage_floor,
            spec.upper_floor,
        ),
        _box(whole, spec.upper_floor, spec.wall_top),
        _roof(whole, spec.wall_top, spec.ridge),
    )


def shed_solid(outline: Footprint, spec: ShedSpec) -> Solid:
    return _box(outline, spec.floor, spec.floor + spec.height)


def terrace_solid(outline: Footprint, house_spec: HouseSpec) -> Solid:
    return _box(
        outline, house_spec.upper_floor - TERRACE_THICKNESS, house_spec.upper_floor
    )


def _measured(
    points: Sequence[Point],
    triangles: Sequence[Triangle],
    name: str,
    position: Position,
    floor: float,
) -> Corner:
    z = ground.height(points, triangles, *position)
    if z is None:
        raise ValueError(f"the {name} corner is off the survey")
    return Corner(name=name, position=position, floor=floor, ground=z)


def corners(
    points: Sequence[Point],
    triangles: Sequence[Triangle],
    start: Position,
    end: Position,
    spec: HouseSpec,
) -> tuple[Corner, ...]:
    front_north, front_south, lower_south, lower_north = footprint(
        start, end, spec, spec.lower_depth
    )
    _, _, back_south, back_north = footprint(start, end, spec, spec.length)
    return tuple(
        _measured(points, triangles, name, position, floor)
        for name, position, floor in (
            ("front north", front_north, spec.garage_floor),
            ("front south", front_south, spec.garage_floor),
            ("lower back north", lower_north, spec.garage_floor),
            ("lower back south", lower_south, spec.garage_floor),
            ("back north", back_north, spec.upper_floor),
            ("back south", back_south, spec.upper_floor),
        )
    )


def outline_corners(
    points: Sequence[Point],
    triangles: Sequence[Triangle],
    label: str,
    outline: Footprint,
    floor: float,
) -> tuple[Corner, ...]:
    names = ("front north", "front south", "back south", "back north")
    return tuple(
        _measured(points, triangles, f"{label} {name}", position, floor)
        for name, position in zip(names, outline, strict=True)
    )
