"""`house.web` — composition, not new arithmetic.

Every number it returns is already pinned by `test_sweep`, `test_csv` and
`test_to_html`; what is untested elsewhere is the wiring. So this checks the two
things only this module decides: that a good run returns exactly what the
interpreters produce, and that a refused run returns the reason and *nothing
else* — from both halves of the validation rule.

Pyodide is not exercised here. It is CPython 3.14, the same interpreter these
tests run on, which is the whole reason the browser build needs no shims.
"""

import json

from house import web
from house.core import sweep
from house.core.specs import AtticSpec, CostSpec
from house.interpreters import to_csv, to_text

INPUTS = {
    "widths": [9.0, 10.0],
    "pitches_deg": [30.0, 45.0],
    "length": 25.0,
    "overhang_eave": 0.6,
    "overhang_gable": 0.4,
    "h_min": 1.9,
    "roof_buildup": 0.30,
    "floor_buildup": 0.20,
    "knee_height": 0.0,
    "collar_above_wall_top": None,
    "eur_per_m2": 110.0,
}


def test_renders_exactly_what_the_interpreters_produce() -> None:
    result = json.loads(web.report(json.dumps(INPUTS)))

    attic = AtticSpec(
        h_min=1.9,
        roof_buildup=0.30,
        floor_buildup=0.20,
        knee_height=0.0,
        collar_above_wall_top=None,
    )
    rows = sweep.width_by_pitch(
        widths=[9.0, 10.0],
        pitches_deg=[30.0, 45.0],
        length=25.0,
        attic=attic,
        costs=CostSpec(eur_per_m2=110.0),
        overhang_eave=0.6,
        overhang_gable=0.4,
    )
    assert result["problems"] == []
    assert result["table"] == to_text.render_table(rows)
    assert result["csv"] == to_csv.render_csv(rows)
    assert result["html"].startswith("<!doctype html>")


def test_zero_and_blank_both_mean_no_collar_tie() -> None:
    """The web accepts `0` for absence exactly as `--collar 0` does.

    The CLI has no choice about the convention — a required flag cannot also be
    omitted — but a form can express absence as an empty field. It accepts both
    so that a number that works on the command line is not an error in the
    browser; `core.specs.collar_from_input` is the single place that decides.
    """
    blank = json.loads(web.report(json.dumps(INPUTS | {"collar_above_wall_top": None})))
    zero = json.loads(web.report(json.dumps(INPUTS | {"collar_above_wall_top": 0})))

    assert blank["problems"] == []
    assert zero == blank


def test_a_spec_that_raises_is_reported_and_nothing_is_computed() -> None:
    result = json.loads(web.report(json.dumps(INPUTS | {"h_min": -1.0})))

    assert "h_min must be positive" in result["problems"][0]
    assert (result["table"], result["csv"], result["html"]) == ("", "", "")


def test_a_cross_spec_problem_is_reported_the_same_way() -> None:
    """The half no single spec can see — a collar that only a pitch rules out.

    3.0 m clears the knee wall, so `AtticSpec` accepts it; it is the 30° roof at
    9 m that has no ceiling left up there, and only `validate` can see that.
    """
    result = json.loads(
        web.report(
            json.dumps(INPUTS | {"knee_height": 0.5, "collar_above_wall_top": 3.0})
        )
    )

    assert "does not fit the roof" in result["problems"][0]
    assert (result["table"], result["csv"], result["html"]) == ("", "", "")
