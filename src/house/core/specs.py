"""Frozen input types for the roof/attic model.

Validation lives here and nowhere else: these constructors are the system
boundary, so the pure functions downstream can trust what they are handed. In
particular `0 < pitch_deg < 90` is what keeps `tan` and `1 / cos` total for
every caller, so no calculation needs its own guard.
"""

import math
from dataclasses import dataclass


def _is_positive(value: float) -> bool:
    """Finite and above zero.

    The `isfinite` half is the point: NaN compares False against everything, so a
    bare `value <= 0` guard lets NaN through and it then poisons every downstream
    number with no hint of where it entered.
    """
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
    """Gable roof (sedlová strecha) geometry.

    Both overhangs are horizontal projections, and they are *not*
    interchangeable — see `docs/decisions.md`.
    """

    pitch_deg: float
    overhang_eave: float = 0.6
    overhang_gable: float = 0.4

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
    """Headroom rule bounding habitable attic area (obytné podkrovie).

    `h_min` deliberately has no default: the binding figure depends on the
    Slovak *obytná plocha* norm, still an open item in `docs/decisions.md`.
    Passing it explicitly keeps an unverified value from reaching a result.
    """

    h_min: float
    knee_height: float = 0.0

    def __post_init__(self) -> None:
        if not _is_positive(self.h_min):
            raise ValueError(f"h_min must be positive, got {self.h_min} m")
        if not _is_non_negative(self.knee_height):
            raise ValueError(
                f"knee wall height must be non-negative, got {self.knee_height} m"
            )


@dataclass(frozen=True, slots=True)
class CostSpec:
    """One all-in rate for the whole roof, in EUR per m² of roof surface.

    Covers everything the roof costs — krov, insulation, membrane, battens,
    covering, gutters, labour — because that is how a builder quotes a roof, and
    one number carries exactly the precision this model has. Charged on **gross**
    area including the overhang, a deliberate over-estimate in the
    budgeting-safe direction (`docs/decisions.md`).
    """

    eur_per_m2: float

    def __post_init__(self) -> None:
        # Positive, not merely non-negative: a zero rate prices the entire roof
        # at nothing and still prints a plausible-looking total.
        if not _is_positive(self.eur_per_m2):
            raise ValueError(f"roof rate must be positive, got {self.eur_per_m2}")
