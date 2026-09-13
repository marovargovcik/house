---
title: Decision Log
icon: 🧭
---

# Decision Log

Dated record of settled decisions that span projects. A project's own decisions
live in its `docs/decisions.md` — e.g.
[`roof/docs/decisions.md`](../roof/docs/decisions.md). **Do not re-litigate or
"fix" these without being asked** — several are deliberate approximations, not
oversights.

## 2026-09

- **One repo, isolated projects.** roof, terrain, excavation, scene and the
  Sweet Home 3D model each get a folder with their own `pyproject.toml`, lockfile,
  venv and `check`. There is no uv workspace and no Python configuration at the
  root: a project should read and run on its own. A Python project that needs
  another takes a path dependency (`[tool.uv.sources]`, `editable = true`). The
  cost, one lockfile per project, is accepted. **Do not** add a root workspace to
  share a lockfile.

- **The `house` package is now `roof`.** It covers roof and attic only.
  Excavation leaves for its own project, so "house" no longer named it.

- **Terrain and excavation are separate Python projects.** `excavation` depends
  on `terrain` for `Z_ground`.

- **The plot frame is the survey's S-JTSK, flipped and shifted:**
  `e = 489216.00 − Y`, `n = 1201780.00 − X`, heights absolute Bpv. It is the frame
  the earlier terrain artifacts already used. Definition and check points in
  `site.md`.

- **`Z_ground` is a triangle mesh (TIN) over the survey points**, linear inside
  each triangle. It is what surveying software does, and a height can be checked
  by hand from three points. Chosen over inverse-distance weighting and a fitted
  plane, which the earlier artifacts also computed. Smoothing is not decided.

- **The terrain and the house are drawn in Python, not Three.js.** The message is
  how the house sits in the terrain — garage dug into the slope, one storey above,
  a roof of about 25°. A true-scale long section and a site plan (SVG) say that
  best, and their coordinates are pinned by tests like any other number. PyVista
  3D views come later, for the overall impression. VTK installs as a pip wheel
  using only the GL/X11 libraries already on the system, but it is ~700 MB, so it
  belongs to `scene/` alone. The earlier Three.js artifacts are not being ported.

- **Sweet Home 3D is for the interior.** It has no real terrain and cannot read
  the Python specs, so the house dimensions are typed in by hand from the specs,
  which stay the source of truth. Its OBJ export can later be placed on the
  terrain in `scene/`.

- **Binary sources go through Git LFS:** `*.sh3d`, `*.dwg`, `*.pdf`. The survey's
  point list stays plain text, so it diffs.

- **No export for the architects for now.** They use SketchUp; if one is needed,
  DXF with contours and survey points in the plot frame is the candidate.

## 2026-08

- **Language: Python, not JavaScript or Scala.** The deliverable that matters is a
  pure, testable, auditable numeric *core*, not a 3D canvas. Python's ecosystem
  (numpy, pandas, pytest, scipy) fits auditing and parameter sweeps best. A 3D
  viewer, if built, is a *separate* JS artifact reading the core's JSON output —
  not part of the core. *Superseded in part:* the drawings and 3D views are
  Python too — see 2026-09.

- **Functional core / imperative shell.** `core/` is pure; IO and rendering are
  interpreters at the edges. Purity is upheld by discipline (Python won't enforce
  it), which is why it's stated as a load-bearing invariant, not a preference.

- **Single terrain seam `Z_ground(x, y)`.** All terrain math depends only on this
  function. Signature keeps `y` even though today's model ignores it, so
  swapping in survey-point terrain later is a body-only change. **Do not** remove
  the unused `y` parameter.

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
  *Superseded:* the survey has arrived (`data/survey/`), and `Z_ground` is a
  triangle mesh over it — see 2026-09.

- **House placement fixed:** "I"-shape, 10–11 m wide, long axis along the slope,
  front wall at x = 18 m (top of the steep 3 m step), garage cutting into the
  escarpment. See `site.md` for the plot profile and full reasoning.
  *Superseded in part:* the position was stated in the pre-survey frame and has to
  be restated in the plot frame.
