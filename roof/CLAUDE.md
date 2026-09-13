# roof

Roof material cost and usable attic area for the house, swept across width and
pitch. The repo-wide rules — principles, architecture invariants, Python
conventions, testing, commits — are in the [root `CLAUDE.md`](../CLAUDE.md); this
file holds only what is specific to `roof/`.

Full formulas and rationale live in [`docs/spec.md`](./docs/spec.md).
**Read it before touching `roof.py` or `attic.py`.** Settled decisions are in
[`docs/decisions.md`](./docs/decisions.md).

## Commands

Run from `roof/`, or add `--directory roof` to `uv run` from the repo root.

| Task | Command |
|------|---------|
| Setup (fresh clone) | `uv sync && npm --prefix web install` |
| Run | `uv run cli` — every input is a required flag; README.md has the current design's invocation |
| Run in a browser | `uv run web` — serves `roof/` and opens the page; needs `npm --prefix web install` |
| Tests | `uv run pytest` — one module: `uv run pytest tests/test_roof.py` |
| Format | `uv run ruff format .` |
| Lint | `uv run ruff check --fix .` |
| Types | `uv run mypy .` |
| Browser page gates | `npm --prefix web run check` — oxlint, oxfmt, tsc |
| Format the browser page | `npm --prefix web run format` — HTML, CSS, JS in one |
| All gates, as pre-commit runs them | `./check` |

## No runtime dependencies

`roof` is `math` and `dataclasses` end to end.

> [!NOTE]
> The empty `dependencies` list is deliberate, not an oversight. It is what lets
> the whole pipeline run on a bare CPython — including the Pyodide browser page —
> so don't reach for a third-party package where the standard library will do.

## Project structure

> [!NOTE]
> Target layout — create modules as the work reaches them; a missing file here is
> not a bug to report.

```text
src/roof/
  core/            # pure modules, depend only on specs
    specs.py       # frozen dataclasses: HouseSpec, RoofSpec, AtticSpec, CostSpec
    roof.py        # roof surface area, material/timber cost
    attic.py       # usable upstairs area vs. pitch/width
    sweep.py       # width x pitch rows
    views.py       # section/plan coordinates for drawings — numbers, not pixels
    validate.py    # cross-spec checks — the ones no single spec can make
  interpreters/    # consume core output; IO lives here
    to_json.py
    to_csv.py      # sweep rows -> CSV
    to_text.py     # sweep rows -> fixed-width table for a terminal
    to_svg.py      # views -> SVG (string building, no IO)
    to_html.py     # sweep + drawings -> one self-contained page
    sk.py          # Slovak number formatting for the report
  cli.py           # entry point: flags -> core -> stdout and files
  web.py           # entry point: JSON -> core -> strings. Pure; the browser's.
web/
  index.html       # the browser UI's markup; fetches src/ live, no build step
  style.css        # its styling (the report brings its own)
  scripts/
    app.js         # entry point: boot, then let the form drive it
    dom.js         # the page's elements, looked up once and class-checked
    form.js        # reading the form into a payload, and refusing a bad one
    view.js        # display state; the only thing that writes to the panes
    runtime.js     # Pyodide, and the module list it copies into it
  package.json     # pyodide itself, plus oxlint, oxfmt, typescript
tests/             # hand-checked cases pinning every output; mirrors src/roof/
docs/
  spec.md          # formulas, terminology, rationale, caveats
  decisions.md     # dated record of settled decisions — don't re-litigate these
check              # every gate; the root pre-commit hook runs it
```

The build is a `src/` layout (`uv_build`), so imports are absolute from the
package root: `from roof.core.roof import surface_area`.

## Editor: the browser page

On save, the `oxc.oxc-vscode` extension formats HTML, CSS, JS/TS and JSON with
`oxfmt` and applies `source.fixAll.oxc`, auto-detecting the pinned binaries in
`web/node_modules`. Config discovery is nested, so `web/.oxfmtrc.json` and
`web/.oxlintrc.json` apply even though the workspace folder is `roof/`.
