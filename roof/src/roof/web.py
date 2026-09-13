"""The browser build: the sweep the page runs, and the server that hands it over.

Split the way every interpreter here is split — `render_html` / `write_html`,
`render_csv` / `write_csv` — with the pure half first and the effect at the very
edge:

- `report()` is **pure**: JSON in, rendered strings out, no IO. This is what runs
  *inside* the browser, where there is nowhere to write anyway, and it is
  testable on CPython exactly as the core is (`tests/test_web.py`).
- `main()` is the effect: `uv run web` serves the page and opens it. It never
  runs in the browser — Pyodide imports this module and calls `report`.

The counterpart to `roof.cli`, and deliberately the *only* Python the browser
build adds. Pyodide is CPython 3.14 — the same interpreter `uv run cli` uses — so
`src/roof/` is loaded verbatim, with no transform, no shims and no compatibility
layer. That is the whole reason this file is short.

Where it differs from `cli.py`:

- **No `argparse`.** The form is the parser.
- **Two spellings of "no collar tie".** An empty field arrives as `null`, and 0
  is accepted for the same thing, so a number that works on the command line is
  not an error here. `core.specs.collar_from_input` is where that rule lives.
"""

import json
import webbrowser
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from roof.core import sweep, validate
from roof.core.specs import AtticSpec, CostSpec, collar_from_input
from roof.interpreters import to_csv, to_html, to_text


def report(payload: str) -> str:
    """`{"widths": [...], ...}` as JSON -> `{problems, table, csv, html}` as JSON.

    `problems` non-empty means the run was **refused** and the three renderings
    are empty — nothing was computed, so there is nothing to show. Validation
    follows the same rule as `cli.py`: a spec raises because a field is unusable
    on its own, `validate` returns because a combination is only nonsense
    together, and this entry point is what decides a run stops.
    """
    args = json.loads(payload)
    try:
        attic = AtticSpec(
            h_min=args["h_min"],
            roof_buildup=args["roof_buildup"],
            floor_buildup=args["floor_buildup"],
            knee_height=args["knee_height"],
            collar_above_wall_top=collar_from_input(args["collar_above_wall_top"]),
        )
        costs = CostSpec(eur_per_m2=args["eur_per_m2"])
        shape = {
            "widths": args["widths"],
            "pitches_deg": args["pitches_deg"],
            "length": args["length"],
            "overhang_eave": args["overhang_eave"],
            "overhang_gable": args["overhang_gable"],
        }
        problems = validate.sweep_problems(attic=attic, **shape)
    except ValueError as invalid:
        return _refused([str(invalid)])

    if problems:
        return _refused(list(problems))

    rows = sweep.width_by_pitch(attic=attic, costs=costs, **shape)
    return json.dumps(
        {
            "problems": [],
            "table": to_text.render_table(rows),
            "csv": to_csv.render_csv(rows),
            "html": to_html.render_html(
                rows,
                length=args["length"],
                attic=attic,
                costs=costs,
                overhang_eave=args["overhang_eave"],
                overhang_gable=args["overhang_gable"],
            ),
        }
    )


def _refused(problems: list[str]) -> str:
    return json.dumps({"problems": problems, "table": "", "csv": "", "html": ""})


PORT = 8000
"""Fixed rather than picked: a stable URL survives a restart, and the one way it
can fail — something else already on 8000 — says so plainly."""


def main() -> None:
    """Serve the project root (`roof/`) at `/web/` and open it. `uv run web`.

    The **project root**, not `web/`: the page fetches `../src/` so that editing a
    core module and reloading is the whole loop, which means the served tree has
    to contain both. Serving `web/` alone 404s every module.

    Threaded because the page requests all fifteen modules at once, and a
    single-threaded handler answers them one connection at a time.
    """
    root = Path(__file__).resolve().parent.parent.parent
    url = f"http://127.0.0.1:{PORT}/web/"
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    with ThreadingHTTPServer(("127.0.0.1", PORT), handler) as server:
        # Flushed: stdout is block-buffered when redirected, and this line is
        # how you get in if the browser does not open on its own.
        print(f"serving {root} at {url}  (ctrl-c to stop)", flush=True)
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print()
