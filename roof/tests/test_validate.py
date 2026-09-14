"""Input combinations every spec accepts but nobody can build."""

import pytest

from roof.core import validate
from roof.core.specs import AtticSpec

WITH_COLLAR = AtticSpec(
    h_min=1.9,
    roof_buildup=0.30,
    floor_buildup=0.20,
    knee_height=0.0,
    collar_above_wall_top=2.4,
)


def _problems(attic: AtticSpec) -> tuple[str, ...]:
    """One 9 m house at four pitches."""
    return validate.sweep_problems(
        widths=(9.0,),
        pitches_deg=(25.0, 30.0, 35.0, 45.0),
        length=25.0,
        attic=attic,
        overhang_eave=0.6,
        overhang_gable=0.4,
    )


def test_a_collar_higher_than_the_roof_is_reported_with_its_combinations() -> None:
    """The ceiling peaks at 1.7674 m (25°) and 2.2517 m (30°), below a 2.4 m
    collar; at 35° (2.7847 m) and 45° (4.0757 m) it's fine. Failing rows are named."""
    problems = _problems(WITH_COLLAR)

    assert len(problems) == 1
    assert "9 m / 25°, 9 m / 30°" in problems[0]
    assert "35°" not in problems[0]
    assert "45°" not in problems[0]


@pytest.mark.parametrize("collar", [1.5, None])
def test_a_collar_that_fits_every_swept_row_is_no_problem(collar: float | None) -> None:
    """1.5 m fits under the ceiling even at 25°; `None` is no collar. 1.5 m is too
    low to clear h_min, but that's a result, not an input error."""
    attic = AtticSpec(
        h_min=1.9,
        roof_buildup=0.30,
        floor_buildup=0.20,
        knee_height=0.0,
        collar_above_wall_top=collar,
    )
    assert _problems(attic) == ()


def test_every_spec_the_sweep_will_build_is_built_here_first() -> None:
    """A bad second width raises from validation, before the sweep runs."""
    with pytest.raises(ValueError, match="footprint"):
        validate.sweep_problems(
            widths=(9.0, -11.0),
            pitches_deg=(30.0,),
            length=25.0,
            attic=WITH_COLLAR,
            overhang_eave=0.6,
            overhang_gable=0.4,
        )
