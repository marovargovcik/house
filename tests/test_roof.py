"""Hand-checked references for roof geometry and cost (docs/spec.md §3a)."""

import math

import pytest

from house.core import roof
from house.core.specs import CostSpec, HouseSpec, RoofingLayer, RoofSpec

HOUSE = HouseSpec(width=9.0, length=10.0)
BARE = {"overhang_eave": 0.0, "overhang_gable": 0.0}
COSTS = CostSpec(
    layers=(
        RoofingLayer(name="sheet", eur_per_m2=25.0),
        RoofingLayer(name="membrane", eur_per_m2=5.0),
        RoofingLayer(name="battens", eur_per_m2=8.0),
    ),
    krov_eur_per_m2=60.0,
    gutter_eur_per_m=30.0,
)


def test_area_scales_with_pitch() -> None:
    """The two sanity checks docs/spec.md §3a asks for, both without overhang.

    At 45° the roof is footprint x sqrt(2) = 127.2792 m². As the pitch flattens
    the area collapses back onto the 90 m² footprint. Together these pin the
    direction of the 1 / cos θ term.
    """
    assert roof.surface_area(HOUSE, RoofSpec(pitch_deg=45.0, **BARE)) == pytest.approx(
        90.0 * math.sqrt(2)
    )
    assert roof.surface_area(HOUSE, RoofSpec(pitch_deg=0.01, **BARE)) == pytest.approx(
        90.0, abs=1e-4
    )


def test_overhangs_are_wired_to_their_own_factors() -> None:
    """0.6 m eave / 0.4 m gable at 30° -> 127.2018 m²; swapped -> 126.7399 m².

    The swap is the check that catches the two terms landing on the wrong side
    of the / cos θ division (docs/decisions.md). It only bites because the house
    is not square and the two overhangs differ — with either symmetry the wrong
    wiring passes. Zeroing both must recover the pre-overhang formula.
    """
    at_30 = RoofSpec(pitch_deg=30.0, overhang_eave=0.6, overhang_gable=0.4)
    swapped = RoofSpec(pitch_deg=30.0, overhang_eave=0.4, overhang_gable=0.6)

    assert roof.surface_area(HOUSE, at_30) == pytest.approx(127.2018, abs=1e-4)
    assert roof.surface_area(HOUSE, swapped) == pytest.approx(126.7399, abs=1e-4)
    assert roof.surface_area(HOUSE, RoofSpec(pitch_deg=30.0, **BARE)) == pytest.approx(
        10.0 * 9.0 / math.cos(math.radians(30.0))
    )


def test_geometry_at_30_degrees() -> None:
    """Ridge 2.5981 m, rafter 5.889 m, gutter run 21.6 m for the 9 x 10 m house.

    The gutter run is horizontal, so it must not move with pitch.
    """
    geom = roof.geometry(HOUSE, RoofSpec(pitch_deg=30.0))
    assert geom.ridge_height == pytest.approx(2.5981, abs=1e-4)
    assert geom.rafter_length == pytest.approx(5.889, abs=1e-4)
    assert geom.gutter_run == pytest.approx(21.6)
    assert roof.geometry(HOUSE, RoofSpec(pitch_deg=45.0)).gutter_run == pytest.approx(
        21.6
    )


def test_cost_splits_area_rates_from_the_per_metre_gutter() -> None:
    """127.2018 m² at 38 + 60 EUR/m², plus 21.6 m of gutter at 30 EUR/m.

    Pins that roofing and krov are charged on gross area (deliberate
    over-estimate, docs/decisions.md) while gutters are charged per metre.
    """
    geom = roof.geometry(HOUSE, RoofSpec(pitch_deg=30.0))
    cost = roof.cost(geom, COSTS)
    assert cost.roofing == pytest.approx(4833.6688, abs=1e-3)
    assert cost.krov == pytest.approx(7632.1087, abs=1e-3)
    assert cost.gutters == pytest.approx(648.0)
    assert cost.total == pytest.approx(13113.7775, abs=1e-3)
