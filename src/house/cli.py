"""Entry point for the Module 1 sweep (`docs/spec.md` §3): width by pitch.

The imperative shell — it picks the inputs, calls the pure core, and prints.
Every input is a flag, and the constants below are its documented defaults, so
`--help` carries the assumptions and a run with custom flags still describes
itself in the report header.

Defaults are stated here rather than hidden in the core: `AtticSpec` takes
`h_min` and both build-ups with no defaults by decision (`docs/decisions.md`),
precisely so an unverified number cannot reach a result unannounced.
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

# Clear-height allowances, both explicit assumptions until the projektant's
# section drawing lands (`docs/decisions.md`, open items). ROOF_BUILDUP is
# measured perpendicular to the roof plane — krokva, insulation, service cavity,
# and lining — so it costs more headroom the steeper the pitch.
ROOF_BUILDUP = 0.30
FLOOR_BUILDUP = 0.20

# No knee wall and no collar tie in the current design. Both are exposed anyway:
# "what would a 0.5 m nadmurovka buy me?" is the question `docs/decisions.md`
# keeps the knee parameter alive to answer, and it deserves a flag rather than an
# edit.
KNEE_HEIGHT = 0.0

# All-in roof rate: krov, insulation, membrane, battens, covering, gutters, and
# labour in one number, the way a builder quotes it (`docs/decisions.md`).
EUR_PER_M2 = 110.0


def build_parser() -> argparse.ArgumentParser:
    """Every sweep input as a flag, defaulting to the constants above."""
    parser = argparse.ArgumentParser(
        description="Roof and attic sweep over width and pitch.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
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

    footprint = parser.add_argument_group("footprint")
    footprint.add_argument(
        "--widths", type=float, nargs="+", default=list(WIDTHS), help="metres, swept"
    )
    footprint.add_argument("--length", type=float, default=LENGTH, help="metres")
    footprint.add_argument(
        "--pitches",
        type=float,
        nargs="+",
        default=list(PITCHES_DEG),
        help="degrees, swept",
    )
    footprint.add_argument(
        "--overhang-eave",
        type=float,
        default=OVERHANG_EAVE,
        help="odkvapový presah, horizontal projection in metres",
    )
    footprint.add_argument(
        "--overhang-gable",
        type=float,
        default=OVERHANG_GABLE,
        help="štítový presah, horizontal projection in metres",
    )

    headroom = parser.add_argument_group("headroom (all clear heights, metres)")
    headroom.add_argument(
        "--h-min", type=float, default=H_MIN, help="minimum standing height"
    )
    headroom.add_argument(
        "--roof-buildup",
        type=float,
        default=ROOF_BUILDUP,
        help="perpendicular to the roof plane: krokvy, insulation, lining",
    )
    headroom.add_argument(
        "--floor-buildup",
        type=float,
        default=FLOOR_BUILDUP,
        help="vertical, above the wall top",
    )
    headroom.add_argument(
        "--knee", type=float, default=KNEE_HEIGHT, help="nadmurovka height"
    )
    headroom.add_argument(
        "--collar",
        type=float,
        default=None,
        help="klieština underside above the wall top; omit for a roof with none. "
        "Below h_min + floor build-up it rules the attic out entirely",
    )

    parser.add_argument(
        "--eur-per-m2",
        type=float,
        default=EUR_PER_M2,
        help="all-in roof rate per m² of roof surface",
    )
    return parser


def main() -> None:
    """Print the sweep; optionally write it as CSV and as a drawn HTML report."""
    parser = build_parser()
    args = parser.parse_args()

    # The spec constructors are the validation boundary, so a bad flag surfaces
    # as their message rather than a traceback — `parser.error` exits 2 with it.
    try:
        attic = AtticSpec(
            h_min=args.h_min,
            roof_buildup=args.roof_buildup,
            floor_buildup=args.floor_buildup,
            knee_height=args.knee,
            collar_above_wall_top=args.collar,
        )
        costs = CostSpec(eur_per_m2=args.eur_per_m2)
        table = sweep.width_by_pitch(
            widths=args.widths,
            pitches_deg=args.pitches,
            length=args.length,
            attic=attic,
            costs=costs,
            overhang_eave=args.overhang_eave,
            overhang_gable=args.overhang_gable,
        )
    except ValueError as invalid:
        parser.error(str(invalid))

    print(
        f"h_min = {attic.h_min:g} m (assumption), "
        f"roof at {costs.eur_per_m2:g} EUR/m2 all-in\n"
    )
    print(table.round(2).to_string(index=False))

    if args.csv_path is not None:
        to_csv.write_csv(table, args.csv_path)
        print(f"\nwrote {args.csv_path}")

    if args.html is not None:
        to_html.write_html(
            table,
            length=args.length,
            attic=attic,
            costs=costs,
            overhang_eave=args.overhang_eave,
            overhang_gable=args.overhang_gable,
            path=args.html,
        )
        print(f"wrote {args.html}")
