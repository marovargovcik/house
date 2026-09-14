"""Sweep rows → CSV."""

import csv
import io
import math
from collections.abc import Sequence
from dataclasses import astuple
from pathlib import Path

from roof.core.sweep import SweepRow, column_names


def render_csv(rows: Sequence[SweepRow]) -> str:
    """The rows at full precision; rounding is the reader's job."""
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(column_names())
    writer.writerows(
        # Empty, not "nan", so a spreadsheet keeps the column numeric.
        ["" if isinstance(v, float) and math.isnan(v) else v for v in astuple(row)]
        for row in rows
    )
    return out.getvalue()


def write_csv(rows: Sequence[SweepRow], path: Path) -> None:
    path.write_text(render_csv(rows), encoding="utf-8")
