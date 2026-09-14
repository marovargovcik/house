"""Roof views → SVG strings.

Every card uses the same `SCALE` at natural size, never fit-to-box, so sizes and
pitches compare by eye.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass

from roof.core import attic as attic_calc
from roof.core import views
from roof.core.specs import AtticSpec, HouseSpec, RoofSpec
from roof.core.views import Point, Rect
from roof.interpreters import sk

SCALE = 26.0
"""Pixels per metre, shared by every card."""

_TICK = 0.13
"""Half-length of a dimension line's end tick, in metres."""

_ARC_RADIUS = 0.9
"""Radius of the pitch-angle arc, in metres."""

_LABEL_CLEARANCE = 0.5
"""Metres between the pitch label and its rafter; shallow pitches push it out."""


@dataclass(frozen=True, slots=True)
class _Frame:
    """Metres → pixels for one panel. `y` flips: metres go up, pixels go down."""

    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def px(self, p: Point) -> tuple[float, float]:
        return ((p.x - self.x_min) * SCALE, (self.y_max - p.y) * SCALE)

    @property
    def width_px(self) -> float:
        return (self.x_max - self.x_min) * SCALE

    @property
    def height_px(self) -> float:
        return (self.y_max - self.y_min) * SCALE


def _line(f: _Frame, a: Point, b: Point, cls: str, arrows: bool = False) -> str:
    x1, y1 = f.px(a)
    x2, y2 = f.px(b)
    marks = ' marker-start="url(#arrow)" marker-end="url(#arrow)"' if arrows else ""
    return (
        f'<line class="{cls}" x1="{x1:.1f}" y1="{y1:.1f}" '
        f'x2="{x2:.1f}" y2="{y2:.1f}"{marks}/>'
    )


def _points(f: _Frame, points: Sequence[Point]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in (f.px(p) for p in points))


def _polyline(f: _Frame, points: Sequence[Point], cls: str) -> str:
    return f'<polyline class="{cls}" points="{_points(f, points)}"/>'


def _polygon(f: _Frame, points: Sequence[Point], cls: str) -> str:
    return f'<polygon class="{cls}" points="{_points(f, points)}"/>'


def _rect(f: _Frame, r: Rect, cls: str) -> str:
    x, y = f.px(Point(r.x_min, r.y_max))
    w = (r.x_max - r.x_min) * SCALE
    h = (r.y_max - r.y_min) * SCALE
    return f'<rect class="{cls}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"/>'


def _text(
    f: _Frame,
    at: Point,
    label: str,
    cls: str,
    dx: float = 0.0,
    dy: float = 0.0,
    turned: bool = False,
) -> str:
    x, y = f.px(at)
    x += dx
    y += dy
    turn = f' transform="rotate(-90 {x:.1f} {y:.1f})"' if turned else ""
    return f'<text class="{cls}" x="{x:.1f}" y="{y:.1f}"{turn}>{label}</text>'


def _dim_h(f: _Frame, x0: float, x1: float, y: float, label: str) -> str:
    """Horizontal dimension line with end ticks and a label above it."""
    return "".join(
        (
            _line(f, Point(x0, y), Point(x1, y), "dim", arrows=True),
            _line(f, Point(x0, y - _TICK), Point(x0, y + _TICK), "dim"),
            _line(f, Point(x1, y - _TICK), Point(x1, y + _TICK), "dim"),
            _text(f, Point((x0 + x1) / 2, y), label, "dim-label", dy=-5.0),
        )
    )


def _dim_v(f: _Frame, y0: float, y1: float, x: float, label: str) -> str:
    """Vertical dimension line; the label is turned, as on a drafted section."""
    return "".join(
        (
            _line(f, Point(x, y0), Point(x, y1), "dim", arrows=True),
            _line(f, Point(x - _TICK, y0), Point(x + _TICK, y0), "dim"),
            _line(f, Point(x - _TICK, y1), Point(x + _TICK, y1), "dim"),
            _text(f, Point(x, (y0 + y1) / 2), label, "dim-label", dx=-5.0, turned=True),
        )
    )


def _pitch_arc(f: _Frame, spring: Point, pitch_deg: float) -> str:
    """Pitch angle at the right eave; the left has the overhang dimension."""
    theta = math.radians(pitch_deg)
    start = Point(spring.x - _ARC_RADIUS, spring.y)
    end = Point(
        spring.x - _ARC_RADIUS * math.cos(theta),
        spring.y + _ARC_RADIUS * math.sin(theta),
    )
    sx, sy = f.px(start)
    ex, ey = f.px(end)
    r = _ARC_RADIUS * SCALE
    reach = min(3.0, _LABEL_CLEARANCE / math.sin(theta / 2))
    label_at = Point(
        spring.x - reach * math.cos(theta / 2),
        spring.y + reach * math.sin(theta / 2),
    )
    return "".join(
        (
            _line(f, spring, start, "ref"),
            (
                f'<path class="arc" d="M{sx:.1f},{sy:.1f} '
                f'A{r:.1f},{r:.1f} 0 0 1 {ex:.1f},{ey:.1f}"/>'
            ),
            _text(f, label_at, f"{sk.trimmed(pitch_deg)}°", "angle-label", dy=4.0),
        )
    )


def _section_panel(
    house: HouseSpec, roof: RoofSpec, attic: AtticSpec
) -> tuple[_Frame, str]:
    sec = views.section(house, roof, attic)
    half_width = house.width / 2
    eave_x = sec.eave_outer[1].x
    floor_y = sec.floor[0].y
    ceiling_apex = sec.ceiling[1]
    # From the core, so it stops at a collar and matches `clear_ridge_m`.
    clear_ridge = attic_calc.clear_ridge_height(house, roof, attic)
    frame = _Frame(
        x_min=-eave_x - 2.7,
        x_max=eave_x + 1.9,
        y_min=min(0.0, sec.eave_outer[0].y) - 2.5,
        y_max=max(sec.apex.y, floor_y + attic.h_min) + 0.9,
    )

    parts = []
    if sec.standing_room is not None:
        parts.append(_polygon(frame, sec.standing_room, "usable"))
    parts += [
        # Roof plane to ceiling: the headroom the build-up takes.
        _polygon(
            frame,
            (
                sec.knee_top[0],
                sec.apex,
                sec.knee_top[1],
                sec.ceiling[2],
                ceiling_apex,
                sec.ceiling[0],
            ),
            "buildup",
        ),
        _rect(frame, Rect(-half_width, 0.0, half_width, floor_y), "buildup"),
        _line(frame, Point(-eave_x - 0.4, 0.0), Point(eave_x + 0.4, 0.0), "datum"),
        _line(frame, sec.knee_top[0], sec.apex, "roof"),
        _line(frame, sec.knee_top[1], sec.apex, "roof"),
        _line(frame, sec.knee_top[0], sec.eave_outer[0], "roof overhang"),
        _line(frame, sec.knee_top[1], sec.eave_outer[1], "roof overhang"),
        _polyline(frame, sec.ceiling, "ceiling"),
        _line(frame, sec.floor[0], sec.floor[1], "floor"),
        # Drawn even above the apex: that shows why the attic is unusable.
        _line(
            frame,
            Point(-half_width, floor_y + attic.h_min),
            Point(half_width, floor_y + attic.h_min),
            "headroom",
        ),
        _text(
            frame,
            Point(-half_width, floor_y + attic.h_min),
            f"h_min {sk.trimmed(attic.h_min)}",
            "note end",
            dx=-6.0,
            dy=-4.0,
        ),
        _pitch_arc(frame, sec.knee_top[1], roof.pitch_deg),
        _text(frame, sec.apex, "hrebeň", "note mid", dy=-8.0),
        _dim_v(
            frame, 0.0, sec.apex.y, eave_x + 1.0, f"hrebeň {sk.trimmed(sec.apex.y)} m"
        ),
        _dim_v(
            frame,
            floor_y,
            floor_y + clear_ridge,
            -eave_x - 1.7,
            f"svetlá {sk.trimmed(clear_ridge)} m",
        ),
        _dim_h(
            frame, -half_width, half_width, -1.3, f"šírka {sk.trimmed(house.width)} m"
        ),
    ]
    if roof.overhang_eave > 0:
        parts.append(
            _dim_h(
                frame,
                -eave_x,
                -half_width,
                -0.6,
                f"odkvap {sk.trimmed(roof.overhang_eave)}",
            )
        )
    if attic.knee_height > 0:
        parts += [
            _line(frame, sec.wall_top[0], sec.knee_top[0], "knee"),
            _line(frame, sec.wall_top[1], sec.knee_top[1], "knee"),
            _text(frame, sec.knee_top[0], "nadmurovka", "note end", dx=-7.0),
        ]
    if sec.collar is not None:
        parts += [
            _line(frame, sec.collar[0], sec.collar[1], "collar"),
            _text(frame, sec.collar[1], "klieština", "note", dx=6.0, dy=-4.0),
        ]
    if sec.headroom_line is not None:
        left, right = sec.headroom_line
        parts.append(
            _dim_h(
                frame,
                left.x,
                right.x,
                -2.0,
                f"úžitková {sk.trimmed(right.x - left.x)} m",
            )
        )
    else:
        parts.append(
            _text(
                frame,
                Point(0.0, -2.0),
                f"nikde nie je výška {sk.trimmed(attic.h_min)} m",
                "dim-label",
            )
        )
    return frame, "".join(parts)


def _plan_panel(
    house: HouseSpec, roof: RoofSpec, attic: AtticSpec
) -> tuple[_Frame, str]:
    pl = views.plan(house, roof, attic)
    outline = pl.roof_outline
    frame = _Frame(
        x_min=outline.x_min - 1.3,
        x_max=outline.x_max + 1.3,
        y_min=outline.y_min - 1.4,
        y_max=outline.y_max + 0.9,
    )

    parts = [
        _rect(frame, outline, "roof-outline"),
        _rect(frame, pl.walls, "walls"),
    ]
    if pl.usable_strip is not None:
        parts.append(_rect(frame, pl.usable_strip, "usable"))
    parts += [
        _line(frame, pl.ridge[0], pl.ridge[1], "ridge"),
        _dim_h(
            frame,
            pl.walls.x_min,
            pl.walls.x_max,
            outline.y_min - 0.75,
            f"dĺžka {sk.trimmed(house.length)} m",
        ),
        _dim_v(
            frame,
            pl.walls.y_min,
            pl.walls.y_max,
            outline.x_min - 0.75,
            f"šírka {sk.trimmed(house.width)} m",
        ),
    ]
    if roof.overhang_gable > 0:
        parts.append(
            _dim_h(
                frame,
                pl.walls.x_max,
                outline.x_max,
                outline.y_max + 0.35,
                f"štít {sk.trimmed(roof.overhang_gable)}",
            )
        )
    if pl.usable_strip is not None:
        strip = pl.usable_strip
        parts.append(
            _dim_v(
                frame,
                strip.y_min,
                strip.y_max,
                outline.x_max + 0.75,
                f"úžitková {sk.trimmed(strip.y_max - strip.y_min)} m",
            )
        )
    return frame, "".join(parts)


def card_svg(house: HouseSpec, roof: RoofSpec, attic: AtticSpec) -> str:
    """Section and plan of one configuration, side by side, drawn to `SCALE`."""
    gap = 20.0
    sec_frame, sec = _section_panel(house, roof, attic)
    plan_frame, plan = _plan_panel(house, roof, attic)
    width = sec_frame.width_px + gap + plan_frame.width_px
    height = max(sec_frame.height_px, plan_frame.height_px)
    # Bottom-aligned, so ridge heights compare across a row of cards.
    return (
        f'<svg class="drawing" width="{width:.0f}" height="{height:.0f}" '
        f'viewBox="0 0 {width:.0f} {height:.0f}" '
        'xmlns="http://www.w3.org/2000/svg">'
        f'<g transform="translate(0 {height - sec_frame.height_px:.1f})">{sec}</g>'
        f'<g transform="translate({sec_frame.width_px + gap:.1f} '
        f'{height - plan_frame.height_px:.1f})">{plan}</g>'
        "</svg>"
    )


def defs_svg() -> str:
    """Arrowhead and hatch, once per page: inline SVGs share one id space."""
    return (
        '<svg class="defs" width="0" height="0" xmlns="http://www.w3.org/2000/svg">'
        "<defs>"
        '<marker id="arrow" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" '
        'markerHeight="5" orient="auto-start-reverse"><path d="M0,0 L8,4 L0,8 z"/>'
        "</marker>"
        '<pattern id="hatch" width="6" height="6" patternUnits="userSpaceOnUse" '
        'patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="6"/></pattern>'
        "</defs></svg>"
    )


STYLE = """
.drawing { overflow: visible; max-width: 100%; height: auto; }
.defs { position: absolute; }
#arrow path { fill: var(--dim); }
#hatch line { stroke: var(--usable); stroke-width: 2.5; }
/* Rules below are qualified with `.drawing` to outrank this reset; bare, the
   fills vanish. */
.drawing line, .drawing polyline, .drawing polygon, .drawing rect, .drawing path {
  fill: none; stroke-linecap: round; stroke-linejoin: round;
}
.drawing .roof { stroke: var(--roof); stroke-width: 3; }
.drawing .overhang { stroke: var(--roof); stroke-width: 3; opacity: 0.45; }
.drawing .knee { stroke: var(--roof); stroke-width: 5; }
.drawing .buildup { fill: var(--roof); fill-opacity: 0.22; stroke: none; }
.drawing .ceiling { stroke: var(--ink); stroke-width: 1.6; opacity: 0.85; }
.drawing .floor { stroke: var(--ink); stroke-width: 2.5; opacity: 0.85; }
.drawing .collar { stroke: var(--roof); stroke-width: 4; }
.drawing .datum { stroke: var(--ink); stroke-width: 1; stroke-dasharray: 7 3 2 3;
  opacity: 0.5; }
.drawing .headroom { stroke: var(--usable); stroke-width: 1.2; stroke-dasharray: 5 4; }
.drawing .usable { fill: url(#hatch); stroke: var(--usable); stroke-width: 1.2; }
.drawing .walls { stroke: var(--ink); stroke-width: 2; fill: var(--wall-fill); }
.drawing .roof-outline { stroke: var(--roof); stroke-width: 1.4; stroke-dasharray: 6 4;
  fill: var(--roof); fill-opacity: 0.06; }
.drawing .ridge { stroke: var(--roof); stroke-width: 1.6; stroke-dasharray: 9 4; }
.drawing .dim { stroke: var(--dim); stroke-width: 1; }
.drawing .ref { stroke: var(--dim); stroke-width: 1; stroke-dasharray: 3 3; }
.drawing .arc { stroke: var(--accent); stroke-width: 1.4; }
.drawing text { font: 11px ui-sans-serif, system-ui, sans-serif; fill: var(--dim); }
.drawing .dim-label { text-anchor: middle; }
.drawing .angle-label { text-anchor: middle; fill: var(--accent); font-weight: 600;
  paint-order: stroke; stroke: var(--panel); stroke-width: 3px; }
.drawing .note { font-size: 10px; fill: var(--ink); opacity: 0.8; text-anchor: start;
  paint-order: stroke; stroke: var(--panel); stroke-width: 3px; }
.drawing .note.mid { text-anchor: middle; }
.drawing .note.end { text-anchor: end; }
"""
