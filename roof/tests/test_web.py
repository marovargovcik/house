"""The browser entry point's wiring, and the page's links to the Python."""

import json
import re
from pathlib import Path

import pytest

from roof import web

ROOT = Path(__file__).resolve().parent.parent
from roof.core import sweep
from roof.core.specs import AtticSpec, CostSpec
from roof.interpreters import to_csv, to_text

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
    """Empty and 0 both mean no collar, as `--collar 0` does."""
    blank = json.loads(web.report(json.dumps(INPUTS | {"collar_above_wall_top": None})))
    zero = json.loads(web.report(json.dumps(INPUTS | {"collar_above_wall_top": 0})))

    assert blank["problems"] == []
    assert zero == blank


def test_a_spec_that_raises_is_reported_and_nothing_is_computed() -> None:
    result = json.loads(web.report(json.dumps(INPUTS | {"h_min": -1.0})))

    assert "h_min must be positive" in result["problems"][0]
    assert (result["table"], result["csv"], result["html"]) == ("", "", "")


def test_a_cross_spec_problem_is_reported_the_same_way() -> None:
    """3.0 m clears the knee wall, but the 9 m / 30° roof has no ceiling up there."""
    result = json.loads(
        web.report(
            json.dumps(INPUTS | {"knee_height": 0.5, "collar_above_wall_top": 3.0})
        )
    )

    assert "does not fit the roof" in result["problems"][0]
    assert (result["table"], result["csv"], result["html"]) == ("", "", "")


def test_the_page_lists_every_module_it_has_to_load() -> None:
    """`runtime.js` lists the modules to load; a missing one only fails in the
    browser. `cli.py` is left out on purpose."""
    source = (ROOT / "web" / "scripts" / "runtime.js").read_text()
    block = re.search(r"const MODULES = \[(.*?)\];", source, re.DOTALL)
    assert block is not None, (
        "web/scripts/runtime.js no longer declares MODULES as a literal"
    )
    listed = set(re.findall(r'"([^"]+)"', block.group(1)))

    package = ROOT / "src" / "roof"
    on_disk = {
        str(path.relative_to(ROOT / "src")) for path in package.rglob("*.py")
    } - {"roof/cli.py"}

    assert listed == on_disk, (
        f"web/scripts/runtime.js MODULES is out of step with src/roof/: "
        f"missing {sorted(on_disk - listed)}, stale {sorted(listed - on_disk)}"
    )


def test_the_import_map_points_at_a_file_that_exists() -> None:
    """A stale import map only fails in the browser. Skipped without node_modules."""
    web = ROOT / "web"
    if not (web / "node_modules").exists():
        pytest.skip("web/node_modules is absent — run `npm --prefix web install`")

    page = (web / "index.html").read_text()
    block = re.search(r'<script type="importmap">(.*?)</script>', page, re.DOTALL)
    assert block is not None, "web/index.html no longer carries an import map"
    imports = json.loads(block.group(1))["imports"]

    for specifier, target in imports.items():
        resolved = (web / target).resolve()
        assert resolved.is_file(), (
            f"import map sends {specifier!r} to {target!r}, which does not exist"
        )


def test_every_export_is_imported_somewhere() -> None:
    """No export under `web/` goes unused; `tsc` only catches unused imports."""
    scripts = sorted(
        path
        for path in (ROOT / "web").rglob("*.js")
        if "node_modules" not in path.parts
    )
    assert scripts, "no browser modules found"

    exported = {
        (path, name.strip())
        for path in scripts
        for block in re.findall(r"^export \{([^}]*)\};", path.read_text(), re.MULTILINE)
        for name in block.split(",")
        if name.strip()
    }
    # Otherwise a changed export style passes by finding nothing.
    assert exported, "no exports found — has the export style changed?"
    imported = set()
    for path in scripts:
        # Collapsed: oxfmt wraps long imports across lines.
        flat = " ".join(path.read_text().split())
        for pattern in (
            r'import \{([^}]*)\} from "([^"]+)"',
            r'@import \{([^}]*)\} from "([^"]+)"',
        ):
            for block, specifier in re.findall(pattern, flat):
                if not specifier.startswith("."):
                    continue
                target = (path.parent / specifier).resolve()
                imported |= {
                    (target, name.strip()) for name in block.split(",") if name.strip()
                }

    unused = sorted(
        f"{path.relative_to(ROOT).as_posix()}: {name}"
        for path, name in exported
        if (path.resolve(), name) not in imported
    )
    assert not unused, f"exported but never imported — drop the `export`: {unused}"
