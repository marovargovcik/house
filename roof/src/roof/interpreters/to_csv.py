"""Sweep rows → CSV.

Split in two on purpose: `render_csv` builds the text and `write_csv` puts it on
disk. Only the second is an effect, so a caller with nowhere to write — a browser
runtime, a test — can have the numbers without one.
"""

import csv
import io
import math
from collections.abc import Sequence
from dataclasses import astuple
from pathlib import Path

from roof.core.sweep import SweepRow, column_names


def render_csv(rows: Sequence[SweepRow]) -> str:
    """The rows at full precision.

    `str` of a float round-trips exactly in Python, so the CSV carries what the
    calculation produced rather than what a display format left of it — the
    rounding belongs to whatever reads this, not to the record of it.
    """
    out = io.StringIO(newline="")
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(column_names())
    writer.writerows(
        # An empty cell rather than the text "nan": a spreadsheet reads the first
        # as a gap in a numeric column and the second as a string, which turns
        # the whole column into text.
        ["" if isinstance(v, float) and math.isnan(v) else v for v in astuple(row)]
        for row in rows
    )
    return out.getvalue()


def write_csv(rows: Sequence[SweepRow], path: Path) -> None:
    path.write_text(render_csv(rows), encoding="utf-8")
