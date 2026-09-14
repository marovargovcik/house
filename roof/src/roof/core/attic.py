"""Usable attic area. Pure. Headroom is clear: finished floor to finished ceiling."""

import math
from dataclasses import dataclass

from roof.core import roof as roof_calc
from roof.core.specs import AtticSpec, HouseSpec, RoofSpec


@dataclass(frozen=True, slots=True)
class AtticResult:
    usable_width: float
    usable_area: float
    clear_ridge_height: float


def ceiling_drop(roof: RoofSpec, attic: AtticSpec) -> float:
    """Vertical headroom lost to `roof_buildup`, which is perpendicular: `t / cos θ`."""
    return attic.roof_buildup / math.cos(math.radians(roof.pitch_deg))


def clear_ridge_height(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> float:
    """Headroom at the ridge, capped by a collar tie. A ridge beam is not modelled."""
    under_ceiling = (
        attic.knee_height
        + roof_calc.ridge_height(house, roof)
        - ceiling_drop(roof, attic)
        - attic.floor_buildup
    )
    if attic.collar_above_wall_top is None:
        return under_ceiling
    return min(under_ceiling, attic.collar_above_wall_top - attic.floor_buildup)


def min_collar_height(attic: AtticSpec) -> float:
    """Lowest collar above the wall top that leaves `h_min`; same at every pitch."""
    return attic.h_min + attic.floor_buildup


def collar_blocks(attic: AtticSpec) -> bool:
    """Whether a collar is too low to leave `h_min` anywhere. Outboard of it the
    ceiling is lower still, so a collar blocks the attic or costs nothing."""
    return (
        attic.collar_above_wall_top is not None
        and attic.collar_above_wall_top - attic.floor_buildup < attic.h_min
    )


def usable_width(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> float:
    """Width of the strip clearing `h_min`. The outer clamp covers a ridge too low."""
    if collar_blocks(attic):
        return 0.0
    lost_per_side = max(
        0.0,
        (
            attic.h_min
            + ceiling_drop(roof, attic)
            + attic.floor_buildup
            - attic.knee_height
        )
        / math.tan(math.radians(roof.pitch_deg)),
    )
    return max(0.0, house.width - 2 * lost_per_side)


def estimate(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> AtticResult:
    width = usable_width(house, roof, attic)
    return AtticResult(
        usable_width=width,
        usable_area=width * house.length,
        clear_ridge_height=clear_ridge_height(house, roof, attic),
    )
