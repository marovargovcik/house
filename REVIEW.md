# Code Review

Approve a change that makes the codebase healthier, even if it isn't perfect.
This is a personal budgeting tool: the numbers and the purity boundary matter
most; there is no attack surface.

## Priority

1. **Correctness** — do outputs match hand-checked references, and would the test
   catch a wrong number?
2. **Purity** — is `core/` still pure, with IO only at the edges?
3. **Clarity** — naming, justified abstraction, no surprises, a *why* comment
   where the code can't say it.
4. **Style** — only rules written in `CLAUDE.md`; nothing ruff owns.
5. **Performance** — only unbounded or obviously wasteful work.

## Look for

- Sign errors; degrees vs radians; unit mix-ups.
- `core/` importing interpreters, rendering or IO; mutated arguments;
  module-level state; collaborators reached globally instead of passed in.
- Tests: key paths and edges covered (e.g. ridge below `h_min` → 0 width), no
  duplicates, hard-coded inputs, a regression test for each bug fix.
- Types: full hints, mypy clean, frozen dataclasses instead of positional tuples.

Deliberate approximations are not defects — check the settled decisions in
`CLAUDE.md` first. Don't ask to extract a literal used once.

## How

- Don't block on perfection, or on "I'd have done it differently".
- Label comments: `blocking`, `issue`, `suggestion`, `nitpick`, `question`,
  `thought`.
- Prefer a *why* comment in the code over a review comment.
