"""Survey → a self-contained HTML page with a 3D view to rotate."""

from collections.abc import Iterable, Sequence
from pathlib import Path

import plotly.graph_objects as go

from terrain.core import features, views
from terrain.core.boundary import Setback, Side
from terrain.core.ground import Triangle
from terrain.core.house import Solid
from terrain.core.profile import Profile
from terrain.core.survey import Point
from terrain.core.views import Vertex

BOUNDARY_COLOR = "#e8590c"
SETBACK_COLOR = "#e03131"
PROFILE_COLOR = "#1c7ed6"
COMPASS_COLOR = "#868e96"
COMPASS = "svetové strany"


def _lines(
    name: str,
    color: str,
    width: float,
    lines: Iterable[Sequence[Vertex]],
    dash: str = "solid",
) -> go.Scatter3d:
    # `None` breaks the trace between lines.
    xs: list[float | None] = []
    ys: list[float | None] = []
    zs: list[float | None] = []
    for line in lines:
        for x, y, z in line:
            xs.append(x)
            ys.append(y)
            zs.append(z)
        xs.append(None)
        ys.append(None)
        zs.append(None)
    return go.Scatter3d(
        x=xs,
        y=ys,
        z=zs,
        mode="lines",
        name=name,
        line={"color": color, "width": width, "dash": dash},
        hoverinfo="skip",
    )


def _labels(
    name: str, color: str, at: Sequence[Vertex], texts: Sequence[str]
) -> go.Scatter3d:
    return go.Scatter3d(
        x=[x for x, _, _ in at],
        y=[y for _, y, _ in at],
        z=[z for _, _, z in at],
        mode="text",
        name=name,
        text=list(texts),
        textfont={"size": 13, "color": color},
        hoverinfo="skip",
    )


def _mesh(name: str, color: str, solid: Solid) -> go.Mesh3d:
    return go.Mesh3d(
        x=[x for x, _, _ in solid.vertices],
        y=[y for _, y, _ in solid.vertices],
        z=[z for _, _, z in solid.vertices],
        i=[i for i, _, _ in solid.faces],
        j=[j for _, j, _ in solid.faces],
        k=[k for _, _, k in solid.faces],
        color=color,
        flatshading=True,
        name=name,
        showlegend=True,
        hoverinfo="name",
    )


def _compass(points: Sequence[Point]) -> list[go.Scatter3d | go.Cone]:
    c = views.compass(points)
    labels = _labels(
        COMPASS,
        COMPASS_COLOR,
        (c.north, c.south, c.east, c.west),
        ("SEVER", "JUH", "VÝCHOD", "ZÁPAD"),
    )
    labels.update(textposition="top center", legendgroup=COMPASS)
    shaft = _lines(COMPASS, COMPASS_COLOR, 3, [(c.arrow_tail, c.north)])
    shaft.update(legendgroup=COMPASS, showlegend=False)
    head = go.Cone(
        x=[c.north[0]],
        y=[c.north[1]],
        z=[c.north[2]],
        u=[0.0],
        v=[1.0],
        w=[0.0],
        anchor="tip",
        sizemode="absolute",
        sizeref=1.0,
        colorscale=[[0, COMPASS_COLOR], [1, COMPASS_COLOR]],
        showscale=False,
        name=COMPASS,
        legendgroup=COMPASS,
        showlegend=False,
        hoverinfo="skip",
    )
    return [labels, shaft, head]


def _house(solids: Sequence[Solid]) -> list[go.Mesh3d]:
    looks = (
        ("garáž a sklad", "#868e96"),
        ("obytné poschodie", "#f1f3f5"),
        ("strecha", "#b03a2e"),
    )
    return [
        _mesh(name, color, solid)
        for (name, color), solid in zip(looks, solids, strict=True)
    ]


def _profile(line: Profile) -> list[go.Scatter3d]:
    name = f"profil +{line.offset:g} m"
    samples = [line.sections[0].start, *(s.end for s in line.sections)]
    track = go.Scatter3d(
        x=[s.x for s in samples],
        y=[s.y for s in samples],
        z=[z for _, _, z in views.above(samples, 0.3)],
        mode="lines+markers",
        name=name,
        legendgroup=name,
        line={"color": PROFILE_COLOR, "width": 6},
        marker={"size": 3, "color": PROFILE_COLOR},
        text=[f"{s.distance:.1f} m od začiatku: {s.z:.2f} m" for s in samples],
        hoverinfo="text",
    )
    slopes = _labels(
        name,
        PROFILE_COLOR,
        [views.midpoint(s.start, s.end, 1.0) for s in line.sections],
        [f"{s.slope_deg:.1f}°" for s in line.sections],
    )
    slopes.update(legendgroup=name, showlegend=False)
    return [track, slopes]


def render_html(
    points: Sequence[Point],
    triangles: Sequence[Triangle],
    profiles: Sequence[Profile],
    solids: Sequence[Solid],
    shed: Solid,
    terrace: Solid,
    sides: Sequence[Side],
    setbacks: Sequence[Setback],
    area: float,
    exaggeration: float,
) -> str:
    numbered = views.by_number(points)
    highest = max(z for solid in (*solids, shed, terrace) for _, _, z in solid.vertices)
    box = views.extent(points, highest)
    x_ratio, y_ratio, z_ratio = views.aspect(box, exaggeration)
    fence_points = sorted({n for fence in features.FENCES for n in fence})
    shed_ring = (*features.EXISTING_SHED, features.EXISTING_SHED[0])
    boundary_ring = (*features.BOUNDARY, features.BOUNDARY[0])
    xs = [p.x for p in points]
    ys = [p.y for p in points]
    zs = [p.z for p in points]

    figure = go.Figure(
        data=[
            go.Mesh3d(
                x=xs,
                y=ys,
                z=zs,
                i=[i for i, _, _ in triangles],
                j=[j for _, j, _ in triangles],
                k=[k for _, _, k in triangles],
                intensity=zs,
                colorscale="Earth",
                showscale=False,
                flatshading=True,
                name="terén",
                hoverinfo="skip",
            ),
            *_house(solids),
            _mesh("záhradný sklad", "#a0703c", shed),
            _mesh("terasa", "#c9a26b", terrace),
            *_compass(points),
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers",
                name="body merania",
                marker={"size": 2, "color": "#171b19"},
                text=[f"bod {p.number}: {p.z:.2f} m" for p in points],
                hoverinfo="text",
            ),
            _lines(
                "plot",
                "#5b4636",
                4,
                [
                    *(
                        views.raised(numbered, fence, views.FENCE_HEIGHT)
                        for fence in features.FENCES
                    ),
                    *views.posts(numbered, fence_points, views.FENCE_HEIGHT),
                ],
            ),
            _lines(
                "stromy",
                "#2f7d3b",
                6,
                views.posts(numbered, features.TREES, views.TREE_HEIGHT),
            ),
            _lines(
                "sklad",
                "#6b6f73",
                5,
                [
                    views.raised(numbered, shed_ring, 0.0),
                    views.raised(numbered, shed_ring, views.SHED_HEIGHT),
                    *views.posts(numbered, features.EXISTING_SHED, views.SHED_HEIGHT),
                ],
            ),
            _lines(
                "hranica parcely",
                BOUNDARY_COLOR,
                3,
                [views.raised(numbered, boundary_ring, 0.2)],
            ),
            _labels(
                "rozmery",
                BOUNDARY_COLOR,
                [
                    views.midpoint(numbered[s.start], numbered[s.end], 2.0)
                    for s in sides
                ],
                [f"{s.length:.1f} m" for s in sides],
            ),
            _lines(
                "odstup od hranice (min.)",
                SETBACK_COLOR,
                3,
                [views.above(sb.limit_line, 0.15) for sb in setbacks],
                dash="dash",
            ),
            _lines(
                "vzdialenosť od hranice",
                SETBACK_COLOR,
                6,
                [views.above(sb.measure, 0.15) for sb in setbacks if sb.measure],
            ),
            _labels(
                "odstupy",
                SETBACK_COLOR,
                [
                    *(
                        views.midpoint(sb.measure[0], sb.measure[-1], 0.8)
                        for sb in setbacks
                        if sb.measure
                    ),
                    *(
                        views.midpoint(sb.limit_line[0], sb.limit_line[-1], 0.8)
                        for sb in setbacks
                    ),
                ],
                [
                    *(f"{sb.gap:.2f} m" for sb in setbacks if sb.measure),
                    *(f"min. {sb.limit:g} m" for sb in setbacks),
                ],
            ),
            *(trace for line in profiles for trace in _profile(line)),
        ],
        layout={
            "title": f"Parcela 1561/1 — terén, {area:.0f} m²",
            "margin": {"l": 0, "r": 0, "t": 40, "b": 0},
            "scene": {
                "aspectmode": "manual",
                "aspectratio": {"x": x_ratio, "y": y_ratio, "z": z_ratio},
                "xaxis": {"title": "", "range": list(box.x)},
                "yaxis": {"title": "", "range": list(box.y)},
                "zaxis": {"title": "výška (m n. m.)", "range": list(box.z)},
            },
        },
    )
    return str(figure.to_html(include_plotlyjs=True, full_html=True))


def write_html(
    points: Sequence[Point],
    triangles: Sequence[Triangle],
    profiles: Sequence[Profile],
    solids: Sequence[Solid],
    shed: Solid,
    terrace: Solid,
    sides: Sequence[Side],
    setbacks: Sequence[Setback],
    area: float,
    exaggeration: float,
    path: Path,
) -> None:
    path.write_text(
        render_html(
            points,
            triangles,
            profiles,
            solids,
            shed,
            terrace,
            sides,
            setbacks,
            area,
            exaggeration,
        ),
        encoding="utf-8",
    )
