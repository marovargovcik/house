"""Plot sides, area and distances, measured flat. Pure."""

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import pairwise

from terrain.core import profile
from terrain.core.ground import Triangle
from terrain.core.profile import Position, Sample
from terrain.core.survey import Point


@dataclass(frozen=True, slots=True)
class Side:
    start: int
    end: int
    length: float


@dataclass(frozen=True, slots=True)
class Setback:
    """The line `limit` metres in from a side, and the way across to a building."""

    limit: float
    gap: float
    limit_line: tuple[Sample, ...]
    measure: tuple[Sample, ...]


def sides(numbered: Mapping[int, Point], corners: Sequence[int]) -> tuple[Side, ...]:
    return tuple(
        Side(
            start=a,
            end=b,
            length=math.hypot(
                numbered[b].x - numbered[a].x, numbered[b].y - numbered[a].y
            ),
        )
        for a, b in pairwise((*corners, corners[0]))
    )


def area(numbered: Mapping[int, Point], corners: Sequence[int]) -> float:
    """Shoelace formula."""
    twice = sum(
        numbered[a].x * numbered[b].y - numbered[b].x * numbered[a].y
        for a, b in pairwise((*corners, corners[0]))
    )
    return abs(twice) / 2


def _closest_on_segment(p: Position, a: Position, b: Position) -> Position:
    (px, py), (ax, ay), (bx, by) = p, a, b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return (ax + t * dx, ay + t * dy)


def nearest(
    a: Position, b: Position, outline: Sequence[Position]
) -> tuple[Position, Position]:
    """The closest (outline, side) point pair, for an outline not crossing a-b."""
    pairs = [
        *((corner, _closest_on_segment(corner, a, b)) for corner in outline),
        *(
            (_closest_on_segment(end, c, d), end)
            for c, d in pairwise((*outline, outline[0]))
            for end in (a, b)
        ),
    ]
    return min(pairs, key=lambda pair: math.dist(*pair))


def gap(a: Position, b: Position, outline: Sequence[Position]) -> float:
    return math.dist(*nearest(a, b, outline))


def outline_gap(a: Sequence[Position], b: Sequence[Position]) -> float:
    return min(gap(c, d, b) for c, d in pairwise((*a, a[0])))


def contains(ring: Sequence[Position], p: Position) -> bool:
    x, y = p
    crossings = sum(
        1
        for (x0, y0), (x1, y1) in pairwise((*ring, ring[0]))
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0)
    )
    return crossings % 2 == 1


def shifted_toward(
    a: Position, b: Position, distance: float, toward: Position
) -> tuple[Position, Position]:
    (ax, ay), (bx, by) = a, b
    length = math.hypot(bx - ax, by - ay)
    nx, ny = (by - ay) / length, -(bx - ax) / length
    sign = 1.0 if (toward[0] - ax) * nx + (toward[1] - ay) * ny >= 0 else -1.0
    dx, dy = sign * nx * distance, sign * ny * distance
    return (ax + dx, ay + dy), (bx + dx, by + dy)


def setback(
    points: Sequence[Point],
    triangles: Sequence[Triangle],
    a: Position,
    b: Position,
    outline: Sequence[Position],
    limit: float,
    step: float,
) -> Setback:
    near, far = nearest(a, b, outline)
    distance = math.dist(near, far)
    return Setback(
        limit=limit,
        gap=distance,
        limit_line=profile.samples(
            points, triangles, *shifted_toward(a, b, limit, near), step
        ),
        measure=profile.samples(points, triangles, far, near, step)
        if distance > 0
        else (),
    )
