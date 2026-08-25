"""Frozen input types for the roof/attic model.

Validation lives here and nowhere else: these constructors are the system
boundary, so the pure functions downstream can trust what they are handed. In
particular `0 < pitch_deg < 90` is what keeps `tan` and `1 / cos` total for
every caller, so no calculation needs its own guard.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class HouseSpec:
    """Footprint of the "I"-shape house, in metres."""

    width: float
    length: float

    def __post_init__(self) -> None:
        if self.width <= 0 or self.length <= 0:
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
        if self.overhang_eave < 0 or self.overhang_gable < 0:
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
        if self.h_min <= 0:
            raise ValueError(f"h_min must be positive, got {self.h_min} m")
        if self.knee_height < 0:
            raise ValueError(
                f"knee wall height must be non-negative, got {self.knee_height} m"
            )


@dataclass(frozen=True, slots=True)
class RoofingLayer:
    """One priced layer of the roof build-up, in EUR per m² of roof surface."""

    name: str
    eur_per_m2: float

    def __post_init__(self) -> None:
        if self.eur_per_m2 < 0:
            raise ValueError(f"{self.name}: rate must be non-negative")


@dataclass(frozen=True, slots=True)
class CostSpec:
    """Ballpark rates, all configurable.

    When the real all-in builder's quote arrives it replaces `layers` with a
    single entry covering material and labour, and the rest of the model is
    unaffected.
    """

    layers: tuple[RoofingLayer, ...]
    krov_eur_per_m2: float
    gutter_eur_per_m: float

    def __post_init__(self) -> None:
        if self.krov_eur_per_m2 < 0 or self.gutter_eur_per_m < 0:
            raise ValueError("cost rates must be non-negative")

    @property
    def roofing_eur_per_m2(self) -> float:
        return sum(layer.eur_per_m2 for layer in self.layers)
