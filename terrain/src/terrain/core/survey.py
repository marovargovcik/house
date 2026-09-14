"""Survey points in the plot frame. Pure."""

from dataclasses import dataclass

EAST_ORIGIN = 489216.00
NORTH_ORIGIN = 1201780.00


@dataclass(frozen=True, slots=True)
class Point:
    number: int
    x: float
    y: float
    z: float


def parse(text: str) -> tuple[Point, ...]:
    """Rows of number, Y, X, height. S-JTSK's Y and X point west and south, so both
    flip; a height of 0.00 marks a position, not the ground."""
    rows = (line.split() for line in text.splitlines() if line.strip())
    return tuple(
        Point(
            number=int(number),
            x=EAST_ORIGIN - float(y),
            y=NORTH_ORIGIN - float(x),
            z=float(z),
        )
        for number, y, x, z in rows
        if float(z) != 0
    )
