---
title: The site
icon: ⛰️
---

# The site — plot, survey, terrain and excavation

Facts about the plot that more than one project depends on, plus the specs for
the terrain and excavation projects until each gets its own folder.

## 1. Survey and coordinate frame

- **Source:** the surveyor's measurement of parcel 1561/1 (job `TE_Kanova4a`), in
  [`data/`](../data). `terrain.txt` is the point list — one point per line:
  number, Y, X, height. `terrain.dwg` / `terrain.pdf` is the drawing, and the only
  record of what each point *is* (boundary corner, fence, tree, road); no code
  reads it.
- **Input frame:** S-JTSK (Y, X), heights Bpv in metres above sea level. Points
  with height 0.00 only mark a position and are not terrain.
- **Plot frame:** every core function speaks this and nothing else. Survey
  points are converted **once, at ingestion**:

  ```text
  e = 489216.00 − Y      # metres, east
  n = 1201780.00 − X     # metres, north
  z = height             # metres, Bpv — absolute, not relative to the plot
  ```

  S-JTSK's axes point west (Y) and south (X); the flip turns them into east and
  north. `Z_ground(x, y)` takes `x = e`, `y = n`. The frame matches the earlier
  terrain artifacts: point 1 (489191.47, 1201769.56) → (24.53, 10.44), point 3
  (489172.31, 1201775.75) → (43.69, 4.25).
- **Ground surface:** `Z_ground` is a triangle mesh (TIN) over the survey points,
  linear inside each triangle — see [`decisions.md`](./decisions.md).

> [!WARNING]
> §2 and §3 predate the survey. They were written against a hand-measured
> profile (46 × 20 m, `x` along the length, constant across the width). The
> excavation model (§2c–§2d) and the seam design (§3) still hold; the plot
> numbers and placement in §2a–§2b do not match the survey and get restated in
> the plot frame when `excavation/` starts.

## 2. Excavation volume

### 2a. The plot (measured)

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

### 2b. House placement (decided)

- "I"-shape, **10–11 m wide** (plot is 20 m wide → ~9–10 m to spare across).
- Long axis runs **along the slope** (down the 46 m direction).
- **Front wall at x = 18 m**, extending toward the back (toward 46 m).
- **25 m long.** The front wall at 18 m on a 46 m plot leaves 28 m to build
  into, so the house runs 18–43 m with ~3 m to spare at the bottom edge. Module 1
  sweeps width and pitch against this single fixed length.
- So the front ~3 m of house (18–21 m) sits over the steep step → this is the
  garage, cutting up to ~2.5 m into the hill. Everything from 21 m back sits over
  near-flat ground close to garage-floor level → minimal digging there.

This is why the design "evens out": the terrain does the work. Heavy excavation
is confined to the front garage zone; the rest barely needs digging.

### 2c. The excavation model

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

### 2d. Signature & outputs

- `excavation.py`: `(terrain, footprint, position, Z_pad, cell_size) → (volume, max_cut_depth)`
- Output that matters: excavation **volume (m³)**; plus **max cut depth** (free).

Sanity checks to pin in tests:
- footprint on flat ground with `Z_pad` = ground → volume 0
- rectangle of area A on a plane, avg cut depth d (= depth at centroid) →
  volume ≈ A × d (hand-computable)

---

## 3. The terrain seam & future survey points

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
