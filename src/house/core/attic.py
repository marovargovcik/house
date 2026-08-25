"""Usable attic area under a gable roof. Pure — see `docs/spec.md` §3b.

Under a gable with no knee wall the ceiling slopes from full ridge height down
to zero at the eaves, so usable floor is whatever strip still clears `h_min`.
"""

import math
from dataclasses import dataclass

from house.core.specs import AtticSpec, HouseSpec, RoofSpec


@dataclass(frozen=True, slots=True)
class AtticResult:
    usable_width: float
    usable_area: float


def usable_width(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> float:
    """Width of the strip clearing `h_min`, measured across the house.

    The outer clamp also covers the "ridge lower than `h_min`" case: a ridge too
    low to stand under is algebraically the same as the strip going negative, so
    one clamp handles both and no separate ridge-height branch is needed.
    """
    lost_per_side = max(
        0.0,
        (attic.h_min - attic.knee_height) / math.tan(math.radians(roof.pitch_deg)),
    )
    return max(0.0, house.width - 2 * lost_per_side)


def estimate(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> AtticResult:
    width = usable_width(house, roof, attic)
    return AtticResult(usable_width=width, usable_area=width * house.length)
