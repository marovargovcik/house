"""Parameter sweeps over the roof/attic model. Pure — builds rows, writes nothing.

The sweep exists to surface the trade-off `docs/spec.md` §3b names: a steeper
pitch buys usable attic area but costs roof surface, since area grows as
`1 / cos θ`. `eur_per_usable_m2` is where the two meet.

A row is a frozen dataclass rather than a DataFrame row. The table was only ever
a container — built from dicts and immediately unpacked back into dicts by the
interpreters — and a named type is what this project reaches for anyway. It also
leaves the whole Module 1 pipeline on the standard library, which is what makes
it portable to a browser runtime.
"""

from collections.abc import Sequence
from dataclasses import dataclass, fields

from house.core import attic as attic_calc
from house.core import roof as roof_calc
from house.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec


@dataclass(frozen=True, slots=True)
class SweepRow:
    """One (width, pitch) combination. Field order is the report's column order."""

    width_m: float
    pitch_deg: float
    roof_area_m2: float
    ridge_above_wall_top_m: float
    clear_ridge_m: float
    usable_width_m: float
    usable_area_m2: float
    usable_fraction: float
    total_eur: float
    eur_per_usable_m2: float


def column_names() -> tuple[str, ...]:
    """Field order, for renderers that lay the rows out as a table."""
    return tuple(field.name for field in fields(SweepRow))


def width_by_pitch(
    widths: Sequence[float],
    pitches_deg: Sequence[float],
    length: float,
    attic: AtticSpec,
    costs: CostSpec,
    overhang_eave: float,
    overhang_gable: float,
) -> tuple[SweepRow, ...]:
    """One row per (width, pitch) combination.

    `eur_per_usable_m2` is NaN where the pitch is too shallow to yield any
    habitable area — dividing by zero usable area would invent a number, and NaN
    keeps those rows visible in the table rather than silently ranking them best.
    """
    return tuple(
        _row(
            HouseSpec(width=width, length=length),
            RoofSpec(
                pitch_deg=pitch_deg,
                overhang_eave=overhang_eave,
                overhang_gable=overhang_gable,
            ),
            attic,
            costs,
        )
        for width in widths
        for pitch_deg in pitches_deg
    )


def _row(
    house: HouseSpec, roof: RoofSpec, attic: AtticSpec, costs: CostSpec
) -> SweepRow:
    geom = roof_calc.geometry(house, roof)
    cost = roof_calc.cost(geom, costs)
    usable = attic_calc.estimate(house, roof, attic)
    return SweepRow(
        width_m=house.width,
        pitch_deg=roof.pitch_deg,
        roof_area_m2=geom.surface_area,
        # The knee wall (nadmurovka) sits on the wall top and the roof springs
        # from it, so it raises the ridge one-for-one. `roof.ridge_height` is the
        # slope rise alone, which is why the knee is added here rather than
        # hidden in the geometry.
        ridge_above_wall_top_m=geom.ridge_height + attic.knee_height,
        # What is left of that ridge after the roof and floor build-ups. The
        # structural figure is what a height limit measures; this is what you
        # stand under.
        clear_ridge_m=usable.clear_ridge_height,
        usable_width_m=usable.usable_width,
        usable_area_m2=usable.usable_area,
        usable_fraction=usable.usable_area / (house.width * house.length),
        total_eur=cost,
        eur_per_usable_m2=(
            cost / usable.usable_area if usable.usable_area > 0 else float("nan")
        ),
    )
