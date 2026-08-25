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
uv run house
```

Everything runs through `uv run`; there is no virtualenv to activate.

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
