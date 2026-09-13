"""The cross-spec checks (`core/validate.py`).

What they exist for: an input that every spec accepts on its own and that no
calculation refuses, but that describes a house nobody can build.
"""

import pytest

from house.core import validate
from house.core.specs import AtticSpec

WITH_COLLAR = AtticSpec(
    h_min=1.9,
    roof_buildup=0.30,
    floor_buildup=0.20,
    knee_height=0.0,
    collar_above_wall_top=2.4,
)


def _problems(attic: AtticSpec) -> tuple[str, ...]:
    """One 9 m house swept across four pitches — the fixture both cases share."""
    return validate.sweep_problems(
        widths=(9.0,),
        pitches_deg=(25.0, 30.0, 35.0, 45.0),
        length=25.0,
        attic=attic,
        overhang_eave=0.6,
        overhang_gable=0.4,
    )


def test_a_collar_higher_than_the_roof_is_reported_with_its_combinations() -> None:
    """9 m wide, the finished ceiling peaks at 1.7674 m at 25° and 2.2517 m at
    30°, both below a 2.4 m collar — there is no rafter up there to tie. At 35°
    it peaks at 2.7847 m and at 45° at 4.0757 m, so those two are fine.

    The failing rows have to be named: without them the answer looks ordinary,
    because `views` just draws no collar and the sweep prices the attic anyway.
    """
    problems = _problems(WITH_COLLAR)

    assert len(problems) == 1
    assert "9 m / 25°, 9 m / 30°" in problems[0]
    assert "35°" not in problems[0]
    assert "45°" not in problems[0]


@pytest.mark.parametrize("collar", [1.5, None])
def test_a_collar_that_fits_every_swept_row_is_no_problem(collar: float | None) -> None:
    """1.5 m sits under the ceiling even at 25°, the shallowest pitch swept and
    so the lowest ceiling; `None` is a roof with no collar tie. Neither is an
    input error.

    1.5 m is also *too low to clear h_min* — 1.3 m under it, so no habitable
    attic at any pitch. That is an answer the report already states, and
    deliberately not a problem here.
    """
    attic = AtticSpec(
        h_min=1.9,
        roof_buildup=0.30,
        floor_buildup=0.20,
        knee_height=0.0,
        collar_above_wall_top=collar,
    )
    assert _problems(attic) == ()


def test_every_spec_the_sweep_will_build_is_built_here_first() -> None:
    """A field that is nonsense on its own must raise from validation, not from
    somewhere inside the sweep — that is what lets the sweep trust its inputs.

    Pinned with a bad width, since widths are swept: the offending `HouseSpec` is
    one the sweep would only reach part-way through its loop.
    """
    with pytest.raises(ValueError, match="footprint"):
        validate.sweep_problems(
            widths=(9.0, -11.0),
            pitches_deg=(30.0,),
            length=25.0,
            attic=WITH_COLLAR,
            overhang_eave=0.6,
            overhang_gable=0.4,
        )
