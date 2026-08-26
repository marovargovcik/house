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

    Neither carries a default. They are measured quantities that change the roof
    area and the timber order, and a default would let one reach a result without
    anyone choosing it — the same rule `AtticSpec` follows.
    """

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
    """Headroom rule bounding habitable attic area (obytné podkrovie).

    `h_min` is **clear** height — finished floor to finished ceiling — so the
    build-ups that eat into it belong here as inputs rather than as a correction
    someone remembers to apply later. Measuring to bare structure on both faces
    is the mistake this type exists to make impossible.

    - `h_min` — no default by decision, see `docs/decisions.md`.
    - `roof_buildup` — thickness **perpendicular to the roof plane**: rafter
      (krokva) depth, insulation, service cavity, lining. Perpendicular because
      that is how rafters and insulation are specified; `attic.ceiling_drop`
      converts it to the vertical loss that headroom actually feels.
    - `floor_buildup` — **vertical** thickness of the attic floor above the wall
      top: structure, insulation, screed, covering.
    - `knee_height` — nadmurovka; the slopes spring from its top. 0 for none.
    - `collar_above_wall_top` — underside of the collar tie (klieština) above the
      wall top, or `None` for a roof with no collar. See `attic.usable_width`
      for why this gates rather than reduces.

    None of them defaults, `collar_above_wall_top` included: a roof with no collar
    tie has to say `None` rather than leave it unsaid. The type stays a union
    because absence is genuinely not a height — it is the entry point's job to
    translate, not this one's.
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
            # The rafters spring from the knee top, so a collar at or below it
            # has nothing to tie. Both fields live here, so this is a check the
            # spec can make itself; a collar higher than the *roof* needs the
            # width and pitch too, and lives in `core/validate.py`.
            if self.collar_above_wall_top <= self.knee_height:
                raise ValueError(
                    "collar must sit above the knee wall the rafters spring "
                    f"from, got collar {self.collar_above_wall_top} m, knee "
                    f"{self.knee_height} m"
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
