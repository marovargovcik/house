"""Ground slope along straight lines. Pure."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import pairwise

from terrain.core import ground
from terrain.core.ground import Triangle
from terrain.core.survey import Point

# From the bottom corner by the road to the top, repeated towards the plot's middle.
START = 115
END = 5002
OFFSETS = (0.0, 7.0, 14.0)

# A shorter leftover at the end of a line is floating-point noise, not a section.
MIN_SECTION = 1e-6

Position = tuple[float, float]


@dataclass(frozen=True, slots=True)
class Sample:
    distance: float
    x: float
    y: float
    z: float


@dataclass(frozen=True, slots=True)
class Section:
    start: Sample
    end: Sample

    @property
    def rise(self) -> float:
        return self.end.z - self.start.z

    @property
    def slope_deg(self) -> float:
        return math.degrees(
            math.atan2(self.rise, self.end.distance - self.start.distance)
        )


@dataclass(frozen=True, slots=True)
class Profile:
    offset: float
    sections: tuple[Section, ...]


def shifted(start: Position, end: Position, offset: float) -> tuple[Position, Position]:
    """The line moved `offset` metres to its right."""
    (x0, y0), (x1, y1) = start, end
    length = math.hypot(x1 - x0, y1 - y0)
    dx = (y1 - y0) / length * offset
    dy = -(x1 - x0) / length * offset
    return (x0 + dx, y0 + dy), (x1 + dx, y1 + dy)


def samples(
    points: Sequence[Point],
    triangles: Sequence[Triangle],
    start: Position,
    end: Position,
    step: float,
) -> tuple[Sample, ...]:
    (x0, y0), (x1, y1) = start, end
    length = math.hypot(x1 - x0, y1 - y0)
    inner = (
        i * step
        for i in range(1, math.ceil(length / step))
        if i * step < length - MIN_SECTION
    )

    def at(distance: float) -> Sample:
        t = distance / length
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        z = ground.height(points, triangles, x, y)
        if z is None:
            raise ValueError(f"the line leaves the survey at {distance:.1f} m")
        return Sample(distance=distance, x=x, y=y, z=z)

    return tuple(at(distance) for distance in (0.0, *inner, length))


def sections(line: Sequence[Sample]) -> tuple[Section, ...]:
    return tuple(Section(start=a, end=b) for a, b in pairwise(line))
