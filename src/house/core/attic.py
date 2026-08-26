"""Usable attic area under a gable roof. Pure — see `docs/spec.md` §3b.

Headroom is measured **clear**: finished floor to finished ceiling. Three things
stand between the bare structure and that clear height, and they behave
differently, which is why they are modelled separately:

- the roof build-up (rafters, insulation, lining) lowers the ceiling,
- the floor build-up raises the floor,
- a collar tie (klieština) caps the height everywhere at once.

Measuring to the rafter line from the wall top — as this module first did —
over-states the usable strip by roughly the sum of the first two, magnified by
`1 / cos θ`.
"""

import math
from dataclasses import dataclass

from house.core import roof as roof_calc
from house.core.specs import AtticSpec, HouseSpec, RoofSpec


@dataclass(frozen=True, slots=True)
class AtticResult:
    usable_width: float
    usable_area: float
    clear_ridge_height: float


def ceiling_drop(roof: RoofSpec, attic: AtticSpec) -> float:
    """Vertical height the roof build-up costs.

    `roof_buildup` is perpendicular to the roof plane, but headroom is vertical,
    and two parallel planes a perpendicular distance `t` apart stand `t / cos θ`
    apart vertically. So the same rafters and insulation cost more headroom on a
    steeper roof — 0.30 m becomes 0.33 m at 25° and 0.42 m at 45°. Taking the
    build-up as a vertical figure instead would quietly under-state every steep
    pitch, which is the direction that flatters the result.
    """
    return attic.roof_buildup / math.cos(math.radians(roof.pitch_deg))


def clear_ridge_height(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> float:
    """Headroom at the ridge — the best the attic ever gets.

    A ridge beam, where the design has one, eats into this further; it is not
    modelled (`docs/spec.md` §3b caveats).
    """
    return (
        attic.knee_height
        + roof_calc.ridge_height(house, roof)
        - ceiling_drop(roof, attic)
        - attic.floor_buildup
    )


def min_collar_height(attic: AtticSpec) -> float:
    """Lowest a collar tie can sit above the wall top and still leave `h_min`.

    Independent of width and pitch — it is the floor build-up plus the headroom
    itself — so it is one figure for a whole sweep, and the number to hand the
    projektant when the krov is designed.
    """
    return attic.h_min + attic.floor_buildup


def collar_blocks(attic: AtticSpec) -> bool:
    """Whether a collar tie rules the attic out entirely.

    A collar gates rather than narrows. Under it the clear height is the
    collar's; outboard of it the ceiling has already fallen below the collar. So
    if the collar itself does not clear `h_min` then nothing in the attic does,
    and if it does clear it, it takes nothing off the strip the roof plane
    already allows.

    Treating the collar plane as a ceiling is deliberately conservative: you can
    put your head between two collars, but not while walking, and the collar zone
    is usually boarded out anyway.
    """
    return (
        attic.collar_above_wall_top is not None
        and attic.collar_above_wall_top - attic.floor_buildup < attic.h_min
    )


def usable_width(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> float:
    """Width of the strip clearing `h_min`, measured across the house.

    The outer clamp also covers the "ridge too low to stand under" case: it is
    algebraically the same as the strip going negative, so one clamp handles both
    and no separate ridge-height branch is needed.
    """
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
