"""Entry point for the Module 1 sweep (`docs/spec.md` §3): width by pitch.

The imperative shell — it picks the inputs, calls the pure core, and prints. Every
number here is a stated assumption rather than a default hidden in the core: the
core takes `h_min` with no default by decision, and the roof rate is a single
all-in EUR/m² figure rather than a layer stack (`docs/decisions.md`).
"""

import argparse
from pathlib import Path

from house.core import sweep
from house.core.specs import AtticSpec, CostSpec
from house.interpreters import to_csv, to_html

# Footprint per the locked placement in `docs/spec.md` §4b: "I"-shape, 10-11 m
# wide, long axis down the slope. 9 m is swept too as the low anchor the worked
# examples in §3b use.
WIDTHS = (9.0, 10.0, 11.0)
# Front wall at x = 18 m on a 46 m plot leaves 28 m to build into, so 25 m runs
# the house nearly to the lower shelf with ~3 m to spare (`docs/spec.md` §4b).
LENGTH = 25.0
PITCHES_DEG = (25.0, 30.0, 35.0, 40.0, 45.0)
OVERHANG_EAVE = 0.6
OVERHANG_GABLE = 0.4

# An explicit sweep assumption, not a confirmed value — the binding figure waits
# on the Slovak *obytná plocha* norm.
H_MIN = 1.9

# All-in roof rate: krov, insulation, membrane, battens, covering, gutters, and
# labour in one number, the way a builder quotes it (`docs/decisions.md`).
COSTS = CostSpec(eur_per_m2=110.0)


def main() -> None:
    """Print the sweep; optionally write it as CSV and as a drawn HTML report."""
    parser = argparse.ArgumentParser(
        description="Roof and attic sweep over width and pitch."
    )
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        help="write the table here as CSV as well as printing it",
    )
    parser.add_argument(
        "--html",
        type=Path,
        help="also write a drawn report here: section and plan per swept row",
    )
    args = parser.parse_args()

    attic = AtticSpec(h_min=H_MIN)
    table = sweep.width_by_pitch(
        widths=WIDTHS,
        pitches_deg=PITCHES_DEG,
        length=LENGTH,
        attic=attic,
        costs=COSTS,
        overhang_eave=OVERHANG_EAVE,
        overhang_gable=OVERHANG_GABLE,
    )
    print(
        f"h_min = {H_MIN} m (assumption), roof at {COSTS.eur_per_m2:g} EUR/m2 all-in\n"
    )
    print(table.round(2).to_string(index=False))

    if args.csv_path is not None:
        to_csv.write_csv(table, args.csv_path)
        print(f"\nwrote {args.csv_path}")

    if args.html is not None:
        to_html.write_html(
            table,
            length=LENGTH,
            attic=attic,
            costs=COSTS,
            overhang_eave=OVERHANG_EAVE,
            overhang_gable=OVERHANG_GABLE,
            path=args.html,
        )
        print(f"wrote {args.html}")
