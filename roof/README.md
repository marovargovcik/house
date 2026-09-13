# roof

A scoping tool for the roof of a self-build house on a sloped plot. It estimates:

- **roof** — surface area and material/timber cost against pitch and footprint
- **attic** — usable upstairs floor area against pitch and width

Excavation is its own project — see the [repo README](../README.md).

It is not an engineering-grade calculator. The goal is **trustworthy,
hand-verifiable numbers** you can sweep across design variables — every figure it
produces is pinned by a test against a hand-computed reference.

## Quick start

```bash
uv sync                                  # create the venv from uv.lock
npm --prefix web install                 # the browser page: Pyodide + its checks
```

Every command here runs from `roof/`. Everything runs through `uv run`; there is
no virtualenv to activate.

### Running a sweep

**Every input is required — there are no defaults.** A default would let a figure
reach a report without anyone looking at it, which is the one thing this tool
must not do. `uv run cli --help` lists them. The design as it currently stands:

```bash
uv run cli --html roof.html \
  --widths 9 10 11 --length 25 --pitches 25 30 35 40 45 \
  --overhang-eave 0.6 --overhang-gable 0.4 \
  --h-min 1.9 --roof-buildup 0.30 --floor-buildup 0.20 --knee 0 --collar 0 \
  --eur-per-m2 110
```

That prints the table and writes the drawn report. Drop `--html` for the table
alone; add a path as the first argument to also write CSV.

The reasoning behind each of those numbers lives in
[`docs/spec.md`](./docs/spec.md) and [`docs/decisions.md`](./docs/decisions.md).
`--h-min`, `--roof-buildup` and `--floor-buildup` are still open items there —
they move the usable-attic figures more than anything else in the list.

`--knee 0` and `--collar 0` say there is no nadmurovka and no klieština. Zero is
how a required flag says "none" — the report states which case it is, so a run
never leaves it ambiguous.

### What the report is

`--html` writes one self-contained page — every row of the sweep drawn as a
gable section and a plan, all at one shared scale so widths and pitches compare
by eye. Open it in a browser; print to PDF from there if you need paper. It is
in Slovak, being what goes to the projektant.

Changing one input is a command line rather than an edit:

```bash
--knee 0.5                             # what a nadmurovka buys
--collar 2.4                           # with a collar tie
--roof-buildup 0.24 --floor-buildup 0.15   # a leaner build-up
```

### In a browser

The same sweep as a web page — a form for every flag above, the drawn report, the
table, and a CSV download. Useful for trying a width or a pitch without a
terminal.

```bash
uv run web
```

That serves `roof/` on port 8000 and opens the page. `roof/`, not
`web/`: the page fetches `../src/`, so both have to be under what is served —
which is also why any other static server (`python3 -m http.server 8000`,
`npx serve .`) has to be started from here, not from `web/`. Source is fetched
with `no-store`, so an edit shows up on reload whatever the server caches.

It runs **`src/roof/` itself**, unmodified, on CPython 3.14 compiled to
WebAssembly ([Pyodide](https://pyodide.org)), served from `web/node_modules` —
so it needs `npm --prefix web install` first, and then no network at all.
There is no build step and nothing generated: the page fetches the modules from
`src/` as you serve them, so editing a core module and reloading is the whole
loop. `src/roof/web.py` is the entry point it calls — the pure counterpart to
`cli.py`.

> [!NOTE]
> Full-precision CSV values can differ from the CLI's in the last digit or two
> (~3e-15 relative): WebAssembly's libm and your machine's disagree by one ulp on
> `tan(radians(30))`. The table and the report are byte-identical — they round
> long before that. See `docs/decisions.md`.

## Development

```bash
uv run pytest                # tests
uv run ruff format .         # format
uv run ruff check --fix .    # lint + import sort
uv run mypy .                # types
npm --prefix web run check   # the browser page: lint, format check, types
npm --prefix web run format  # format web/ (JS, HTML, CSS, JSON)
./check                      # all gates, exactly as the commit hook runs them
```

The browser page has the same three gates the Python does, one tool each:

| | Python | `web/` |
|---|---|---|
| Lint | `ruff check` | `oxlint` |
| Format | `ruff format` | `oxfmt` — HTML, CSS, JS/TS and JSON alike |
| Types | `mypy` (strict) | `tsc` (strict) |

The files under `web/` are plain JavaScript ES modules the browser loads
unmodified — nothing is compiled or bundled. They carry JSDoc annotations and are
checked by the real `tsc` under `strict`, which is what `.ts` files would get. Svelte, or `.ts` source, would
each put a compiler between you and the page, which is the one thing this page
does not have.

`oxfmt` formats `index.html` and `style.css` as well as the JavaScript, so there
is no separate HTML or CSS tool. It also sorts imports, which is why oxlint's
`sort-imports` is off: the formatter owns ordering, the same way it owns line
length on the Python side.

`oxlint` runs **all four categories** — `correctness`, `suspicious`, `pedantic`
and `style` — with the `unicorn`, `typescript`, `oxc`, `import` and `jsdoc`
plugins on. Being opinionated is the point; `web/.oxlintrc.json` then turns off a
short list of rules, and each one is off for a stated reason rather than because
it was noisy:

| Off | Why |
|---|---|
| `no-inline-comments` | it fires on `/** @type {...} */ (value)` casts, which *must* be inline — that is the cast syntax |
| `one-var` | it wants one combined `const` per scope; every declaration here is its own |
| `sort-keys` | `Payload`'s field order mirrors the CLI flags in `README.md`; alphabetising it would hide that |
| `sort-imports` | `oxfmt` sorts imports, and two tools fighting over order is worse than either |
| `no-ternary` | bans *all* ternaries, not just nested ones — `no-nested-ternary` stays on |
| `unicorn/no-null` | `null` is the JSON boundary with Python's `None`; `undefined` has no JSON form |
| `unicorn/prefer-query-selector` | `getElementById` is deliberate, see `scripts/ui.js` |
| `unicorn/no-array-callback-reference` | it and `unicorn/prefer-native-coercion-functions` directly contradict each other on `.map(Number)` |
| `import/no-named-export`, `import/prefer-default-export` | they want one default export per module; every module here exports several by name |

Two rules are **tuned rather than disabled**: `no-magic-numbers` ignores
`0`, `1` and `-1`, and `max-statements` allows 15.

> [!NOTE]
> `oxlint` implements neither `import/no-unresolved` nor `jsdoc/check-param-names`,
> so it will not catch a bad import path or a `@param` naming a parameter that
> does not exist. `tsc` catches both (`TS2307` and `TS8024`), which is why the
> `check` script runs it too.

Formatting and lint autofix run on save in VS Code for both halves of the
repo — Python through `charliermarsh.ruff`, and HTML/CSS/JS/TS/JSON through
`oxc.oxc-vscode`. `.vscode/extensions.json` prompts to install both;
`.vscode/settings.json` handles the rest.

Neither extension uses its own bundled binary: ruff is pinned by
`ruff.importStrategy: fromEnvironment`, and the Oxc extension auto-detects
`web/node_modules`. So the editor runs the same versions the commit hook does and
the two cannot drift. Markdown and TOML are deliberately left out of format-on-
save — `oxfmt` handles both, but it would reflow the hand-wrapped prose in this
file and rewrite `pyproject.toml`, and no gate checks either.

## Documentation

- [`docs/spec.md`](./docs/spec.md) — formulas, terminology, caveats
- [`docs/decisions.md`](./docs/decisions.md) — dated record of settled decisions
- [`CLAUDE.md`](./CLAUDE.md) — commands and structure; the repo's
  [`CLAUDE.md`](../CLAUDE.md) has the architecture invariants and conventions
- [`REVIEW.md`](../REVIEW.md) — code review guidelines
