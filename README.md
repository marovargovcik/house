# house

Tools and models for a self-build house on a sloped plot near Trenčín. Each
folder is its own project, with its own README, environment and checks.

| Project | What it is |
|---|---|
| [`roof/`](./roof/README.md) | Roof cost and usable attic area, swept across width and pitch |

Planned: `terrain/`, `excavation/`, `scene/` and `model/` — see
[`CLAUDE.md`](./CLAUDE.md).

## Setup

```bash
git config core.hooksPath .githooks   # pre-commit runs ./check of each touched project (per clone)
git lfs install                       # .sh3d, .dwg and .pdf are stored in Git LFS
```

Then follow the project's README. In VS Code, open `house.code-workspace`, so
each project gets its own interpreter and settings.

## Documentation

- [`docs/site.md`](./docs/site.md) — the plot: survey, coordinate frame, terrain and excavation specs
- [`docs/decisions.md`](./docs/decisions.md) — decisions that span projects
- [`CLAUDE.md`](./CLAUDE.md) — architecture invariants and working conventions
- [`REVIEW.md`](./REVIEW.md) — code review guidelines
