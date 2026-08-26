# house

A scoping tool for a self-build house on a sloped plot. It estimates:

- **roof** — surface area and material/timber cost against pitch and footprint
- **attic** — usable upstairs floor area against pitch and width
- **excavation** — cut volume and maximum cut depth against pad height

It is not an engineering-grade calculator. The goal is **trustworthy,
hand-verifiable numbers** you can sweep across design variables — every figure it
produces is pinned by a test against a hand-computed reference.

## Quick start

```bash
uv sync                                  # create the venv from uv.lock
git config core.hooksPath .githooks      # enable the pre-commit gate (per clone)
```

Everything runs through `uv run`; there is no virtualenv to activate.

### Running a sweep

**Every input is required — there are no defaults.** A default would let a figure
reach a report without anyone looking at it, which is the one thing this tool
must not do. `uv run house --help` lists them. The design as it currently stands:

```bash
uv run house --html roof.html \
  --widths 9 10 11 --length 25 --pitches 25 30 35 40 45 \
  --overhang-eave 0.6 --overhang-gable 0.4 \
  --h-min 1.9 --roof-buildup 0.30 --floor-buildup 0.20 --knee 0 \
  --eur-per-m2 110
```

That prints the table and writes the drawn report. Drop `--html` for the table
alone; add a path as the first argument to also write CSV.

The reasoning behind each of those numbers lives in
[`docs/spec.md`](./docs/spec.md) and [`docs/decisions.md`](./docs/decisions.md).
`--h-min`, `--roof-buildup` and `--floor-buildup` are still open items there —
they move the usable-attic figures more than anything else in the list.

`--collar` is the one optional input: omit it for a roof with no collar tie
(klieština), since there is no height to state. Pass it and the report says
whether it clears.

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

## Development

```bash
uv run pytest                # tests
uv run ruff format .         # format
uv run ruff check --fix .    # lint + import sort
uv run mypy .                # types
.githooks/pre-commit         # all gates, exactly as the commit hook runs them
```

Formatting and lint autofix also run on save in VS Code — install the
`charliermarsh.ruff` extension and `.vscode/settings.json` handles the rest.

## Documentation

- [`docs/spec.md`](./docs/spec.md) — formulas, terrain data, coordinate frame, caveats
- [`docs/decisions.md`](./docs/decisions.md) — dated record of settled decisions
- [`CLAUDE.md`](./CLAUDE.md) — architecture invariants and working conventions
- [`REVIEW.md`](./REVIEW.md) — code review guidelines
