"""Browser entry point.

`report` is pure (JSON in, JSON out) and runs inside Pyodide. `main` serves the
page for `uv run web` and never runs in the browser.
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
    """`{"widths": [...], ...}` -> `{problems, table, csv, html}`, both as JSON.

    Non-empty `problems` means the run was refused and the rest is empty.
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


def main() -> None:
    """Serve `roof/` and open `/web/`.

    The project root, not `web/`, because the page fetches `../src/`. Threaded
    because the page fetches every module at once.
    """
    root = Path(__file__).resolve().parent.parent.parent
    url = f"http://127.0.0.1:{PORT}/web/"
    handler = partial(SimpleHTTPRequestHandler, directory=str(root))
    with ThreadingHTTPServer(("127.0.0.1", PORT), handler) as server:
        # Flushed so the URL shows even when stdout is redirected.
        print(f"serving {root} at {url}  (ctrl-c to stop)", flush=True)
        webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print()
