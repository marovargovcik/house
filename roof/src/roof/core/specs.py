"""Frozen input types. Their constructors reject bad fields, so downstream trusts
them — e.g. `0 < pitch_deg < 90` keeps `tan` and `1 / cos` safe everywhere.
"""

import math
from dataclasses import dataclass


def _is_positive(value: float) -> bool:
    """Finite and above zero. `isfinite` catches NaN, which `value <= 0` misses."""
    return math.isfinite(value) and value > 0


def _is_non_negative(value: float) -> bool:
    return math.isfinite(value) and value >= 0


@dataclass(frozen=True, slots=True)
class HouseSpec:
    """Footprint of the "I"-shape house, in metres."""

    width: float
    length: float

    def __post_init__(self) -> None:
        if not (_is_positive(self.width) and _is_positive(self.length)):
            raise ValueError(
                f"footprint must be positive, got {self.width} x {self.length} m"
            )


@dataclass(frozen=True, slots=True)
class RoofSpec:
    """Gable roof (sedlová strecha). Overhangs are horizontal projections, not
    interchangeable, and have no defaults."""

    pitch_deg: float
    overhang_eave: float
    overhang_gable: float

    def __post_init__(self) -> None:
        if not 0 < self.pitch_deg < 90:
            raise ValueError(
                f"pitch must be within (0, 90) degrees, got {self.pitch_deg}"
            )
        if not (
            _is_non_negative(self.overhang_eave)
            and _is_non_negative(self.overhang_gable)
        ):
            raise ValueError(
                f"overhangs must be non-negative, got eave {self.overhang_eave} m, "
                f"gable {self.overhang_gable} m"
            )


@dataclass(frozen=True, slots=True)
class AtticSpec:
    """Headroom rule for the habitable attic (obytné podkrovie). No defaults.

    - `h_min` — clear height, finished floor to finished ceiling.
    - `roof_buildup` — krokvy, insulation, lining; perpendicular to the roof plane.
    - `floor_buildup` — attic floor above the wall top; vertical.
    - `knee_height` — nadmurovka; 0 for none. Kept so a run shows what one buys.
    - `collar_above_wall_top` — klieština underside, or `None` for none.
    """

    h_min: float
    roof_buildup: float
    floor_buildup: float
    knee_height: float
    collar_above_wall_top: float | None

    def __post_init__(self) -> None:
        if not _is_positive(self.h_min):
            raise ValueError(f"h_min must be positive, got {self.h_min} m")
        if not (
            _is_non_negative(self.roof_buildup)
            and _is_non_negative(self.floor_buildup)
            and _is_non_negative(self.knee_height)
        ):
            raise ValueError(
                "build-ups and knee wall height must be non-negative, got roof "
                f"{self.roof_buildup} m, floor {self.floor_buildup} m, "
                f"knee {self.knee_height} m"
            )
        if self.collar_above_wall_top is not None:
            if not _is_positive(self.collar_above_wall_top):
                raise ValueError(
                    "collar must sit above the wall top, got "
                    f"{self.collar_above_wall_top} m"
                )
            # Rafters spring from the knee top, so a collar at or below it ties
            # nothing. A collar above the roof is `validate`'s check.
            if self.collar_above_wall_top <= self.knee_height:
                raise ValueError(
                    "collar must sit above the knee wall the rafters spring "
                    f"from, got collar {self.collar_above_wall_top} m, knee "
                    f"{self.knee_height} m"
                )


def collar_from_input(value: float | None) -> float | None:
    """0 or `None` means no collar tie. Shared by both entry points."""
    return None if value is None or value == 0 else value


@dataclass(frozen=True, slots=True)
class CostSpec:
    """All-in EUR per m² of roof surface, charged on gross area."""

    eur_per_m2: float

    def __post_init__(self) -> None:
        # A zero rate would still print a plausible-looking total.
        if not _is_positive(self.eur_per_m2):
            raise ValueError(f"roof rate must be positive, got {self.eur_per_m2}")
