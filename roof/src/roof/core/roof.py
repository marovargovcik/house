"""Gable roof geometry and cost. Pure."""

import math
from dataclasses import dataclass

from roof.core.specs import CostSpec, HouseSpec, RoofSpec


@dataclass(frozen=True, slots=True)
class RoofGeometry:
    surface_area: float
    ridge_height: float
    rafter_length: float
    gutter_run: float


def ridge_height(house: HouseSpec, roof: RoofSpec) -> float:
    """Height of the ridge (hrebeň) above the wall top."""
    return house.width / 2 * math.tan(math.radians(roof.pitch_deg))


def rafter_length(house: HouseSpec, roof: RoofSpec) -> float:
    """Sloped length of one rafter (krokva), eave overhang included."""
    return (house.width / 2 + roof.overhang_eave) / math.cos(
        math.radians(roof.pitch_deg)
    )


def surface_area(house: HouseSpec, roof: RoofSpec) -> float:
    """Both roof planes. The eave overhang follows the slope, so `1 / cos θ`
    stretches it; the gable overhang runs along the ridge, so it doesn't."""
    return (
        (house.length + 2 * roof.overhang_gable)
        * (house.width + 2 * roof.overhang_eave)
        / math.cos(math.radians(roof.pitch_deg))
    )


def gutter_run(house: HouseSpec, roof: RoofSpec) -> float:
    """Gutter (odkvapový žľab) length along both eaves; pitch doesn't change it.
    For ordering, not costing. Downpipes (zvody) are not modelled."""
    return 2 * (house.length + 2 * roof.overhang_gable)


def geometry(house: HouseSpec, roof: RoofSpec) -> RoofGeometry:
    return RoofGeometry(
        surface_area=surface_area(house, roof),
        ridge_height=ridge_height(house, roof),
        rafter_length=rafter_length(house, roof),
        gutter_run=gutter_run(house, roof),
    )


def cost(geom: RoofGeometry, costs: CostSpec) -> float:
    """The all-in rate on gross area, overhangs included."""
    return geom.surface_area * costs.eur_per_m2
