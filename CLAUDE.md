# Project Guidelines

## What this project is

A scoping/decision-support tool that estimates roof material cost, usable attic
area, and excavation volume for a self-build house on a sloped plot. It is not an
engineering-grade calculator — the goal is **trustworthy, hand-verifiable numbers**
you can sweep across design variables.

Full formulas, terrain data, and rationale live in [`docs/spec.md`](./docs/spec.md).
**Read it before touching `roof.py`, `attic.py`, `terrain.py`, or `excavation.py`.**

---

## Commands

Everything runs through `uv run` — never activate the virtualenv manually.

| Task | Command |
|------|---------|
| Setup (fresh clone) | `uv sync && git config core.hooksPath .githooks` |
| Run | `uv run house` — every input is a required flag; README.md has the current design's invocation |
| Tests | `uv run pytest` — one module: `uv run pytest tests/test_roof.py` |
| Format | `uv run ruff format .` |
| Lint | `uv run ruff check --fix .` |
| Types | `uv run mypy .` |
| All gates, as pre-commit runs them | `.githooks/pre-commit` |

> [!WARNING]
> `git config core.hooksPath .githooks` is **per clone**. Without it the
> pre-commit hook silently never runs.

---

## Core Principles

> Adapted from [Andrej Karpathy's CLAUDE.md](https://github.com/forrestchang/andrej-karpathy-skills/blob/main/CLAUDE.md).
> These shape *how* you collaborate before any language-specific rule kicks in.

### Think Before Coding

- **State assumptions explicitly.** Name what you're assuming; ask if uncertain rather than guessing.
- **Surface multiple interpretations.** When a request is ambiguous, lay out the options instead of silently picking one.
- **Advocate for simplicity.** Push back on unclear or over-scoped requirements before writing code.
- **Stop when confused.** Don't code through confusion — identify what's unclear and resolve it first.

### Simplicity First

- **Implement only what's asked.** Skip speculative features beyond stated requirements.
- **Avoid premature abstraction.** No abstractions for single-use patterns; three similar lines beats a premature helper.
- **Skip unnecessary flexibility.** No configurability, feature flags, or backwards-compatibility shims unless explicitly requested.
- **Minimize error handling.** Skip handling for scenarios that can't occur. Trust internal code; only validate at system boundaries.
- **Ruthlessly trim excess code.** If 200 lines could be 50, rewrite.

### Surgical Changes

- **Preserve adjacent code.** Don't "improve" unrelated code, formatting, or comments while making your change.
- **Don't refactor stable code** unless explicitly asked.
- **Match existing codebase conventions** over personal preference.
- **Flag dead code separately** rather than deleting it unprompted.
- **Clean only your own orphans.** Remove imports/variables your change made unused; preserve pre-existing dead code.

### Goal-Driven Execution

- **Define verifiable success criteria.** Turn vague requests into testable goals with clear checks.
- **Plan multi-step tasks** with verification points before implementing.
- **Use tests to verify fixes.** When fixing a bug, write a test that reproduces it before implementing the fix.
- **Build independently with clear criteria.** Strong success metrics enable autonomous work without constant re-clarification.

---

## Architecture — the load-bearing invariants

These are the rules that this project's whole design depends on. They are not
enforced by the language (Python has no `F[_]` to make side effects visible in
types), so they must be upheld **by discipline** — which means they matter more
here, not less.

- **`core/` is pure.** Modules in `core/` contain only pure functions: same
  inputs → same outputs, no IO, no file/network/print, no global state, no
  mutation of arguments. This is what makes the numbers testable in isolation and
  trustworthy. A calculation that reaches for IO is a bug in the design.
- **IO and rendering live in `interpreters/` and entry points only.** JSON export,
  spreadsheet export, a future 3D viewer — these *consume* what the core produces.
  `core/` never imports an interpreter, a plotting library, or anything that does IO.
- **An interpreter splits building from writing.** `render_html` / `write_html`,
  `render_csv` / `write_csv`: the string is built by a pure function and one thin
  wrapper puts it on disk. A caller with nowhere to write — a test, a browser
  runtime — gets the output without the effect.
- **All terrain access goes through `Z_ground(x, y)`.** No module inlines terrain
  assumptions. The `y` parameter stays in the signature even while today's model
  ignores it — this is what makes swapping in survey-point terrain a body-only
  change. See `docs/spec.md`.
- **Calculations are named functions, never buried in render/UI callbacks.** So
  they can be unit-tested independently of any visualization. This extends to
  drawings: a drawing's *coordinates* are numbers, so they live in `core/views.py`
  and are pinned by tests; only the string building lives in an interpreter.
- **Every numeric output has a hand-checked `pytest` case that pins it.** A new
  calculation is not done until a test fixes its value against a hand-computed
  reference. Prefer a few high-value checks (flat plot → 0 excavation, 45° roof →
  footprint × √2) over many shallow ones.

## Project structure

> [!NOTE]
> Target layout. Only `src/house/__init__.py` exists today — create modules as
> the work reaches them; a missing file here is not a bug to report.

```text
src/house/
  core/            # pure modules, depend only on specs
    specs.py       # frozen dataclasses: HouseSpec, TerrainSpec, RoofSpec, ...
    roof.py        # roof surface area, material/timber cost
    attic.py       # usable upstairs area vs. pitch/width
    terrain.py     # Z_ground(x, y) — the terrain seam
    excavation.py  # excavation volume + max cut depth
    views.py       # section/plan coordinates for drawings — numbers, not pixels
  interpreters/    # consume core output; IO lives here
    to_json.py
    to_csv.py      # sweep rows -> CSV
    to_text.py     # sweep rows -> fixed-width table for a terminal
    to_svg.py      # views -> SVG (string building, no IO)
    to_html.py     # sweep + drawings -> one self-contained page
    sk.py          # Slovak number formatting for the report
    to_scene.py    # later — geometry → JSON for a JS/Three.js viewer
tests/             # hand-checked cases pinning every output; mirrors src/house/
docs/
  spec.md          # formulas, terrain data, rationale, caveats
  decisions.md     # dated record of settled decisions — don't re-litigate these
```

The build is a `src/` layout (`uv_build`), so imports are absolute from the
package root: `from house.core.roof import surface_area`.

---

## Functional style in Python

The FP discipline from the core principles, expressed in Python idioms (not
Scala's). The principle transfers; the syntax is Python's.

- **Pure functions first.** Put as much logic as possible in pure, easily testable
  functions. Side effects are pushed to the edges (interpreters, entry points).
- **Immutable data.** Model domain data as **frozen dataclasses**
  (`@dataclass(frozen=True)`). Never mutate arguments. Return new values rather
  than mutating in place.
- **Explicit dependencies.** Effectful collaborators are passed as explicit
  arguments, typed against a `typing.Protocol`, not reached for via globals or
  module-level singletons. This is the Python stand-in for injected algebras —
  same principle (dependencies are visible and swappable), Python form.
- **Model the domain with types.** Product types → frozen dataclasses or
  `NamedTuple`. Sum types → `enum.Enum`, or a union of frozen dataclasses consumed
  with structural `match`/`case`. Prefer a named type over a bare tuple whose
  fields you'd access positionally.
- **Errors are explicit at boundaries.** The pure core does not do IO-error
  handling. Where a function can legitimately fail as part of its result, model
  that in the return type (e.g. return an explicit result/`None`) rather than
  raising for control flow. Raise exceptions at system boundaries, validate input
  only there — trust internal code.
- **Prefer comprehensions and pure transforms** over imperative accumulation with
  mutation, where it stays readable. Don't sacrifice clarity for point-free
  cleverness — obvious code wins.

## Function size

Few absolute rules, but watch for these pitfalls:

- **Large jumps in abstraction levels** — e.g. inline unit-conversion or validation
  buried inside a function whose primary concern is geometry.
- **Single Responsibility violations** — if it's hard to give the function a
  descriptive, succinct name, it's probably doing too much.

---

## Python conventions

**Tech stack**: Python 3.14+ (pinned in `.python-version`) and **nothing else at
runtime** — Module 1 is `math` and `dataclasses` end to end. `numpy` (grid math)
and `scipy` (survey-point interpolation) come back with Module 2's excavation
work; add them with `uv add` when a module actually imports them, not before.

> [!NOTE]
> The empty `dependencies` list is deliberate, not an oversight. It is what lets
> the whole pipeline run on a bare CPython — including a browser runtime — so
> don't reach for a third-party package where the standard library will do.

**Toolchain** — the 2026-consolidated stack, mostly one company (Astral). All
tool configuration belongs in `pyproject.toml`, never in per-tool dotfiles:

- **`uv`** — Python version, virtualenv, dependency resolution, locking, and command
  running, all in one (replaces pip/venv/poetry/pyenv).
- **`ruff`** — lint *and* format in one binary (replaces black/flake8/isort/
  pyupgrade). The formatter is black-compatible.
- **`mypy`** — type checking, and the CI gate. Chosen over `pyright`/`ty` because
  it's the most mature and most compatible with `numpy`/`scipy` type stubs, which
  matters for a trust-the-numbers project. `ty` (Astral's Rust type checker) is
  much faster and worth revisiting once it settles, but `mypy` is the source of
  truth for now. Configured `strict = true` in `pyproject.toml`.
- **`pylance`** — a *second* type checker, running in the editor only. See
  [Two type checkers](#two-type-checkers-mypy-wins) below before acting on
  anything it reports.
- **`pytest`** — tests.

### Two type checkers — mypy wins

Two type checkers see this code, and they are set up so they rarely disagree:

| Checker | Where it runs | Configured in | Authority |
|---|---|---|---|
| `mypy` (`strict = true`) | CLI, **editor on save**, pre-commit hook, CI | `pyproject.toml` | **source of truth** |
| Pylance / Pyright (`basic`) | VS Code editor only | `.vscode/settings.json` | advisory |

The editor runs the **project's own mypy** via `ms-python.mypy-type-checker` with
`importStrategy: fromEnvironment` — the same binary and config the commit hook
uses, so an editor diagnostic and a blocked commit are the same event. Pylance is
deliberately held at `basic`: it earns its place as the language server
(completion, hover, go-to-definition), and at `basic` it still catches undefined
names and bad attribute access without arguing with mypy about inference.

> [!IMPORTANT]
> **When they disagree, `mypy` wins.** It is what gates the commit, so code that
> satisfies Pylance but fails `mypy` is broken; the reverse is at worst untidy.
> Never silence a `mypy` error to appease Pylance.

- **Do this** — find the annotation that satisfies both. Pyright is stricter about
  *inferred* types, so a real annotation usually fixes it cleanly. Example:
  `rows = []` passes `mypy` (which infers the element type from later `.append`
  calls) but Pyright reports `list[Unknown]`; writing
  `rows: list[dict[str, float]] = []` satisfies both and is better code anyway.
- **Don't do this** — add `# type: ignore` for a Pylance-only complaint. That
  suppresses `mypy`, the checker that actually matters, to quiet one that doesn't.
  `# pyright: ignore` is the narrower tool if suppression is genuinely needed.
- **Don't raise Pylance back to `strict`** without a reason. It was lowered on
  purpose: `numpy`/`pandas` generics are where Pyright and mypy diverge most, and
  only mypy can fail a commit.

### uv workflow

- Add deps with `uv add <pkg>`; dev deps with `uv add --dev pytest ruff mypy`.
- **Never activate a virtualenv manually** — run everything through `uv run`
  (`uv run pytest`, `uv run ruff check`, `uv run mypy .`) so the right environment
  is always used.
- **Commit `uv.lock`** so the project runs identically everywhere. Use
  `uv sync --frozen` in CI.
- Use `uvx <tool>` for one-off tools you don't want as project deps.

### Enforcement

- **Type hints are mandatory** on every function signature (params and return).
  The compiler safety Scala gave for free is now the type checker's job — it is
  not optional. `mypy` must pass clean; a type error is a broken build, the same
  way an unresolved Scala warning was.
- **`ruff` must pass clean** (lint and format). Format with `uv run ruff format`;
  don't hand-format. `ruff check --fix` handles unused imports and outdated syntax —
  use it liberally.
- Use `@dataclass(frozen=True)` for data representation. Add `slots=True` where it
  costs nothing.
- Define related constructors/factories as `@classmethod` or module-level functions
  on/near the type, not scattered.
- Prefer standard-library idioms over hand-rolled loops, and `numpy` once
  Module 2 brings it back for grid work — but keep the calculation legible and
  auditable (this is a trust-the-numbers project).
- Imports at the top of the file; no inline imports except to break a genuine cycle
  (and prefer restructuring over that).
- Absolute imports within the package.

**Where enforcement actually happens:**

- **On save** — `.vscode/settings.json` runs `ruff format` plus ruff's autofix and
  import sorting via the `charliermarsh.ruff` extension. It uses the project's
  pinned ruff (`ruff.importStrategy: fromEnvironment`), not the extension's bundled
  copy, so the editor and CI can't drift apart.
- **As you type** — Pylance type-checks in the editor. It is **advisory only**;
  see [Two type checkers](#two-type-checkers-mypy-wins).
- **On commit** — `.githooks/pre-commit` runs `ruff format --check`, `ruff check`,
  `mypy`, and `pytest` over the whole tree and aborts the commit on any failure. It checks
  the working tree, not just staged files, so an unrelated dirty file will block
  the commit. Bypass deliberately with `git commit --no-verify`.

## Units, vocabulary & coordinate frame

- **Domain terminology, including Slovak equivalents for roof/attic terms, is in
  [`docs/spec.md`](./docs/spec.md)** — use the Slovak terms in any output intended
  for the projektant or the builders.
- Units are **metres, degrees, and EUR** throughout. Convert at boundaries only;
  the core speaks these units and nothing else.
- The plot has **one fixed, documented coordinate frame** (origin and axis
  directions in `docs/spec.md`). Survey points arriving in another frame are
  translated/rotated **once at ingestion**; every core function speaks the plot
  frame.

---

## Testing

- **Write as few tests as possible that cover all the important properties.**
  Before writing tests, identify the specific properties worth testing. Only write
  tests that cover **different** properties and code paths — no duplicates, no
  low-value tests.
- A good test **breaks if the behavior it describes changes, and only then.** Don't
  test implementation details.
- **Every numeric output is pinned to a hand-computed reference.** These are the
  most important tests in the project — they are what "trust the numbers" means.
  Examples: flat plot with pad at grade → 0 excavation; roof at 45° → footprint × √2;
  rectangle of area A at average cut depth d → volume ≈ A × d.
- **For bug fixes**: write a test that reproduces the bug before fixing it.
- Prefer **hard-coded values** for any dimensions/inputs in tests over generated or
  "current" values, so tests are deterministic.
- Place tests in `tests/`, mirroring the package structure.
- Run tests with `uv run pytest`. Scope to a module with
  `uv run pytest tests/test_roof.py`.

---

## General practices

- **Code vs Documentation**: when code behavior contradicts documentation, trust
  the code as the source of truth — then fix the doc.
- Use GNU `sed` via `gsed` instead of `sed` for cross-platform compatibility.
- Avoid `git -C` and `gh --repo` unless strictly necessary.
- When analyzing code, check test files for additional context on usage patterns.

## Comments

- Only add comments when the code is not self-explanatory.
- Explain *why*, not *what*. Prefer clear, obvious code over a comment.
- Add comments about non-obvious assumptions or side-effects.
- **A deliberate imprecision is not a bug — don't "fix" it.** Several modelling
  choices in this project are intentionally approximate for budgeting. When you
  spot one, leave it and check `docs/decisions.md` before "correcting" it.

## Talking to me

Short. Verbosity is a bug, not thoroughness.

- **Answer in a few sentences.** No preamble, no restating my question, no summary
  of what you just did. Bullets over paragraphs.
- **Plain words.** Drop "comprehensive", "robust", "seamless", "leverage". Don't
  sell the work — say what's done, what isn't, what broke.
- **Explain on request, not by default.** Offer ("want the detail?") instead of
  pre-emptively writing three paragraphs.
- **Skip the mechanism tour.** Answer the question that was asked, not the four
  related ones.

## Commit messages

- **One-line subject**, imperative, explains the *why* when it isn't obvious.
  Add a body only when the why genuinely needs a sentence or two.
- Prefer a **commit-by-commit approach**: break changes into smaller, logical
  commits; each commit is one focused change, easy to review and revert.
- **PR descriptions stay short** — what changed and why, a few lines. No file
  walkthrough; the diff already shows that.

## Documentation

Docs live in `./docs`, kebab-case filenames. Style:

- ATX-style headings (`#`, `##`). Specify the language on every code block.
- `-` for unordered lists. Standard Markdown tables.
- GitHub-flavored callouts for important info: `> [!NOTE]`, `> [!WARNING]`, `> [!TIP]`.
- For style guides, use a **"Do this / Don't do this"** pattern with concrete
  examples, and always justify *why*.
- Reference code as `file_path:line_number` when pointing at a specific
  implementation.

## Code review

- Detailed guidelines in [`REVIEW.md`](./REVIEW.md).
- Priority order: **correctness** (do the numbers match the hand-checked
  references?) → **the purity boundary** (is `core/` still pure, is IO only at the
  edges?) → **clarity** → **style** → **performance**.

## Repeated feedback

- If you notice repeated requests for similar changes or expressions of
  frustration, suggest updating these instructions.
