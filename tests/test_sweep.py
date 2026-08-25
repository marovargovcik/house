"""The sweep is plumbing over pinned functions — check the wiring, not the math."""

import math

import pytest

from house.core import sweep
from house.core.specs import AtticSpec, CostSpec, RoofingLayer

COSTS = CostSpec(
    layers=(RoofingLayer(name="all-in", eur_per_m2=38.0),),
    krov_eur_per_m2=60.0,
    gutter_eur_per_m=30.0,
)


def test_row_matches_the_hand_checked_case_and_flags_unusable_pitches() -> None:
    """The 9 m / 30° row must reproduce the values pinned in the unit tests, and
    the 20° row (ridge below h_min) must carry NaN rather than a ranking-beating
    zero-division artefact."""
    table = sweep.width_by_pitch(
        widths=[9.0],
        pitches_deg=[20.0, 30.0],
        length=10.0,
        attic=AtticSpec(h_min=1.9),
        costs=COSTS,
        overhang_eave=0.6,
        overhang_gable=0.4,
    )

    assert len(table) == 2
    row = table[table["pitch_deg"] == 30.0].iloc[0]
    assert row["roof_area_m2"] == pytest.approx(127.2018, abs=1e-4)
    assert row["usable_area_m2"] == pytest.approx(24.1821, abs=1e-4)
    assert row["total_eur"] == pytest.approx(13113.7775, abs=1e-4)
    assert row["eur_per_usable_m2"] == pytest.approx(542.2934, abs=1e-4)
    assert row["usable_fraction"] == pytest.approx(0.2687, abs=1e-4)

    shallow = table[table["pitch_deg"] == 20.0].iloc[0]
    assert shallow["usable_area_m2"] == 0.0
    assert math.isnan(shallow["eur_per_usable_m2"])
