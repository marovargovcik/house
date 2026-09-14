"""Input combinations no single spec can see. Pure; returns problems, never raises.

Any problem stops the whole run and names its rows — never skip rows or warn. A
pitch too shallow to stand under, or a collar too low, is a result, not a problem.
"""

from collections.abc import Sequence

from roof.core import attic as attic_calc
from roof.core import roof as roof_calc
from roof.core.specs import AtticSpec, HouseSpec, RoofSpec


def collar_fits(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> bool:
    """Whether the collar sits below the finished ceiling's apex, with rafters to tie."""
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
    """Builds every spec the sweep will, so a bad field raises here, before the run."""
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
