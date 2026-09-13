"""Gable roof geometry and ballpark cost. Pure — see `docs/spec.md` §3a."""

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
    """Total roof surface, both planes.

    The eave overhang joins the `width` factor because it continues the slope and
    so is stretched by `1 / cos θ`; the gable overhang joins the `length` factor
    because it runs horizontally along the ridge. Wiring the two the other way
    round still produces a plausible-looking number — see `docs/decisions.md`.
    """
    return (
        (house.length + 2 * roof.overhang_gable)
        * (house.width + 2 * roof.overhang_eave)
        / math.cos(math.radians(roof.pitch_deg))
    )


def gutter_run(house: HouseSpec, roof: RoofSpec) -> float:
    """Gutter (odkvapový žľab) length along both eaves.

    A horizontal line at the eave, so unlike the roof surface it does not grow
    with pitch. Reported for ordering, not for costing — gutters are inside the
    all-in rate. Downpipes (zvody) are not modelled: they need an eave height,
    which is outside this module.
    """
    return 2 * (house.length + 2 * roof.overhang_gable)


def geometry(house: HouseSpec, roof: RoofSpec) -> RoofGeometry:
    return RoofGeometry(
        surface_area=surface_area(house, roof),
        ridge_height=ridge_height(house, roof),
        rafter_length=rafter_length(house, roof),
        gutter_run=gutter_run(house, roof),
    )


def cost(geom: RoofGeometry, costs: CostSpec) -> float:
    """Ballpark cost of the roof: one all-in rate on gross surface area.

    Gross means the overhang is charged too — a deliberate over-estimate in the
    budgeting-safe direction (`docs/decisions.md`). Gutters live inside the rate,
    so `gutter_run` is geometry for ordering material now, like `rafter_length`,
    and no longer a cost input.
    """
    return geom.surface_area * costs.eur_per_m2
