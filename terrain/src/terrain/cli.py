"""Entry point: survey file -> printed summary and a 3D page."""

import argparse
from pathlib import Path

from terrain.core import (
    boundary,
    excavation,
    features,
    ground,
    house,
    profile,
    survey,
    views,
)
from terrain.interpreters import to_html, to_text

HOUSE_FLAGS = (
    ("--house-start", "front wall, metres up the slope lines"),
    ("--house-offset", "centre line, metres beside the first slope line"),
    ("--house-length", "metres along the slope"),
    ("--house-width", "metres across the slope"),
    ("--lower-depth", "garage level, metres back from the front wall"),
    ("--garage-floor", "metres above sea level"),
    ("--lower-height", "metres from the garage floor to the upper floor"),
    ("--upper-height", "metres from the upper floor to the wall top"),
    ("--pitch", "roof pitch in degrees"),
    ("--boundary-gap", "least distance from the house to the plot boundary"),
)

SHED_FLAGS = (
    ("--shed-start", "front wall, metres up the slope lines"),
    ("--shed-offset", "centre, metres beside the first slope line"),
    ("--shed-depth", "metres along the slope"),
    ("--shed-length", "metres across the slope"),
    ("--shed-floor", "metres above sea level"),
    ("--shed-height", "metres from its floor to its top"),
    ("--shed-boundary-gap", "least distance from the shed to the plot boundary"),
)

TERRACE_FLAGS = (
    ("--terrace-length", "metres along the house's south wall"),
    ("--terrace-width", "metres out from the wall"),
    ("--terrace-from-back", "metres short of the house's back wall"),
)

DIG_FLAGS = (
    ("--floor-buildup", "metres from a finished floor to the gravel's bottom"),
    ("--footing-width", "metres"),
    ("--footing-depth", "metres below the gravel's bottom"),
    ("--working-space", "metres dug beyond buried walls"),
)

LAYOUT = r"""
the layout being tried now, run from terrain/:

  uv run view ../data/terrain.txt terrain.html --exaggeration 1 --section 5 \
    --house-start 15 --house-offset 7 --house-length 25 --house-width 10 \
    --lower-depth 9 --garage-floor 270.2 --lower-height 3.0 --upper-height 2.8 \
    --pitch 25 --boundary-gap 2.5 \
    --shed-start 40 --shed-offset 7 --shed-depth 2.8 --shed-length 10 \
    --shed-floor 273.2 --shed-height 2.5 --shed-boundary-gap 2 \
    --terrace-length 7 --terrace-width 3 --terrace-from-back 1 \
    --floor-buildup 0.5 --footing-width 0.6 --footing-depth 0.8 --working-space 0.8
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="3D view of the surveyed plot.",
        epilog=LAYOUT,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("survey", type=Path, help="the point list, data/terrain.txt")
    parser.add_argument("html", type=Path, help="write the page here")
    parser.add_argument(
        "--exaggeration",
        type=float,
        required=True,
        help="how much to stretch heights on screen; 1 for true scale",
    )
    parser.add_argument(
        "--section",
        type=float,
        required=True,
        help="length of each slope section, in metres",
    )
    for title, flags in (
        ("house (required)", HOUSE_FLAGS),
        ("garden shed (required)", SHED_FLAGS),
        ("terrace (required)", TERRACE_FLAGS),
        ("excavation (required)", DIG_FLAGS),
    ):
        group = parser.add_argument_group(title)
        for flag, help_text in flags:
            group.add_argument(flag, type=float, required=True, help=help_text)
    args = parser.parse_args()
    if not args.exaggeration > 0:
        parser.error(f"exaggeration must be positive, got {args.exaggeration}")
    if not args.section > 0:
        parser.error(f"section must be positive, got {args.section}")

    try:
        house_spec = house.HouseSpec(
            start=args.house_start,
            offset=args.house_offset,
            length=args.house_length,
            width=args.house_width,
            lower_depth=args.lower_depth,
            garage_floor=args.garage_floor,
            lower_height=args.lower_height,
            upper_height=args.upper_height,
            pitch_deg=args.pitch,
        )
        shed_spec = house.ShedSpec(
            start=args.shed_start,
            offset=args.shed_offset,
            depth=args.shed_depth,
            length=args.shed_length,
            floor=args.shed_floor,
            height=args.shed_height,
        )
        terrace_spec = house.TerraceSpec(
            length=args.terrace_length,
            width=args.terrace_width,
            from_back=args.terrace_from_back,
        )
        dig_spec = excavation.DigSpec(
            floor_buildup=args.floor_buildup,
            footing_width=args.footing_width,
            footing_depth=args.footing_depth,
            working_space=args.working_space,
        )
    except ValueError as invalid:
        parser.error(str(invalid))

    points = survey.parse(args.survey.read_text(encoding="utf-8"))
    numbered = views.by_number(points)
    mesh = ground.triangles(points)
    first, last = numbered[profile.START], numbered[profile.END]
    start, end = (first.x, first.y), (last.x, last.y)
    profiles = [
        profile.Profile(
            offset=offset,
            sections=profile.sections(
                profile.samples(
                    points, mesh, *profile.shifted(start, end, offset), args.section
                )
            ),
        )
        for offset in profile.OFFSETS
    ]
    house_outline = house.footprint(start, end, house_spec, house_spec.length)
    shed_outline = house.shed_outline(start, end, shed_spec)
    terrace_outline = house.terrace_outline(start, end, house_spec, terrace_spec)

    sides = boundary.sides(numbered, features.BOUNDARY)
    area = boundary.area(numbered, features.BOUNDARY)
    ring = [(numbered[n].x, numbered[n].y) for n in features.BOUNDARY]

    def side_ends(side: boundary.Side) -> tuple[profile.Position, profile.Position]:
        a, b = numbered[side.start], numbered[side.end]
        return (a.x, a.y), (b.x, b.y)

    clearances = [
        to_text.Clearance(
            side=side,
            house=boundary.gap(*side_ends(side), house_outline),
            shed=boundary.gap(*side_ends(side), shed_outline),
        )
        for side in sides
    ]
    inside = all(
        boundary.contains(ring, corner)
        for corner in (*house_outline, *shed_outline, *terrace_outline)
    )
    # Drawn only on the side each building is nearest to.
    house_side = min(clearances, key=lambda c: c.house).side
    shed_side = min(clearances, key=lambda c: c.shed).side

    try:
        house_corners = house.corners(points, mesh, start, end, house_spec)
        shed_corners = house.outline_corners(
            points, mesh, "shed", shed_outline, shed_spec.floor
        )
        terrace_corners = house.outline_corners(
            points, mesh, "terrace", terrace_outline, house_spec.upper_floor
        )
        pits = excavation.pits(
            points, mesh, start, end, house_spec, shed_spec, dig_spec, excavation.CELL
        )
        setbacks = [
            boundary.setback(
                points,
                mesh,
                *side_ends(house_side),
                house_outline,
                args.boundary_gap,
                views.LINE_STEP,
            ),
            boundary.setback(
                points,
                mesh,
                *side_ends(shed_side),
                shed_outline,
                args.shed_boundary_gap,
                views.LINE_STEP,
            ),
        ]
    except ValueError as invalid:
        parser.error(str(invalid))

    print(
        to_text.render_summary(
            profiles,
            (house_spec, house_corners),
            (
                shed_spec,
                shed_corners,
                boundary.outline_gap(shed_outline, house_outline),
            ),
            (terrace_spec, house_spec.upper_floor, terrace_corners),
            pits,
            clearances,
            (args.boundary_gap, args.shed_boundary_gap),
            inside,
            area,
        )
    )
    to_html.write_html(
        points,
        mesh,
        profiles,
        house.solids(start, end, house_spec),
        house.shed_solid(shed_outline, shed_spec),
        house.terrace_solid(terrace_outline, house_spec),
        sides,
        setbacks,
        area,
        args.exaggeration,
        args.html,
    )
    print(f"\nwrote {args.html}")
