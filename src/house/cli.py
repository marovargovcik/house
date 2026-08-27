"""Entry point for the Module 1 sweep (`docs/spec.md` §3): width by pitch.

The imperative shell — it reads the inputs, calls the pure core, and prints.

**Every input is required.** A default here would be the same failure the core
already refuses: `AtticSpec` takes `h_min` and both build-ups with no defaults by
decision (`docs/decisions.md`) so an unverified number cannot reach a result
unannounced, and a default in the entry point would put it back one layer out.
So every figure in a report is one somebody typed on the day.

There are no exceptions. `--collar` is required too, with 0 meaning "no collar
tie" — the one place a value stands in for absence, because a flag cannot be both
required and omitted. `core.specs.collar_from_input` does the translation — the
browser build accepts 0 for the same thing, so the rule lives in one place rather
than in each entry point. `AtticSpec` keeps `float | None`, since absence
genuinely is not a height, and it still rejects a collar sitting at or below the
wall top.

`README.md` holds the invocation for the design as it currently stands, and the
reasoning behind each of those numbers is in `docs/spec.md` and
`docs/decisions.md` — not here, where it would rot next to a value nobody reads.
"""

import argparse
from pathlib import Path

from house.core import sweep, validate
from house.core.specs import AtticSpec, CostSpec, collar_from_input
from house.interpreters import to_csv, to_html, to_text


def build_parser() -> argparse.ArgumentParser:
    """Every sweep input as a required flag. See the module docstring."""
    parser = argparse.ArgumentParser(
        description="Roof and attic sweep over width and pitch. "
        "Every input is required — see README.md for the current design.",
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

    footprint = parser.add_argument_group("footprint (required)")
    footprint.add_argument(
        "--widths", type=float, nargs="+", required=True, help="metres, swept"
    )
    footprint.add_argument("--length", type=float, required=True, help="metres")
    footprint.add_argument(
        "--pitches", type=float, nargs="+", required=True, help="degrees, swept"
    )
    footprint.add_argument(
        "--overhang-eave",
        type=float,
        required=True,
        help="odkvapový presah, horizontal projection in metres",
    )
    footprint.add_argument(
        "--overhang-gable",
        type=float,
        required=True,
        help="štítový presah, horizontal projection in metres",
    )

    headroom = parser.add_argument_group("headroom, in metres (required)")
    headroom.add_argument(
        "--h-min", type=float, required=True, help="minimum clear standing height"
    )
    headroom.add_argument(
        "--roof-buildup",
        type=float,
        required=True,
        help="perpendicular to the roof plane: krokvy, insulation, lining",
    )
    headroom.add_argument(
        "--floor-buildup",
        type=float,
        required=True,
        help="vertical, above the wall top",
    )
    headroom.add_argument(
        "--knee", type=float, required=True, help="nadmurovka height; 0 for none"
    )
    headroom.add_argument(
        "--collar",
        type=float,
        required=True,
        help="klieština underside above the wall top; 0 for a roof with no "
        "collar tie. Below h_min + floor build-up it rules the attic out entirely",
    )

    parser.add_argument(
        "--eur-per-m2",
        type=float,
        required=True,
        help="all-in roof rate per m² of roof surface",
    )
    return parser


def main() -> None:
    """Print the sweep; optionally write it as CSV and as a drawn HTML report."""
    parser = build_parser()
    args = parser.parse_args()

    collar = collar_from_input(args.collar)

    # Validation is the whole of the boundary, and it runs before anything is
    # swept: the spec constructors reject a field that is nonsense on its own,
    # and `validate` reports the combinations no single spec can see. Both
    # surface as `parser.error` — exit 2 with the message — rather than a
    # traceback. Past this point the inputs are trusted.
    try:
        attic = AtticSpec(
            h_min=args.h_min,
            roof_buildup=args.roof_buildup,
            floor_buildup=args.floor_buildup,
            knee_height=args.knee,
            collar_above_wall_top=collar,
        )
        costs = CostSpec(eur_per_m2=args.eur_per_m2)
        problems = validate.sweep_problems(
            widths=args.widths,
            pitches_deg=args.pitches,
            length=args.length,
            attic=attic,
            overhang_eave=args.overhang_eave,
            overhang_gable=args.overhang_gable,
        )
    except ValueError as invalid:
        parser.error(str(invalid))
    if problems:
        parser.error("; ".join(problems))

    rows = sweep.width_by_pitch(
        widths=args.widths,
        pitches_deg=args.pitches,
        length=args.length,
        attic=attic,
        costs=costs,
        overhang_eave=args.overhang_eave,
        overhang_gable=args.overhang_gable,
    )

    print(f"h_min = {attic.h_min:g} m, roof at {costs.eur_per_m2:g} EUR/m2 all-in\n")
    print(to_text.render_table(rows))

    if args.csv_path is not None:
        to_csv.write_csv(rows, args.csv_path)
        print(f"\nwrote {args.csv_path}")

    if args.html is not None:
        to_html.write_html(
            rows,
            length=args.length,
            attic=attic,
            costs=costs,
            overhang_eave=args.overhang_eave,
            overhang_gable=args.overhang_gable,
            path=args.html,
        )
        print(f"wrote {args.html}")
