"""3D coordinates for the page, in metres. Pure."""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol

from terrain.core.survey import Point

Vertex = tuple[float, float, float]

# Display sizes only.
FENCE_HEIGHT = 1.2
TREE_HEIGHT = 5.0
SHED_HEIGHT = 2.5
LINE_STEP = 1.0
ARROW_LENGTH = 4.0
LABEL_LIFT = 1.0
COMPASS_MARGIN = 5.0


@dataclass(frozen=True, slots=True)
class Compass:
    """North is the survey grid's north."""

    north: Vertex
    south: Vertex
    east: Vertex
    west: Vertex
    arrow_tail: Vertex


@dataclass(frozen=True, slots=True)
class Extent:
    x: tuple[float, float]
    y: tuple[float, float]
    z: tuple[float, float]


class Located(Protocol):
    @property
    def x(self) -> float: ...
    @property
    def y(self) -> float: ...
    @property
    def z(self) -> float: ...


def by_number(points: Sequence[Point]) -> dict[int, Point]:
    return {point.number: point for point in points}


def above(located: Iterable[Located], height: float) -> tuple[Vertex, ...]:
    return tuple((p.x, p.y, p.z + height) for p in located)


def raised(
    points: Mapping[int, Point], numbers: Sequence[int], height: float
) -> tuple[Vertex, ...]:
    return above((points[n] for n in numbers), height)


def posts(
    points: Mapping[int, Point], numbers: Sequence[int], height: float
) -> tuple[tuple[Vertex, Vertex], ...]:
    return tuple(
        (
            (points[n].x, points[n].y, points[n].z),
            (points[n].x, points[n].y, points[n].z + height),
        )
        for n in numbers
    )


def midpoint(a: Located, b: Located, height: float) -> Vertex:
    return ((a.x + b.x) / 2, (a.y + b.y) / 2, (a.z + b.z) / 2 + height)


def extent(points: Sequence[Point], highest: float) -> Extent:
    xs, ys, zs = [p.x for p in points], [p.y for p in points], [p.z for p in points]
    return Extent(
        x=(min(xs) - COMPASS_MARGIN, max(xs) + COMPASS_MARGIN),
        y=(min(ys) - COMPASS_MARGIN, max(ys) + COMPASS_MARGIN),
        z=(min(zs), max(highest, *zs)),
    )


def aspect(box: Extent, exaggeration: float) -> tuple[float, float, float]:
    x_span = box.x[1] - box.x[0]
    y_span = box.y[1] - box.y[0]
    z_span = box.z[1] - box.z[0]
    return (1.0, y_span / x_span, z_span * exaggeration / x_span)


def compass(points: Sequence[Point]) -> Compass:
    xs, ys = [p.x for p in points], [p.y for p in points]
    x_mid, y_mid = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    z = max(p.z for p in points) + LABEL_LIFT
    north_y = max(ys) + COMPASS_MARGIN
    return Compass(
        north=(x_mid, north_y, z),
        south=(x_mid, min(ys) - COMPASS_MARGIN, z),
        east=(max(xs) + COMPASS_MARGIN, y_mid, z),
        west=(min(xs) - COMPASS_MARGIN, y_mid, z),
        arrow_tail=(x_mid, north_y - ARROW_LENGTH, z),
    )
