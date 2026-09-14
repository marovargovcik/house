# roof

Roof material cost and usable attic area for the house, swept across width and
pitch. The repo-wide rules — principles, architecture invariants, Python
conventions, testing, commits — are in the [root `CLAUDE.md`](../CLAUDE.md); this
file holds only what is specific to `roof/`.

**Read [The model](#the-model) before touching `roof.py` or `attic.py`.**

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

## The model

A plain gable roof over an "I"-shaped house. `w` width, `L` length, `θ` pitch,
`k` knee-wall height; everything in metres.

```text
ridge height       = (w/2)·tan θ                 # above the wall top; the sweep reports k + this
rafter length      = (w/2 + o_eave) / cos θ
roof area          = (L + 2·o_gable)·(w + 2·o_eave) / cos θ
cost               = roof area × all-in €/m²
ceiling drop       = roof_buildup / cos θ
usable width       = max(0, w − 2·max(0, (h_min + ceiling drop + floor_buildup − k) / tan θ))
usable area        = usable width × L
clear ridge height = k + ridge height − ceiling drop − floor_buildup   # capped at collar − floor_buildup
min collar height  = h_min + floor_buildup
```

**Settled — don't change these without being asked:**

- **Overhangs are horizontal projections.** `o_eave` continues the slope, so it
  sits inside the `/ cos θ` factor; `o_gable` runs along the ridge, so it goes on
  `L`. Swapped, they still give a plausible number — a test catches it.
- **One all-in €/m²** — krov, insulation, membrane, battens, covering, gutters,
  labour — charged on **gross** area, overhangs included. A deliberate
  over-estimate. No per-layer costing.
  Rafter length and gutter run are reported for ordering, not costed.
- **Headroom is clear height**, finished floor to finished ceiling.
  `roof_buildup` is perpendicular to the roof plane, hence `/ cos θ`; treating it
  as vertical would flatter every steep pitch.
- **A collar tie gates, it does not narrow.** If it clears `h_min` it costs
  nothing; if not, usable width is 0. Don't model it as a width reduction.
- **Not modelled:** ridge beam, purlins and their posts, dormers. The figures are
  the best a pitch can give.
- **Measured inputs have no defaults**, in the specs or the CLI: `h_min`, both
  overhangs, both build-ups, knee and collar. On the CLI `0` means no knee / no
  collar; `collar_from_input` maps a collar of 0 to `None`. Keep the knee
  parameter even though the design has none.
- **A bad input combination fails the whole run**, naming the (width, pitch)
  rows — never skip rows or warn. A pitch too shallow to stand under, or a collar
  too low, is a result (0 usable width), not a validation error.

## The report

- **Slovak throughout** — prose, labels, decimal comma, no-break space between
  thousands. The core stays English; only `interpreters/sk.py` and the label
  strings in the renderers translate.
- `core/views.py` builds the drawing's coordinates from the same functions as the
  table, so a drawing cannot disagree with its row.
- **One px-per-metre scale across every card**, never fit-to-box, so widths and
  pitches compare by eye.
- The hatched standing-room region's base is exactly `usable_width`. The `h_min`
  line is drawn even when it floats above the ridge.

## Slovak terms

Use these in anything for the projektant or the builders.

| English | Slovensky |
|---|---|
| gable roof | sedlová strecha |
| ridge | hrebeň |
| pitch | sklon strechy |
| rafters | krokvy |
| roof structure (load-bearing) | krov |
| collar tie | klieština |
| eave overhang | odkvapový presah |
| eaves / gutter | odkvap / odkvapová sústava |
| gable / end wall | štít / štítová stena |
| rake / gable overhang | štítový presah |
| knee wall | nadmurovka |
| habitable attic | (obytné) podkrovie |
| usable / habitable floor area | úžitková / obytná plocha |

## No runtime dependencies

`roof` is `math` and `dataclasses` end to end.

> [!NOTE]
> The empty `dependencies` list is deliberate, not an oversight. It is what lets
> the whole pipeline run on a bare CPython — including the Pyodide browser page —
> so don't reach for a third-party package where the standard library will do.

## Project structure

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
    ui.js          # the page's elements, looked up once and class-checked
    form.js        # reading the form into a payload, and refusing a bad one
    view.js        # display state; the only thing that writes to the panes
    runtime.js     # Pyodide, and the module list it copies into it
  package.json     # pyodide itself, plus oxlint, oxfmt, typescript
tests/             # hand-checked cases pinning every output; mirrors src/roof/
check              # every gate; the root pre-commit hook runs it
```

The build is a `src/` layout (`uv_build`), so imports are absolute from the
package root: `from roof.core.roof import surface_area`.

## The browser page

- **It runs `src/roof/` unmodified** in Pyodide, with no build step: the page
  fetches the modules from `src/` (with `no-store`), so edit and reload.
  `web.py` is its entry point. Serve `roof/`, not `web/` — the page fetches
  `../src/`.
- **Pyodide, not MicroPython.** MicroPython drops annotations, which breaks
  `@dataclass` and `NamedTuple`. Don't retry it for the smaller download.
- **Plain JS ES modules with JSDoc, checked by `tsc` under `strict`.** No `.ts`
  source or framework: either would put a compiler between the source and the
  page.
- **`tsc` also covers two gaps in oxlint:** a bad import path (`TS2307`) and a
  `@param` naming a missing parameter (`TS8024`).
- **Full-precision CSV can differ from the CLI's in the last digit** — the
  WebAssembly libm is one ulp off on `tan`. The table and report are identical.
  Don't round the CSV to hide it.

`web/.oxlintrc.json` turns on every category, then turns off these on purpose:

| Off | Why |
|---|---|
| `no-inline-comments` | JSDoc casts `/** @type {...} */ (value)` must be inline |
| `one-var` | every declaration here is its own |
| `sort-keys` | `Payload`'s field order mirrors the CLI flags |
| `sort-imports` | `oxfmt` sorts imports; two tools would fight |
| `no-ternary` | bans all ternaries; `no-nested-ternary` stays on |
| `unicorn/no-null` | `null` is the JSON form of Python's `None` |
| `unicorn/prefer-query-selector` | `getElementById` is deliberate, see `scripts/ui.js` |
| `unicorn/no-array-callback-reference` | contradicts `unicorn/prefer-native-coercion-functions` on `.map(Number)` |
| `import/no-named-export`, `import/prefer-default-export` | every module exports several names |

Tuned, not off: `no-magic-numbers` ignores `0`, `1`, `-1`; `max-statements` is 15.

**Editor:** on save, `oxc.oxc-vscode` formats HTML, CSS, JS/TS and JSON with
`oxfmt` and applies `source.fixAll.oxc`, using the binaries in
`web/node_modules`. Nested config discovery makes `web/.oxfmtrc.json` and
`web/.oxlintrc.json` apply from the `roof/` workspace folder. Markdown and TOML
are left out of format-on-save: `oxfmt` would reflow hand-wrapped prose and
rewrite `pyproject.toml`.
