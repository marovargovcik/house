"""The CSV interpreter must hand the sweep's numbers on unchanged."""

from dataclasses import replace
from pathlib import Path

from roof.core.sweep import SweepRow, column_names
from roof.interpreters import to_csv

ROW = SweepRow(
    width_m=9.0,
    pitch_deg=30.0,
    roof_area_m2=127.20181130785834,
    ridge_above_wall_top_m=2.598076211353315,
    clear_ridge_m=2.0516660498395396,
    usable_width_m=0.525386608210713,
    usable_area_m2=5.25386608210713,
    usable_fraction=0.058376289801190334,
    total_eur=13992.199243864417,
    eur_per_usable_m2=2663.2196225018106,
)


def test_csv_keeps_full_precision() -> None:
    """Every figure survives the round trip exactly."""
    lines = to_csv.render_csv([ROW]).splitlines()

    assert lines[0] == ",".join(column_names())
    assert [float(cell) for cell in lines[1].split(",")] == [
        9.0,
        30.0,
        127.20181130785834,
        2.598076211353315,
        2.0516660498395396,
        0.525386608210713,
        5.25386608210713,
        0.058376289801190334,
        13992.199243864417,
        2663.2196225018106,
    ]


def test_no_habitable_attic_leaves_the_cell_empty() -> None:
    """NaN goes out as an empty cell, so the column stays numeric."""
    unusable = replace(ROW, usable_area_m2=0.0, eur_per_usable_m2=float("nan"))
    assert to_csv.render_csv([unusable]).splitlines()[1].endswith(",")


def test_write_csv_is_render_csv_on_disk(tmp_path: Path) -> None:
    """`write_csv` writes exactly what `render_csv` returns."""
    path = tmp_path / "sweep.csv"
    to_csv.write_csv([ROW], path)
    assert path.read_text(encoding="utf-8") == to_csv.render_csv([ROW])
