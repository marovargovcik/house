"""Width x pitch sweep. Pure.

A steeper pitch buys attic area but costs roof surface; `eur_per_usable_m2` is
where the two meet.
"""

from collections.abc import Sequence
from dataclasses import dataclass, fields

from roof.core import attic as attic_calc
from roof.core import roof as roof_calc
from roof.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec


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
    """One row per (width, pitch). `eur_per_usable_m2` is NaN with no usable area."""
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
        # `ridge_height` is the slope rise alone; the knee wall lifts it.
        ridge_above_wall_top_m=geom.ridge_height + attic.knee_height,
        clear_ridge_m=usable.clear_ridge_height,
        usable_width_m=usable.usable_width,
        usable_area_m2=usable.usable_area,
        usable_fraction=usable.usable_area / (house.width * house.length),
        total_eur=cost,
        eur_per_usable_m2=(
            cost / usable.usable_area if usable.usable_area > 0 else float("nan")
        ),
    )
