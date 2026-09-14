"""Hand-checked references for roof geometry and cost."""

import math

import pytest

from roof.core import roof
from roof.core.specs import CostSpec, HouseSpec, RoofSpec

HOUSE = HouseSpec(width=9.0, length=10.0)
BARE = {"overhang_eave": 0.0, "overhang_gable": 0.0}
OVERHANGS = {"overhang_eave": 0.6, "overhang_gable": 0.4}
COSTS = CostSpec(eur_per_m2=110.0)


def test_area_scales_with_pitch() -> None:
    """No overhang: 45° gives footprint x √2 = 127.2792 m², nearly flat the 90 m²."""
    assert roof.surface_area(HOUSE, RoofSpec(pitch_deg=45.0, **BARE)) == pytest.approx(
        90.0 * math.sqrt(2)
    )
    assert roof.surface_area(HOUSE, RoofSpec(pitch_deg=0.01, **BARE)) == pytest.approx(
        90.0, abs=1e-4
    )


def test_overhangs_are_wired_to_their_own_factors() -> None:
    """0.6 m eave / 0.4 m gable at 30° → 127.2018 m²; swapped → 126.7399 m².

    Only bites on a non-square house with unequal overhangs.
    """
    at_30 = RoofSpec(pitch_deg=30.0, **OVERHANGS)
    swapped = RoofSpec(pitch_deg=30.0, overhang_eave=0.4, overhang_gable=0.6)

    assert roof.surface_area(HOUSE, at_30) == pytest.approx(127.2018, abs=1e-4)
    assert roof.surface_area(HOUSE, swapped) == pytest.approx(126.7399, abs=1e-4)
    assert roof.surface_area(HOUSE, RoofSpec(pitch_deg=30.0, **BARE)) == pytest.approx(
        10.0 * 9.0 / math.cos(math.radians(30.0))
    )


def test_geometry_at_30_degrees() -> None:
    """Ridge 2.5981 m, rafter 5.889 m, gutter 21.6 m — the gutter at any pitch."""
    geom = roof.geometry(HOUSE, RoofSpec(pitch_deg=30.0, **OVERHANGS))
    assert geom.ridge_height == pytest.approx(2.5981, abs=1e-4)
    assert geom.rafter_length == pytest.approx(5.889, abs=1e-4)
    assert geom.gutter_run == pytest.approx(21.6)
    assert roof.geometry(
        HOUSE, RoofSpec(pitch_deg=45.0, **OVERHANGS)
    ).gutter_run == pytest.approx(21.6)


def test_cost_is_one_all_in_rate_charged_on_gross_area() -> None:
    """127.2018 m² x 110 EUR → 13 992.20 EUR; without overhangs 11 431.54 EUR."""
    geom = roof.geometry(HOUSE, RoofSpec(pitch_deg=30.0, **OVERHANGS))
    bare = roof.geometry(HOUSE, RoofSpec(pitch_deg=30.0, **BARE))

    assert roof.cost(geom, COSTS) == pytest.approx(13992.1992, abs=1e-3)
    assert roof.cost(bare, COSTS) == pytest.approx(11431.5353, abs=1e-3)
