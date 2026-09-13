---
title: House-Build Simulation — Spec
icon: 🏠
---

# House-Build Simulation — Project Spec & Decisions

A record of the design decisions for a small Python tool that estimates roof
material/cost and usable attic area for a self-build house on a sloped plot near
Trenčín. This is a scoping/decision-support tool, not an engineering-grade
calculator — the goal is trustworthy, hand-verifiable numbers you can sweep
across design variables. The plot, terrain and excavation are specced in the
repo's [`docs/site.md`](../../docs/site.md).

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
  (numpy, pandas, pytest, scipy) fits auditing and parameter sweeps best.
- **No terrain here.** The roof and attic do not depend on the ground. Terrain
  and excavation are separate projects behind the `Z_ground(x, y)` seam.

## 2. Project structure

```
core/            # pure modules, depend only on spec dataclasses
  specs.py       # frozen dataclasses: HouseSpec, RoofSpec, AtticSpec, CostSpec
  roof.py        # roof surface area, material/timber cost
  attic.py       # usable upstairs area vs. pitch/width
  views.py       # section/plan coordinates for drawings
  validate.py    # cross-spec input checks
interpreters/
  to_json.py
  to_csv.py      # sweep rows → CSV
  to_text.py     # sweep rows → fixed-width table for a terminal
  to_svg.py      # views → SVG
  to_html.py     # sweep + drawings → one self-contained page
  sk.py          # Slovak number formatting for the report
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

Cost = roof surface area × **one all-in €/m²** covering the whole roof: krov,
insulation, membrane, battens, covering, gutters, and labour. A builder quotes a
roof as one number, and one number carries exactly the precision this model has —
see `decisions.md`. It is charged on **gross** area including the overhang, a
deliberate over-estimate in the same direction.

Rafter length and gutter run are reported alongside the cost for ordering
material, not used in it.

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
> item (§5).

#### Headroom is clear height, not distance between bare structure

The rafter line is not the ceiling and the wall top is not the floor. Three
things stand between the structure and the height you can actually stand in, and
they behave differently:

| | What it is | How it acts |
|---|---|---|
| `roof_buildup` | rafter (krokva) depth, insulation, service cavity, lining | lowers the ceiling |
| `floor_buildup` | attic floor structure, insulation, screed, covering | raises the floor |
| `collar_above_wall_top` | collar tie (klieština) underside | caps the height everywhere |

**The roof build-up is measured perpendicular to the roof plane** — that is how
rafters and insulation are specified. Headroom is vertical, and two parallel
planes a perpendicular distance `t` apart stand `t / cos θ` apart vertically:

```
ceiling_drop = roof_buildup / cos(θ)
```

So the same 0.30 m of rafters and insulation costs 0.33 m of headroom at 25° and
0.42 m at 45°. A steep roof pays twice — it buys width but gives some back.

> [!WARNING]
> Taking `roof_buildup` as a *vertical* figure instead would under-state every
> steep pitch, which is the direction that flatters the result. This is the same
> class of mistake as wiring `o_eave` to the wrong factor in §3a.

At clear height `h` above the finished floor, horizontal distance from the eave
is `(h + ceiling_drop + floor_buildup − k) / tan θ`. So:

```
usable_width = width − 2 * max(0, (h_min + roof_buildup/cos θ + floor_buildup − k) / tan θ)
```

...clamped at 0, which also covers "the ceiling never reaches `h_min`" — that is
algebraically the same as the strip going negative. Usable floor area =
`usable_width * length`.

`clear_ridge_height = k + (width/2)·tan θ − ceiling_drop − floor_buildup` is the
best the attic ever gets, and the fastest way to see a pitch is hopeless. A
collar tie caps it like any other point, so with one it is the lesser of that
and `collar_above_wall_top − floor_buildup`.

#### The collar tie gates; it does not narrow

A collar tie caps clear height at its own underside. Under it you have the
collar's height; outboard of it the ceiling has already fallen below the collar.
So there is no middle case:

- collar clears `h_min` → it takes **nothing** off the strip the roof plane allows
- collar does not clear `h_min` → **nothing** in the attic does; usable area is 0

Which makes the useful output a constraint rather than a reduction:

```
min_collar_above_wall_top = h_min + floor_buildup
```

Independent of width and pitch — one figure to hand the projektant when the krov
is designed. Note the tension it creates: headroom pushes the collar up, and
structure wants it lower. We do not model the structural side.

Worked examples (h_min = 1.9 m, roof build-up 0.30 m, floor build-up 0.20 m):
- 9 m wide, 25° → 2.10 m structural ridge is **1.57 m clear**: no habitable
  attic at all, where measuring to bare structure claimed 0.85 m of usable width
- 9 m wide, 30° → usable_width 0.53 m (bare structure said 2.42 m)
- 9 m wide, 40° → usable_width 3.06 m (bare structure said 4.47 m)

**Key trade-off the sweep must surface:** steeper pitch *buys* usable attic area
but *costs* more roof surface (area grows as `1/cos θ`) and more ridge height.
That opposition is exactly why a sweep across θ beats guessing — and the
build-ups sharpen it, because they push the shallow end off the table entirely.

> [!NOTE]
> Not modelled: a ridge beam (hrebeňová väznica), purlins and their posts, and
> dormers. Each takes further headroom in a real krov. Today's figures are the
> ceiling of what a given pitch can deliver, not a promise.

### 3c. Knee-wall parameter (default 0)

Even though the current plan is **no knee wall**, keep knee-wall height `k` as a
parameter defaulting to 0, so "what would a 0.5 m knee wall buy me?" is answered
instantly without restructuring:

```
usable_width = width − 2 * max(0, (h_min + ceiling_drop + floor_buildup − k) / tan(θ))
```

The knee wall is the one term that pushes the other way: it offsets the two
build-ups one-for-one.

A knee wall also raises the roof: it stands on the wall top and the slopes
spring from it, so ridge height above the wall top becomes `k + (width/2)*tan(θ)`.
The sweep reports that sum as `ridge_above_wall_top_m` — buying attic area with a
knee wall is not free of height, which matters against a height limit.

### 3d. Drawing the sweep

A table of fifteen rows does not show what a pitch *is*. `uv run cli` with
`--html` writes one self-contained page: every swept row drawn as a gable
section and a plan, with the numbers beside it. Every sweep input is a required
flag — `README.md` carries the invocation for the design as it stands.

The page is **Slovak throughout** — prose, dimension labels, table headers, and
number formatting (decimal comma, no-break space between thousands) — because it
is what goes to the projektant and the builders. The core stays in English;
`interpreters/sk.py` and the label strings in the two renderers are the only
places that translate.

The split follows the rule in §1 rather than bending it:

- `core/views.py` produces the drawing's **coordinates in metres** — apex, eave,
  knee top, headroom line, roof outline, usable strip. They come from
  `roof.ridge_height` and `attic.usable_width`, the same functions the table
  uses, so the picture cannot disagree with the row beside it. Being numbers,
  they are pinned by tests like everything else.
- `interpreters/to_svg.py` turns metres into pixels and builds strings.
  `interpreters/to_html.py` is the only part that writes a file.

Two things the drawing is *for*, and the choices that follow from them:

- **One shared scale (px per metre) across every card**, never fit-to-box. An
  11 m house must look wider than a 9 m one and 25° must look shallower than
  45°, or the page shows nothing the table did not.
- **The hatched standing-room region's base is exactly `usable_width`.** The
  headroom rule of §3b, the number in the table, and the shape on the page are
  one fact drawn three ways. At a pitch too shallow to stand under, the h_min
  line is still drawn — floating above the ridge, which is the clearest possible
  statement of why the attic is unusable.

### Module 1 summary

- `roof.py`: surface area → cost; rafter geometry → timber (pure functions)
- `attic.py`: `(width, θ, h_min, build-ups, knee, collar) → usable area, clear
  ridge height` — headroom measured clear, not between bare structure
- `views.py` + `to_svg.py`/`to_html.py`: the same sweep, drawn (§3d)
- First real thing worth looking at: a sweep across **width × θ**.

---

## 4. Environment

- Local Python interpreter available; `uv` manages the environment.
- **Module 1 has no runtime dependencies** — `math` and `dataclasses` only. That
  is not an accident of scope: it keeps the whole pipeline runnable on a bare
  CPython, including a WASM build in the browser, which is the cheapest route to
  an interactive version of the sweep.
- `pytest`, `ruff` and `mypy` are dev-only.

## 5. Status / next steps

- Scoped with no remaining guesses on width and length.
- Build order: lock the pure functions + hand-checked tests first, then add
  interpreters (JSON, spreadsheet).
- Open item to confirm before/while building Module 1: `h_min` value and the
  Slovak habitable-area norm; the roofing-layer cost breakdown (€/m² per layer)
  for the actual chosen spec.
