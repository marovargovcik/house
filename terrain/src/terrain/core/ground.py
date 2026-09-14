"""The ground as flat triangles between survey points. Pure."""

from collections.abc import Sequence

from scipy.spatial import Delaunay

from terrain.core.survey import Point

Triangle = tuple[int, int, int]

EDGE_TOLERANCE = 1e-9


def triangles(points: Sequence[Point]) -> tuple[Triangle, ...]:
    mesh = Delaunay([(p.x, p.y) for p in points])
    return tuple((int(i), int(j), int(k)) for i, j, k in mesh.simplices)


def height(
    points: Sequence[Point], triangles: Sequence[Triangle], x: float, y: float
) -> float | None:
    for i, j, k in triangles:
        a, b, c = points[i], points[j], points[k]
        det = (b.y - c.y) * (a.x - c.x) + (c.x - b.x) * (a.y - c.y)
        wa = ((b.y - c.y) * (x - c.x) + (c.x - b.x) * (y - c.y)) / det
        wb = ((c.y - a.y) * (x - c.x) + (a.x - c.x) * (y - c.y)) / det
        wc = 1 - wa - wb
        if min(wa, wb, wc) >= -EDGE_TOLERANCE:
            return wa * a.z + wb * b.z + wc * c.z
    return None
