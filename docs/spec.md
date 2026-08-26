---
title: House-Build Simulation — Spec
icon: 🏠
---

# House-Build Simulation — Project Spec & Decisions

A record of the design decisions for a small Python tool that estimates roof
material/cost, usable attic area, and excavation volume for a self-build house
on a sloped plot near Trenčín. This is a scoping/decision-support tool, not an
engineering-grade calculator — the goal is trustworthy, hand-verifiable numbers
you can sweep across design variables.

---

## 1. Guiding principles

- **Functional core, imperative shell.** A pure computational core owns all
  geometry and numbers. Visualization, spreadsheet export, and JSON output are
  *interpreters* that consume what the core produces. The core imports no
  rendering or UI code.
- **Trust over polish.** Code quality matters less than correctness of the
  numbers. Every output must be hand-checkable, and pinned by tests.
- **Python, not JS or Scala.** Chosen because the deliverable that matters is a
  pure, testable, auditable numeric core — not a 3D canvas. Python's ecosystem
  (numpy, pandas, pytest, scipy) fits auditing and parameter sweeps best. A 3D
  viewer, if built later, is a *separate* JS artifact reading the core's JSON
  output — not part of the core.
- **Terrain enters through a single seam.** All terrain-dependent math depends
  only on `Z_ground(x, y)`. Swapping today's model for future survey points is a
  function-body change with zero downstream edits.

## 2. Project structure

```
core/            # pure modules, depend only on spec dataclasses
  specs.py       # frozen dataclasses: HouseSpec, TerrainSpec, RoofSpec, ...
  roof.py        # roof surface area, material/timber cost
  attic.py       # usable upstairs area vs. pitch/width
  terrain.py     # Z_ground(x, y) — the terrain seam
  excavation.py  # excavation volume + max cut depth
interpreters/
  to_json.py
  csv.py
  to_scene.py    # later — geometry → JSON for a JS/Three.js viewer
tests/           # hand-checked cases pinning every output
```

Rendering stays strictly out of `core/`. Calculations live in separate named
functions (never tangled into render callbacks) so numbers can be unit-tested
independently of any visuals.

---

## 3. Module 1 — Roof geometry, material cost, usable attic

House shape is a simple "I" rectangle (no L-shapes or other forms), so the roof
is a plain gable rectangle. All formulas are pure trig and hand-verifiable.

### Terminology (English ↔ slovensky)

Use the Slovak terms in anything intended for the projektant or the builders.

| English | Slovensky |
|---|---|
| gable roof | sedlová strecha |
| ridge | hrebeň |
| pitch / roof angle | sklon strechy |
| rafters | krokvy |
| roof structure (load-bearing) | krov |
| eave overhang | odkvapový presah |
| eaves / gutter | odkvap / odkvapová sústava |
| gable / end wall | štít / štítová stena |
| rake / gable overhang | štítový presah |
| knee wall | nadmurovka |
| habitable attic | (obytné) podkrovie |
| usable / habitable floor area | úžitková / obytná plocha |

### 3a. Roof geometry + material cost

Inputs: `width`, `length`, `pitch θ`, `roofing_type` (with its €/m²), plus an
**eaves/gable overhang** parameter (real extra material, easy to forget).

- Ridge height above wall top: `(width / 2) * tan(θ)`
- Sloped rafter length per side: `(width / 2 + o_eave) / cos(θ)` — the rafter
  runs out over the eave overhang, so the overhang is part of its length
- **Roof surface area:**
  `(length + 2*o_gable) * (width + 2*o_eave) / cos(θ)`

Both overhangs are **horizontal projections** (see `decisions.md`):

- `o_eave` — *odkvapový presah*, the eave overhang at the bottom of the slopes on
  the long sides. It **continues the slope**, so it joins the `width` factor and is
  stretched by `1 / cos(θ)` along with it.
- `o_gable` — *štítový presah*, the rake overhang past the end walls along the
  ridge. It runs **horizontally along the ridge**, not down the pitch, so it joins
  the `length` factor, which carries no `cos(θ)` correction of its own.

> [!WARNING]
> This asymmetry is the easy thing to get wrong. `o_eave` belongs to the factor
> that gets stretched by the pitch; `o_gable` belongs to the factor that doesn't.
> Wiring them to the wrong factors still produces a plausible-looking number.

The `width / cos(θ)` term already covers both roof planes: each half is
`(width/2)/cos(θ)`, times two.

Material cost = area × €/m² per layer (roofing sheet, membrane, battens,
insulation), charged on **gross** area including the overhang — a deliberate
over-estimate, see `decisions.md`.

Krov (the load-bearing structure) is priced the same way — €/m² of roof surface,
a ballpark that avoids guessing a rafter count and spacing we have not designed
yet. Rafter length is reported alongside it for timber ordering, not used in the
cost.

Sanity checks to pin in tests:
- flat-ish roof (θ → 0) → area ≈ footprint
- θ = 45° → area = footprint × √2
- both overhangs 0 → area reduces to `length * width / cos(θ)`, the pre-overhang
  formula (confirms backward consistency)
- **swapping `o_eave` and `o_gable` changes the result** — with `length` 10 m,
  `width` 9 m, θ = 30°: `o_eave` 0.6 / `o_gable` 0.4 → 127.2018 m², but
  0.4 / 0.6 → 126.7399 m². This is the check that catches the two terms being
  wired to the wrong factors; it requires `length ≠ width` and `o_eave ≠ o_gable`
  to bite.

### 3b. Usable upstairs area (the one to model carefully)

Under a gable with **no knee wall**, the ceiling slopes from full ridge height
down to zero at the eaves. Usable floor is bounded by a minimum standing
headroom `h_min`.

> [!IMPORTANT]
> `h_min` is a **required parameter with no default**. The 1.9 m used in the
> worked examples below is an explicit sweep assumption, not a confirmed value —
> the binding figure depends on the Slovak *obytná plocha* norm, still an open
> item (§7).

At headroom `h`, horizontal distance from the eave is `h / tan(θ)`. So:

```
usable_width = width − 2 * (h_min / tan(θ))
```

...provided ridge height `(width/2)*tan(θ) > h_min`, else usable_width = 0.
Usable floor area = `usable_width * length`.

Worked examples (h_min = 1.9 m):
- 9 m wide, 30° → each side loses 1.9/tan(30°) ≈ 3.29 m → usable_width ≈ 2.42 m
  (the "stand in the middle, bump your head reaching the sides" problem)
- 9 m wide, 40° → each side loses ≈ 2.26 m → usable_width ≈ 4.47 m

**Key trade-off the sweep must surface:** steeper pitch *buys* usable attic area
but *costs* more roof surface (area grows as `1/cos θ`) and more ridge height.
That opposition is exactly why a sweep across θ beats guessing.

### 3c. Knee-wall parameter (default 0)

Even though the current plan is **no knee wall**, keep knee-wall height `k` as a
parameter defaulting to 0, so "what would a 0.5 m knee wall buy me?" is answered
instantly without restructuring:

```
usable_width = width − 2 * max(0, (h_min − k) / tan(θ))
```

### Module 1 summary

- `roof.py`: surface area → cost; rafter geometry → timber (pure functions)
- `attic.py`: `(width, θ, h_min, knee=0) → usable area` (one pure function)
- First real thing worth looking at: a sweep across **width × θ**.

---

## 4. Module 2 — Excavation volume

### 4a. The plot (measured)

46 m long × 20 m wide. Elevation drops along the 46 m length in three segments
(total 7 m drop, very unevenly distributed):

| Length segment | Drop | Slope | Character |
|---|---|---|---|
| 0–18 m | 3.5 m | ~11° | gentle upper shelf |
| 18–21 m | 2.5 m | ~40° | **steep 3 m step** (garage goes here) |
| 21–46 m | 1.0 m | ~2° | near-flat lower shelf |

The plot is two gentle shelves separated by a steep 3 m step. That step is the
natural place to tuck the garage into the hill: dig into the escarpment, the
garage's back wall becomes the retaining wall against the ~2.5 m face, living
level sits on the upper shelf.

### 4b. House placement (decided)

- "I"-shape, **10–11 m wide** (plot is 20 m wide → ~9–10 m to spare across).
- Long axis runs **along the slope** (down the 46 m direction).
- **Front wall at x = 18 m**, extending toward the back (toward 46 m).
- So the front ~3 m of house (18–21 m) sits over the steep step → this is the
  garage, cutting up to ~2.5 m into the hill. Everything from 21 m back sits over
  near-flat ground close to garage-floor level → minimal digging there.

This is why the design "evens out": the terrain does the work. Heavy excavation
is confined to the front garage zone; the rest barely needs digging.

### 4c. The excavation model

Terrain is piecewise-linear along length `x` (0 at top edge, increasing
downhill), currently constant across width `y`:

```
Z_ground(x, y):   # y ignored today, present in signature by design
  x ∈ [0, 18]  → drop 3.5 m
  x ∈ [18, 21] → drop 2.5 m (steep)
  x ∈ [21, 46] → drop 1.0 m (near-flat)
```

House sits at pad elevation `Z_pad` (garage finished floor level). Over a grid of
the footprint:

```
dig_depth = max(0, Z_ground(x, y) − Z_pad)
excavation_volume = Σ dig_depth * cell_area
max_cut_depth     = max(dig_depth)   # → height of the uphill retaining/foundation wall
```

Implement as a few numpy lines: sample `Z_ground` per cell, subtract `Z_pad`,
clamp negatives to zero, × cell area, sum.

**`Z_pad` is the design knob.** Set it near the 21 m line's elevation and: the
garage front cuts ~2.5 m into the step while the back of the house sits almost on
grade. Sweeping `Z_pad` trades garage cut depth against fill/foundation at the
back — this single sweep answers "how deep do we dig," and `max_cut_depth` gives
the garage's uphill wall height against the ~2.5 m face (the number foundation
cost hinges on).

### 4d. Signature & outputs

- `excavation.py`: `(terrain, footprint, position, Z_pad, cell_size) → (volume, max_cut_depth)`
- Output that matters: excavation **volume (m³)**; plus **max cut depth** (free).

Sanity checks to pin in tests:
- footprint on flat ground with `Z_pad` = ground → volume 0
- rectangle of area A on a plane, avg cut depth d (= depth at centroid) →
  volume ≈ A × d (hand-computable)

---

## 5. The terrain seam & future survey points

This is the reason for the whole core/interpreter split. Everything
terrain-dependent depends only on `Z_ground(x, y)`. The excavation math never
knows *how* elevation was produced. Terrain fidelity upgrades in three steps,
each a **function-body-only** change with no downstream edits:

1. **Today:** longitudinal profile (three segments along length, constant across
   width). `y` ignored.
2. **Next (from the measurer):** discrete spot elevations — a set of (x, y, z)
   points. `Z_ground` becomes a 2D interpolation (scipy `griddata` linear/cubic,
   or a Delaunay/TIN triangulation as surveyors/CAD use). **Now varies across
   width too** — which today's model flattens.
3. **Later (if a full survey):** dense point cloud / contour DTM — same
   interface, heavier interpolation behind it.

The eventual faithful point-cloud reconstruction is the **intended endpoint** of
the `Z_ground(x, y)` seam, not a bolt-on.

### Four things baked in now to make the upgrade a genuine drop-in

1. **2D signature from the start:** always `Z_ground(x, y)`, even though today's
   body ignores `y`. Prevents touching call sites when width-dependence arrives.
2. **Pluggable terrain source:** today = piecewise-linear-in-x; tomorrow =
   interpolated DEM from (x, y, z) via `griddata`/TIN. All inside the `Z_ground`
   body.
3. **Cell-size parameter exposed now:** grid resolution barely matters on today's
   smooth terrain but matters on real bumpy terrain. Expose as an input so
   refining precision is a one-line change.
4. **Fixed, documented coordinate frame:** one origin and axis convention for the
   plot. Survey points often arrive in national grid or a local origin —
   translate/rotate them **once** at ingestion into the plot frame; everything
   else already speaks that frame.

### Honest caveats (so today's numbers aren't over-trusted)

- Today's model assumes ground is **constant across the 20 m width**. Real
  terrain likely has cross-slope; when (x, y, z) points arrive the excavation
  number will shift, possibly non-trivially. Treat today's volume as a **scoping
  estimate**, not final.
- The single-`Z_pad` model treats a true split-level (garage floor vs. living
  floor half a story up) as one pad at garage-floor level. This slightly
  **over-estimates** excavation (safe direction for budgeting). A second pad
  "step" can be added later as a second clamp region without restructuring.

---

## 6. Environment

- Local Python interpreter available; `pip` available for dependencies.
- Likely dependencies: `numpy` (grid math), `pandas` (sweeps → tables/CSV),
  `pytest` (pin the numbers), `scipy` (future survey-point interpolation).

## 7. Status / next steps

- Both modules scoped with no remaining guesses (real terrain profile, real
  placement, real width).
- Build order: lock the pure functions + hand-checked tests first, then add
  interpreters (JSON, spreadsheet), then optionally a separate JS/Three.js viewer
  reading the core's JSON.
- Open item to confirm before/while building Module 1: `h_min` value and the
  Slovak habitable-area norm; the roofing-layer cost breakdown (€/m² per layer)
  for the actual chosen spec.
