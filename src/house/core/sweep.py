"""Parameter sweeps over the roof/attic model. Pure — builds a table, writes nothing.

The sweep exists to surface the trade-off `docs/spec.md` §3b names: a steeper
pitch buys usable attic area but costs roof surface, since area grows as
`1 / cos θ`. `eur_per_usable_m2` is where the two meet.
"""

from collections.abc import Sequence

import pandas as pd

from house.core import attic as attic_calc
from house.core import roof as roof_calc
from house.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec


def width_by_pitch(
    widths: Sequence[float],
    pitches_deg: Sequence[float],
    length: float,
    attic: AtticSpec,
    costs: CostSpec,
    overhang_eave: float,
    overhang_gable: float,
) -> pd.DataFrame:
    """One row per (width, pitch) combination.

    `eur_per_usable_m2` is NaN where the pitch is too shallow to yield any
    habitable area — dividing by zero usable area would invent a number, and NaN
    keeps those rows visible in the table rather than silently ranking them best.
    """
    rows: list[dict[str, float]] = []
    for width in widths:
        for pitch_deg in pitches_deg:
            house = HouseSpec(width=width, length=length)
            roof = RoofSpec(
                pitch_deg=pitch_deg,
                overhang_eave=overhang_eave,
                overhang_gable=overhang_gable,
            )
            geom = roof_calc.geometry(house, roof)
            cost = roof_calc.cost(geom, costs)
            usable = attic_calc.estimate(house, roof, attic)
            rows.append(
                {
                    "width_m": width,
                    "pitch_deg": pitch_deg,
                    "roof_area_m2": geom.surface_area,
                    "ridge_height_m": geom.ridge_height,
                    "usable_width_m": usable.usable_width,
                    "usable_area_m2": usable.usable_area,
                    "usable_fraction": usable.usable_area / (width * length),
                    "roofing_eur": cost.roofing,
                    "krov_eur": cost.krov,
                    "gutters_eur": cost.gutters,
                    "total_eur": cost.total,
                    "eur_per_usable_m2": (
                        cost.total / usable.usable_area
                        if usable.usable_area > 0
                        else float("nan")
                    ),
                }
            )
    return pd.DataFrame(rows)
