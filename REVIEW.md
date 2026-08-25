# Code Review Guidelines

The primary purpose of code review is to ensure the overall health of the codebase
improves over time. Approve a change when it definitely improves overall health,
even if it isn't perfect. Seek continuous improvement, not perfection.

This is a personal decision-support tool, not a networked service. The review
priorities reflect that: **correctness of the numbers** and **the purity boundary**
matter most; there is no auth/multi-tenant attack surface to police.

## Priority order

1. **Correctness** — do the outputs match the hand-checked references? Is the math
   right? Are the pinning tests present and meaningful?
2. **The purity boundary** — is `core/` still pure? Is IO/rendering confined to
   interpreters and entry points? Does terrain access still go through
   `Z_ground(x, y)`?
3. **Easy to understand** — naming, justified abstraction, no surprising behavior.
4. **Style** — only documented guideline violations, not personal preference.
5. **Performance** — rarely the bottleneck here; flag only egregious cases.

## Focus areas

### Correctness

- Every numeric output is pinned to a **hand-computed reference** in a test. Trace
  the calculation — don't just check that a test exists; check that it would catch
  a wrong number.
- Watch for sign errors and unit mix-ups (metres vs. degrees, radians vs. degrees
  in trig). Confirm angles are converted where `numpy` expects radians.
- Grid/cell-size effects on volume: is the result stable as resolution changes, or
  silently resolution-dependent?
- **Deliberate approximations are not defects.** Check `docs/decisions.md` before
  flagging a modelling simplification — several are intentional and safe-direction
  for budgeting.

### The purity boundary

- `core/` modules must not import interpreters, plotting/rendering libraries, or
  anything doing IO (file, network, `print`).
- No mutation of arguments; no module-level mutable state; no hidden globals.
- Terrain assumptions live only behind `Z_ground(x, y)` — flag any inlined slope
  math elsewhere.
- Effectful collaborators are passed explicitly (typed against a `Protocol`), not
  reached for globally.

### Easy to understand

- **Default to the most obvious code that works.** When introducing an abstraction,
  make sure its benefit outweighs the complexity it adds.
- **Write for the engineer who lacks your context.** Keep it principled and
  unsurprising.
- **When simple code isn't possible, document *why*** — a comment on the *why*, not
  the *what*.

Check for: naming clarity, justified abstraction (flag over-engineering), surprising
behavior, missing "why" comments on non-obvious logic. Do NOT flag style or
performance here — separate focus areas.

### Well tested

We should have *exactly* the right tests to verify the key properties, and no more.
A good test breaks if the behavior it describes changes, and *only* then.

Check for:

- All interesting code paths covered; the numeric outputs pinned to hand references.
- No low-value or duplicate tests; no tests coupled to implementation details.
- Missing edge cases on critical paths (e.g. ridge height below `h_min` → usable
  width 0; pad above grade → 0 excavation).
- **For bug fixes**: is there a test that would have caught the bug?
- Inputs hard-coded and deterministic — no reliance on generated/"current" values.

### Type safety

- Every function has complete type hints (params and return).
- `mypy` (the CI source of truth) passes clean — a type error is treated as a broken
  build, the way an unresolved compiler warning would be.
- Frozen dataclasses for domain data; no bare positional tuples where a named type
  belongs.

### Style

Only flag violations of documented guidelines in `CLAUDE.md`. Anything not in the
guide is personal preference and must not block a review. `ruff` handles formatting
and lint — don't hand-review what the formatter owns. Never suggest extracting
literals into constants unless they are used more than once.

### Performance

Rarely the constraint for this tool. Flag only: genuinely unbounded work, or an
obviously wasteful pattern (e.g. rebuilding a large grid inside a tight sweep loop
when it could be computed once). Don't micro-optimize legible numeric code.

## Principles

- **Balance progress with quality.** Don't block a change for days because it isn't
  perfect. Balance forward progress against the importance of the suggestions.
- **Keep ego out of the process.** Share alternatives with different tradeoffs, but
  don't block just because you'd have done it differently.
- **Use conventional comments.** Types like `blocking`, `issue`, `suggestion`,
  `nitpick`, `question`, `thought` communicate the weight of feedback.
- **Prefer code comments over review comments.** A "why" comment in the code guides
  future readers; a review comment is lost to time.
