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

- **No knee wall — but keep the parameter.** Current design has no knee wall.
  The `attic` calculation still takes knee-wall height as a parameter, so "what
  would a 0.5 m knee wall buy?" is answered instantly without restructuring.
  **Do not** delete the parameter as dead code. *Superseded in part:* it no
  longer defaults to 0 — every caller states it, per the no-defaults rule below.

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

- **Headroom is clear height; the build-ups are required inputs.** The model
  first measured `h_min` from the wall top to the rafter line — bare structure to
  bare structure — which over-stated the usable strip by roughly half and, at
  9 m / 25°, reported 0.85 m of usable width where nothing clears 1.9 m at all.
  `roof_buildup` and `floor_buildup` are now required parameters with **no
  defaults**, for the same reason `h_min` has none: a zero default silently
  restores the flattering number. `roof_buildup` is measured **perpendicular to
  the roof plane**, so it costs `t / cos θ` of headroom — **do not** re-specify
  it as a vertical figure, which would under-state every steep pitch.

- **A collar tie gates the attic rather than narrowing it.** A collar caps clear
  height everywhere at once: under it you have the collar's height, outboard of
  it the ceiling is already lower. So it either rules the attic out entirely or
  costs nothing, and the useful output is the constraint
  `min_collar_above_wall_top = h_min + floor_buildup` — one figure for a whole
  sweep. Treating the collar plane as a ceiling is deliberately conservative (you
  can put your head between collars, but not while walking). **Do not** model it
  as a width reduction. Ridge beams, purlins, and dormers are *not* modelled, so
  today's figures are the ceiling of what a pitch can deliver, not a promise.

- **Measured inputs carry no defaults — in the specs or the entry point.** What
  started as a rule for `h_min` now applies across the board: `RoofSpec`'s two
  overhangs and `AtticSpec`'s build-ups take no defaults, and every CLI flag is
  `required=True`. A default is a number that reaches a result without anyone
  choosing it, and a default in the entry point puts back exactly what the core
  refuses one layer out. The cost is a long command line; `README.md` carries the
  current design's invocation, and the reasoning behind each figure lives in
  these docs rather than beside the value.

  **No exceptions**, including where absence is the answer: a roof with no knee
  wall passes `knee_height=0.0`, and one with no collar tie passes
  `collar_above_wall_top=None`. On the command line both are `0`, since a flag
  cannot be required and also omitted — that translation lives in `cli.py` alone,
  so `AtticSpec` keeps `float | None` (absence genuinely is not a height) and
  still rejects a collar at or below the wall top.

- **The sweep returns frozen dataclasses, not a DataFrame; Module 1 has no
  runtime dependencies.** `pandas` was only ever a container here — the sweep
  built dicts, wrapped them, and the interpreters unwrapped them again — so a
  named `SweepRow` is both what this project reaches for anyway and one less
  thing between the numbers and a reader. `numpy` and `scipy` were declared but
  imported nowhere. All three are gone; `uv add` brings numpy and scipy back when
  Module 2's grid work actually imports them.

  The payoff beyond tidiness: the whole Module 1 pipeline is `math` and
  `dataclasses`, so it runs on a bare CPython — including a WASM build in the
  browser, which is the cheapest path to an interactive sweep with sliders
  instead of flags. **Do not** add a runtime dependency to Module 1 without
  weighing that.

- **Validation is layered by what a check can see.** A spec's `__post_init__`
  refuses a field that is nonsense on its own — that is where `h_min > 0`,
  `0 < pitch < 90`, and *collar above the knee top* live, the last one because
  both fields are `AtticSpec`'s own. A check needing two specs cannot go there:
  2.4 m is a fine collar and 25° on a 9 m house is a fine roof, and there is no
  such roof with such a collar in it. Those live in `core/validate.py`, which the
  entry point runs after collecting every input and before computing anything.

  Specs **raise** (the value itself is unusable); `validate` **returns** its
  problems (a bad combination is a fact about the run, and the entry point is
  what turns it into an exit code). The layer builds every spec the sweep will,
  so `sweep.width_by_pitch` is handed inputs it can trust.

  *Consequence:* **do not** add a defensive clamp downstream for a shape
  validation already rules out — a collar poking through the roof was first
  "fixed" by clamping it in `views`, which is dead code once the spec refuses the
  input.

  **A failed cross-spec check fails the whole run**, naming the offending
  (width, pitch) rows rather than dropping them: a row for a house nobody can
  build is not an answer, and the sweep is only worth reading if every row is
  one. The cost is that one impossible combination blocks the rest, which is
  accepted — the fix is to lower the collar or drop those rows from the sweep.
  **Do not** downgrade this to skipping the offending rows, or to a warning on
  the report.

  **Not** validated, deliberately: a pitch too shallow to stand under and a
  collar too low to clear `h_min` are *results* the model already reports —
  0 usable width, NaN per m², and the collar note on the page.

- **Interpreters split building from writing.** `render_html` / `write_html`,
  `render_csv` / `write_csv`. The pure function returns the string; the wrapper
  is the only line that touches disk. Keeps the effect at the very edge and lets
  a caller with nowhere to write still have the output.

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
- Roof and floor build-up thicknesses — sweeping at 0.30 m (perpendicular) and
  0.20 m as explicit assumptions. Both need the projektant's section drawing:
  they move the usable strip more than any other input, and at the shallow end
  they decide whether there is an attic at all.
- Collar tie: whether the krov has one, and at what height. `min_collar_height`
  reports the lowest that works, currently 2.1 m above the wall top.
