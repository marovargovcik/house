"""The CSV interpreter must hand the sweep's numbers on unchanged."""

from pathlib import Path

import pandas as pd

from house.interpreters import to_csv


def test_csv_keeps_full_precision_and_drops_the_index(tmp_path: Path) -> None:
    table = pd.DataFrame(
        [{"width_m": 9.0, "eur_per_usable_m2": 542.2933587501234}],
        index=[7],
    )
    path = tmp_path / "sweep.csv"

    to_csv.write_csv(table, path)

    assert path.read_text().splitlines()[0] == "width_m,eur_per_usable_m2"
    reloaded = pd.read_csv(path)
    assert reloaded["eur_per_usable_m2"][0] == 542.2933587501234
