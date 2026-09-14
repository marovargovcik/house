# Project Guidelines

## Core Principles

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

## General

- In a fresh clone, run `git config core.hooksPath .githooks` — otherwise the
  pre-commit hook never runs.
- Run Python through `uv run`; never activate a venv.
- When code and docs disagree, the code is right — fix the doc.
- `gsed`, not `sed`. Avoid `git -C` and `gh --repo`.
- Check the tests for usage examples.
- Anything for the projektant or the builders is in Slovak.

## Python — code structure

- **`core/` is pure:** no IO, no print, no global state, no argument mutation.
  Python won't enforce this.
- **IO and rendering live in `interpreters/` and entry points.** An interpreter
  splits building from writing: `render_html` returns the string, `write_html`
  saves it.
- **Validation is layered.** A spec's `__post_init__` raises on a bad field;
  `core/validate.py` returns problems with a combination; the entry point stops
  the run. Past that, trust inputs — no defensive clamps.
- **Calculations are named functions**, never inside render or UI code. Drawing
  coordinates are numbers too, so they live in `core/`.
- **Measured inputs have no defaults**, not even 0.
- Add a runtime dependency only when a module imports it.

## Python — style

- Frozen dataclasses (`slots=True`). Never mutate arguments.
- Effectful collaborators are passed in, typed as a `typing.Protocol` — no
  globals or singletons.
- Records are dataclasses or `NamedTuple`; alternatives are an `Enum` or a union
  of dataclasses with `match`. No positional tuples.
- An expected failure goes in the return type; raise only at boundaries.
- Type hints on every signature. `mypy` (strict) and `ruff` must pass clean.
- When Pylance and mypy disagree, mypy wins: fix it with a real annotation, never
  `# type: ignore`.
- Imports at the top, absolute.
- Comprehensions over mutation where readable. Obvious beats clever.
- Watch for mixed abstraction levels and functions that are hard to name.

## Testing

- Fewest tests that cover the important properties. No duplicates, no low-value
  tests.
- A test breaks when the behaviour changes, and only then.
- **Pin every number to a hand-computed reference** — e.g. 45° roof → footprint
  × √2.
- Hard-coded inputs.

## Comments

- Only where the code can't speak for itself. Explain *why*, in a line or two.
- No history ("first did", "no longer") — git has it.
- **A deliberate imprecision is not a bug.** Read the docstring before "fixing"
  one.

## Commit Messages

- One-line imperative subject that explains the *why*; a body only when needed.
- Prefix with the project when the commit stays inside one:
  `roof: Cap the clear ridge height at the collar tie`.
- Small, focused commits.

## Code Review

- See [`REVIEW.md`](./REVIEW.md). Priority: correctness → purity → clarity →
  style → performance.

## Documentation

- **`README.md`** — what it does today, for people, in plain words. No tech
  decisions, no plans; readable in a minute or two.
- **`CLAUDE.md`** — only rules the code can't show. No project descriptions,
  file trees, formulas or command lists.
- No `docs/` folders. ATX headings, a language on every code block, `-` lists.

## Talking to Me

Short. Verbosity is a bug, not thoroughness.

- **Answer in a few sentences.** No preamble, no restating my question, no summary
  of what you just did. Bullets over paragraphs.
- **Plain words.** Drop "comprehensive", "robust", "seamless", "leverage". Don't
  sell the work — say what's done, what isn't, what broke.
- **Explain on request, not by default.** Offer ("want the detail?") instead of
  pre-emptively writing three paragraphs.
- **Skip the mechanism tour.** Answer the question that was asked.

## Repeated Feedback

- If you notice repeated requests for similar changes or frustration, suggest
  updating these instructions.
