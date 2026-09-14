# Project Guidelines

## What this repo is

Tools for a self-build house on a sloped plot near Trenčín. Not
engineering-grade: the goal is **hand-verifiable numbers**.

| Project | What it is |
|---|---|
| [`roof/`](./roof) | Roof cost and usable attic area across pitches. Python, plus a Pyodide browser page |

**Read a project's own `CLAUDE.md` before working in it.** The survey is in
[`data/README.md`](./data/README.md).

## Layout

```text
CLAUDE.md  README.md  REVIEW.md  house.code-workspace
.githooks/pre-commit   # runs <project>/check for every project a commit touches
data/                  # the survey — read-only
roof/                  # one project = one folder
```

- **A project is self-contained:** own `pyproject.toml`, `uv.lock`,
  `.python-version`, `.venv`, `check`, `CLAUDE.md`, `README.md` and `.vscode/`.
  No Python config at the root.
- **Every project has an executable `check`** running all its gates.

## Commands

| Task | Command |
|------|---------|
| Setup (fresh clone) | `git config core.hooksPath .githooks`, then the project's setup |
| A project's command from the root | `uv run --directory roof pytest` |
| Gates for the projects a commit touches | `.githooks/pre-commit` |
| Gates for every project | `.githooks/pre-commit --all` |

> [!WARNING]
> The hook config is **per clone**. Without it the hook never runs.

## Principles

> Adapted from [Andrej Karpathy's CLAUDE.md](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md).

- **Think first.** State assumptions; lay out interpretations of an ambiguous
  request; push back on over-scoped ones; stop and ask when confused.
- **Simplicity.** Only what's asked. No speculative features, premature
  abstractions, flags or shims. Handle only errors that can happen. If 200 lines
  could be 50, rewrite.
- **Surgical changes.** Don't touch adjacent code, formatting or comments; match
  existing conventions; flag dead code instead of deleting it; remove only the
  orphans your change made.
- **Goal-driven.** Turn a request into checkable criteria; plan multi-step work
  with checkpoints; for a bug, write the failing test first.

## Architecture invariants

Python won't enforce these, so uphold them by discipline.

- **`core/` is pure:** no IO, no print, no global state, no argument mutation.
- **IO and rendering live in `interpreters/` and entry points.** `core/` never
  imports them.
- **Interpreters split building from writing:** `render_html` builds the string,
  `write_html` puts it on disk.
- **Validation is layered.** A bad field: the spec's `__post_init__` raises. A bad
  combination: `core/validate.py` returns problems and the entry point stops the
  run. Past that, trust inputs — no defensive clamps downstream.
- **Calculations are named functions**, never inside render or UI code. Drawing
  coordinates are numbers too: they live in `core/views.py`, pinned by tests.
- **Every numeric output has a hand-checked test** — e.g. 45° roof → footprint ×
  √2.

## Python style

- **Pure functions first**; effects at the edges.
- **Frozen dataclasses** (`slots=True` where free). Never mutate arguments.
- **Effectful collaborators are passed in**, typed as a `typing.Protocol` — no
  globals or singletons.
- **Model the domain with types:** dataclasses or `NamedTuple` for records,
  `Enum` or a union of dataclasses with `match` for alternatives. No positional
  tuples.
- **Errors:** no IO-error handling in the core; an expected failure goes in the
  return type; raise only at boundaries.
- **Comprehensions over mutation** where readable. Obvious beats clever.
- **Function size:** watch for mixed abstraction levels and functions that are
  hard to name.

## Python tooling

Python 3.14+, pinned per project. Add a runtime dependency only when a module
imports it; `roof` has none on purpose. All tool config goes in
`pyproject.toml`.

- **`uv`** — environment, dependencies, lockfile, running. Always `uv run …`,
  never activate a venv. Commit `uv.lock`; `uvx` for one-off tools.
- **`ruff`** — lint and format; must pass clean. Don't hand-format.
- **`mypy`** (`strict`) — the type gate; must pass clean. Type hints on every
  signature.
- **`pytest`** — tests.
- Imports at the top, absolute. Factories as `@classmethod` or next to their type.

**Pylance vs mypy.** Pylance runs in the editor at `basic` and is advisory;
**mypy wins**. Settle a disagreement with a real annotation
(`rows: list[dict[str, float]] = []`), never `# type: ignore` for a Pylance-only
complaint — use `# pyright: ignore` if you must. Don't raise Pylance to `strict`.

**Enforcement.** On save, ruff and mypy run from the project's own `.venv` — open
`house.code-workspace`. On commit, the hook runs `<project>/check` over the whole
project, so an unrelated dirty file blocks it; bypass with
`git commit --no-verify`.

## Units and vocabulary

- **Metres, degrees, EUR.** Convert at boundaries only.
- **Slovak terms** are in [`roof/CLAUDE.md`](./roof/CLAUDE.md); use them in
  anything for the projektant or builders.

## Testing

- **Fewest tests that cover the important properties.** No duplicates, no
  low-value tests.
- A test breaks when the behaviour changes, and only then — don't test
  implementation details.
- **Pin every number to a hand-computed reference.**
- Hard-coded inputs. Tests in `tests/`, mirroring the package.

## General

- When code and docs disagree, the code is right — fix the doc.
- `gsed`, not `sed`. Avoid `git -C` and `gh --repo`.
- Check the tests for usage examples.

## Comments

- Only where the code can't speak for itself. Explain *why*, in a line or two.
- No history ("first did", "no longer") — git has it.
- **A deliberate imprecision is not a bug.** Check the settled decisions in the
  project's `CLAUDE.md` before "fixing" one.

## Talking to me

Short. Verbosity is a bug, not thoroughness.

- **Answer in a few sentences.** No preamble, no restating my question, no summary
  of what you just did. Bullets over paragraphs.
- **Plain words.** Drop "comprehensive", "robust", "seamless", "leverage". Don't
  sell the work — say what's done, what isn't, what broke.
- **Explain on request, not by default.** Offer ("want the detail?") instead of
  pre-emptively writing three paragraphs.
- **Skip the mechanism tour.** Answer the question that was asked.

## Commits

- **One-line imperative subject**; a body only when the why needs it.
- **Prefix with the project** when the commit stays inside one:
  `roof: Cap the clear ridge height at the collar tie`.
- Small, focused commits. PR descriptions: a few lines, no file walkthrough.

## Documentation

- **`README.md`** — what it does today, for people, in plain words. No tech
  decisions, no plans; readable in a minute or two.
- **`CLAUDE.md`** — how and why, for the agent.
- No `docs/` folders. ATX headings, a language on every code block, `-` lists,
  GitHub callouts.

## Code review

See [`REVIEW.md`](./REVIEW.md). Priority: correctness → purity → clarity → style
→ performance.

If you notice the same correction or frustration coming up repeatedly, suggest
updating these instructions.
