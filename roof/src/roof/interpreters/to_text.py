"""Sweep rows → a fixed-width table for a terminal.

English column names and a plain decimal point: this is the developer-facing
view. The Slovak report is `to_html`.
"""

import math
from collections.abc import Sequence
from dataclasses import astuple

from roof.core.sweep import SweepRow, column_names

PLACES = 2
"""Decimals shown. The full-precision record is the CSV, not this."""


def _cell(value: float) -> str:
    return "NaN" if math.isnan(value) else f"{value:.{PLACES}f}"


def render_table(rows: Sequence[SweepRow]) -> str:
    """Right-aligned columns, each as wide as its widest entry."""
    headers = column_names()
    cells = [[_cell(value) for value in astuple(row)] for row in rows]
    widths = [
        max(len(header), *(len(row[index]) for row in cells)) if cells else len(header)
        for index, header in enumerate(headers)
    ]
    lines = [
        "  ".join(text.rjust(width) for text, width in zip(line, widths, strict=True))
        for line in [list(headers), *cells]
    ]
    return "\n".join(lines)
