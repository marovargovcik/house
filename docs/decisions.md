---
title: Decision Log
icon: 🧭
---

# Decision Log

Dated record of settled decisions and the reasoning behind them. **Do not
re-litigate or "fix" these without being asked** — several are deliberate
approximations, not oversights. When a modelling choice looks imprecise, check
here first.

## 2026-08

- **Language: Python, not JavaScript or Scala.** The deliverable that matters is a
  pure, testable, auditable numeric *core*, not a 3D canvas. Python's ecosystem
  (numpy, pandas, pytest, scipy) fits auditing and parameter sweeps best. A 3D
  viewer, if built, is a *separate* JS artifact reading the core's JSON output —
  not part of the core.

- **Functional core / imperative shell.** `core/` is pure; IO and rendering are
  interpreters at the edges. Purity is upheld by discipline (Python won't enforce
  it), which is why it's stated as a load-bearing invariant, not a preference.

- **Single terrain seam `Z_ground(x, y)`.** All terrain math depends only on this
  function. Signature keeps `y` even though today's model ignores it, so
  swapping in survey-point terrain later is a body-only change. **Do not** remove
  the unused `y` parameter.

- **No knee wall — but keep the parameter (default 0).** Current design has no knee
  wall. The `attic` calculation still takes knee-wall height as a parameter
  defaulting to 0, so "what would a 0.5 m knee wall buy?" is answered instantly
  without restructuring. **Do not** delete the parameter as dead code.

- **Single `Z_pad` excavation model (deliberate over-estimate).** A true split-level
  (garage floor vs. living floor half a story up) has two pad elevations. We model
  one pad at garage-floor level, which slightly **over-estimates** excavation.
  That is the safe direction for budgeting. A second pad "step" can be added later
  as a second clamp region. **This is intentional — do not "correct" it to a
  two-pad model unless asked.**

- **Terrain today = piecewise-linear along length, constant across width.** Real
  terrain has cross-slope; today's model flattens it because we only have a
  longitudinal profile. Today's excavation number is a **scoping estimate**, not
  final. It will shift when (x, y, z) survey points arrive. Expected and accepted.

- **House placement fixed:** "I"-shape, 10–11 m wide, long axis along the slope,
  front wall at x = 18 m (top of the steep 3 m step), garage cutting into the
  escarpment. See `spec.md` for the plot profile and full reasoning.

- **Overhang measured as horizontal projection (both eave and gable).** Roofers
  quote horizontal projections, and it keeps the formula hand-checkable. The
  consequence in the formula is an asymmetry: `o_eave` folds into the `/cos θ`
  term (it continues the slope), while `o_gable` adds to the `length` factor
  outside it (it runs horizontally along the ridge). **Do not** "simplify" by
  treating both the same way, and **do not** switch the eave overhang to a
  measurement along the slope — that is a different, rejected convention.
  *Scope of this assumption:* it is geometrically correct for a standard gable
  with a horizontal rake overhang, which is what the locked "I"-shape plan has.
  A hip end or a more complex roof form would require revisiting the `o_gable`
  term — recorded here so the assumption is visible rather than buried in the
  formula.

- **All cost layers charged on gross roof area, including over the overhang
  (deliberate over-estimate).** Sheet, membrane, and battens genuinely run out
  over the eaves; insulation normally stops at the heated envelope, so charging it
  on gross area over-estimates. This is intentional, in the same budgeting-safe
  direction as the single-`Z_pad` excavation choice above. **Do not** add a
  per-layer `covers_overhang` flag unless explicitly asked. Possible future
  refinement if insulation cost turns out to dominate the layer stack.

- **One all-in €/m² for the roof, not a layer stack.** The per-layer roofing
  rates, the separate krov €/m², and the per-metre gutter rate collapsed into a
  single figure covering structure, insulation, membrane, battens, covering,
  gutters, and labour. A builder quotes the roof as one number; splitting it
  invited a precision the inputs never had. The gross-area decision above still
  stands and now applies to that single rate. *Consequence:* gutters no longer
  scale with gutter **run** — they ride on roof **area**. For a rectangle of
  roughly these proportions that is fine for scoping, but it drifts for a long,
  narrow house, so `gutter_run` stays reported as geometry for ordering.
  **Do not** re-introduce per-layer costing unless a quote actually arrives
  broken down that way.

- **`h_min` is a required parameter with no default.** Prevents an unverified
  value silently ending up in a result. Sweeps run at 1.9 m explicitly until the
  Slovak *obytná plocha* norm is confirmed. **Do not** add a default value until
  the norm is confirmed and documented here.

- **Kept the current B2B base engagement** (context only — not a code decision).

## Open items

- `h_min` value and the Slovak habitable-area norm (*obytná plocha*) — needed to
  finalize the attic calculation. Commercial Slovak sources recommend a knee wall
  (*nadmurovka*) of ~1.3 m and cite a 20–45° pitch range for a habitable attic.
  Treat these as **indicative sanity-check anchors only** — the binding `h_min`
  and habitable-area definition needs the actual norm, not a builder's blog.
