# roof

Works out the roof of the house for a range of pitches:

- **roof** — surface area and cost
- **attic** — the upstairs floor area you can stand in

Every number is checked by a test against a hand calculation. It is a budgeting
tool, not an engineering one.

## Setup

```bash
uv sync
npm --prefix web install
```

Run everything from `roof/`.

## Run it

There are no defaults: you give every input, so no number gets in unchosen.
The current design:

```bash
uv run cli --html roof.html \
  --widths 10 --length 25 --pitches 25 30 35 40 45 \
  --overhang-eave 0.6 --overhang-gable 0.4 \
  --h-min 1.9 --roof-buildup 0.30 --floor-buildup 0.20 --knee 0 --collar 0 \
  --eur-per-m2 110
```

This prints a table and writes `roof.html`: every pitch drawn as a section and
a plan, in Slovak, for the projektant. Add a file path as the first
argument to get CSV too. `uv run cli --help` explains each input.

`--knee 0` and `--collar 0` mean no nadmurovka and no klieština.

To try a variant, change one flag:

```bash
--knee 0.5                                  # with a nadmurovka
--collar 2.4                                # with a klieština
--roof-buildup 0.24 --floor-buildup 0.15    # a thinner build-up
```

## In a browser

```bash
uv run web
```

The same inputs as a form, with the drawing, the table and a CSV download.

## Checks

```bash
./check    # everything the commit hook runs
```

## What's counted

- **Cost** is one all-in price per m² for the whole roof, labour included,
  charged on the area with the overhangs — on purpose a little high.
- **Attic area** is floor with at least `--h-min` of headroom, measured to the
  finished floor and ceiling. A ridge beam, purlins or dormers would take some
  of it away.

## Open questions

- `--h-min`: 1.9 m until the Slovak norm for obytná plocha is confirmed.
- `--roof-buildup` and `--floor-buildup`: 0.30 and 0.20 m until the projektant's
  section drawing. They change the attic area the most.
- Klieština: is there one, and how high? It must sit at least `--h-min` +
  `--floor-buildup` (now 2.1 m) above the wall top.
