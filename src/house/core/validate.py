"""Cross-spec input checks. Pure — builds every spec the sweep will, and reports.

Each spec validates its own fields in `__post_init__`, which is where a value
that is nonsense on its own belongs. But a value can be perfectly sensible and
still be impossible *in combination*: 2.4 m above the wall top is a fine collar
tie, 25° on a 9 m house is a fine roof, and there is no such roof with such a
collar in it. Neither spec can see that, because neither can see the other.

Problems are **returned**, not raised. A single bad field makes the value itself
unusable, so the constructor refuses it; a bad *combination* is a fact about the
run, and the entry point is what decides that a run stops. Returning them also
keeps this testable by assertion rather than by exception.

Not checked here, deliberately: a pitch too shallow to stand under, and a collar
too low to clear `h_min`. Those are answers the model already reports — 0 usable
width, NaN per m², and the collar note on the page — not bad input.
"""

from collections.abc import Sequence

from house.core import attic as attic_calc
from house.core import roof as roof_calc
from house.core.specs import AtticSpec, HouseSpec, RoofSpec


def collar_fits(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> bool:
    """Whether the collar tie is low enough to be in this roof at all.

    It ties two opposing rafters, so it has to meet the finished ceiling on both
    sides — which means sitting below the ceiling's apex. Above it there is
    nothing to tie, and nothing catches that on its own: `views` quietly draws no
    collar and the sweep prices an attic that is supposed to have one.
    """
    if attic.collar_above_wall_top is None:
        return True
    ceiling_apex = (
        attic.knee_height
        + roof_calc.ridge_height(house, roof)
        - attic_calc.ceiling_drop(roof, attic)
    )
    return attic.collar_above_wall_top < ceiling_apex


def sweep_problems(
    widths: Sequence[float],
    pitches_deg: Sequence[float],
    length: float,
    attic: AtticSpec,
    overhang_eave: float,
    overhang_gable: float,
) -> tuple[str, ...]:
    """Everything wrong with these inputs that no single spec can see.

    Takes the sweep's own arguments so the entry point checks exactly what it is
    about to run, and constructs every spec the sweep will — so a field that is
    nonsense on its own raises from here, before anything is swept, and
    `sweep.width_by_pitch` can trust what it is handed.
    """
    combinations = [
        (
            HouseSpec(width=width, length=length),
            RoofSpec(
                pitch_deg=pitch_deg,
                overhang_eave=overhang_eave,
                overhang_gable=overhang_gable,
            ),
        )
        for width in widths
        for pitch_deg in pitches_deg
    ]
    collar = attic.collar_above_wall_top
    if collar is None:
        return ()

    misfits = [
        f"{house.width:g} m / {roof.pitch_deg:g}°"
        for house, roof in combinations
        if not collar_fits(house, roof, attic)
    ]
    if not misfits:
        return ()
    return (
        (
            f"collar tie {collar:g} m above the wall top does not fit the roof at "
            f"{', '.join(misfits)} — the finished ceiling peaks below it there, so "
            "there is nothing to tie. Lower the collar, or drop those widths and "
            "pitches from the sweep."
        ),
    )
