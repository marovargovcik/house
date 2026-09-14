"""The summary printed to the terminal."""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from terrain.core.boundary import Side
from terrain.core.house import Corner, HouseSpec, ShedSpec, TerraceSpec
from terrain.core.profile import END, START, Profile


@dataclass(frozen=True, slots=True)
class Clearance:
    side: Side
    house: float
    shed: float


def _profile_lines(line: Profile) -> list[str]:
    first, last = line.sections[0].start, line.sections[-1].end
    overall = math.degrees(math.atan2(last.z - first.z, last.distance))
    return [
        f"Slope {line.offset:g} m beside the line from point {START} to {END}:",
        *(
            f"  {s.start.distance:5.1f} - {s.end.distance:5.1f} m   "
            f"{s.start.z:.2f} -> {s.end.z:.2f} m   "
            f"{s.rise:+.2f} m   {s.slope_deg:4.1f}°"
            for s in line.sections
        ),
        (f"  overall {last.distance:.1f} m, {last.z - first.z:+.2f} m, {overall:.1f}°"),
        "",
    ]


def _corner_lines(corners: Sequence[Corner]) -> list[str]:
    return [
        "  ground at the corners against the floor there (+ is ground above it):",
        *(
            f"    {c.name:<19} ground {c.ground:.2f}   floor {c.floor:.2f}   "
            f"{c.depth:+.2f} m"
            for c in corners
        ),
    ]


def _house_lines(spec: HouseSpec, corners: Sequence[Corner]) -> list[str]:
    return [
        (
            f"House {spec.length:g} x {spec.width:g} m, front wall {spec.start:g} m "
            f"up the slope lines, centre {spec.offset:g} m beside the first:"
        ),
        (
            f"  garage floor {spec.garage_floor:.2f}, upper floor "
            f"{spec.upper_floor:.2f}, wall top {spec.wall_top:.2f}, "
            f"ridge {spec.ridge:.2f}"
        ),
        *_corner_lines(corners),
        "",
    ]


def _shed_lines(
    spec: ShedSpec, corners: Sequence[Corner], from_house: float
) -> list[str]:
    return [
        (
            f"Garden shed {spec.length:g} x {spec.depth:g} m, front wall "
            f"{spec.start:g} m up the slope lines, {from_house:.2f} m from the house:"
        ),
        f"  floor {spec.floor:.2f}, top {spec.floor + spec.height:.2f}",
        *_corner_lines(corners),
        "",
    ]


def _terrace_lines(
    spec: TerraceSpec, level: float, corners: Sequence[Corner]
) -> list[str]:
    return [
        (
            f"Terrace {spec.length:g} x {spec.width:g} m along the house's south "
            f"wall, {spec.from_back:g} m short of its back wall, level {level:.2f}:"
        ),
        *_corner_lines(corners),
        "",
    ]


def _flag(distance: float, limit: float) -> str:
    return f" < {limit:g}!" if distance < limit else "      "


def _side_lines(
    clearances: Sequence[Clearance],
    house_limit: float,
    shed_limit: float,
    inside: bool,
) -> list[str]:
    return [
        "Plot sides, as on a map, and the distance to each:",
        *(
            f"  {c.side.start:>3} -> {c.side.end:<3}  {c.side.length:5.1f} m   "
            f"house {c.house:5.2f} m{_flag(c.house, house_limit)}   "
            f"shed {c.shed:5.2f} m{_flag(c.shed, shed_limit)}"
            for c in clearances
        ),
        *([] if inside else ["  a building or the terrace crosses the boundary"]),
    ]


def render_summary(
    profiles: Sequence[Profile],
    house: tuple[HouseSpec, Sequence[Corner]],
    shed: tuple[ShedSpec, Sequence[Corner], float],
    terrace: tuple[TerraceSpec, float, Sequence[Corner]],
    clearances: Sequence[Clearance],
    limits: tuple[float, float],
    inside: bool,
    area: float,
) -> str:
    return "\n".join(
        [
            *(text for line in profiles for text in _profile_lines(line)),
            *_house_lines(*house),
            *_shed_lines(*shed),
            *_terrace_lines(*terrace),
            *_side_lines(clearances, *limits, inside),
            f"  area {area:.0f} m²",
        ]
    )
