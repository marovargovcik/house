"""Sweep table → CSV.

An interpreter: this is the only place a sweep result touches the disk. The core
builds the table and knows nothing about where it goes.
"""

from pathlib import Path

import pandas as pd


def write_csv(table: pd.DataFrame, path: Path) -> None:
    """Write `table` to `path` at full precision.

    The index is a bare row counter for a sweep table, so it is dropped — carried
    into the CSV it would read as a column that means something.
    """
    table.to_csv(path, index=False)
