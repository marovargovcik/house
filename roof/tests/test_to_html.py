"""The report: one card per row, one shared scale, no external assets."""

from pathlib import Path

from roof.core import sweep
from roof.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec
from roof.interpreters import to_html, to_svg

COSTS = CostSpec(eur_per_m2=110.0)
OVERHANGS = {"overhang_eave": 0.6, "overhang_gable": 0.4}


def _rows() -> tuple[sweep.SweepRow, ...]:
    return sweep.width_by_pitch(
        widths=(9.0, 11.0),
        pitches_deg=(25.0, 45.0),
        length=10.0,
        attic=AtticSpec(
            h_min=1.9,
            roof_buildup=0.30,
            floor_buildup=0.20,
            knee_height=0.0,
            collar_above_wall_top=None,
        ),
        costs=COSTS,
        overhang_eave=0.6,
        overhang_gable=0.4,
    )


def test_report_has_a_card_per_row_and_no_external_assets(tmp_path: Path) -> None:
    rows = _rows()
    path = tmp_path / "roof.html"
    to_html.write_html(
        rows,
        length=10.0,
        attic=AtticSpec(
            h_min=1.9,
            roof_buildup=0.30,
            floor_buildup=0.20,
            knee_height=0.0,
            collar_above_wall_top=None,
        ),
        costs=COSTS,
        overhang_eave=0.6,
        overhang_gable=0.4,
        path=path,
    )
    page = path.read_text(encoding="utf-8")

    assert page.count('<figure class="card">') == 4
    # Nothing fetched. (`xmlns="http://..."` is a name, never requested.)
    assert "<link" not in page
    assert "<script" not in page
    assert "src=" not in page
    # Shared defs: exactly one copy.
    assert page.count('id="arrow"') == 1


def test_a_wider_house_is_drawn_wider_at_the_same_scale() -> None:
    """2 m wider draws exactly 2 x SCALE wider."""
    attic = AtticSpec(
        h_min=1.9,
        roof_buildup=0.30,
        floor_buildup=0.20,
        knee_height=0.0,
        collar_above_wall_top=None,
    )
    roof = RoofSpec(pitch_deg=30.0, **OVERHANGS)
    narrow = to_svg.card_svg(HouseSpec(width=9.0, length=10.0), roof, attic)
    wide = to_svg.card_svg(HouseSpec(width=11.0, length=10.0), roof, attic)

    def svg_width(markup: str) -> float:
        return float(markup.split('width="', 1)[1].split('"', 1)[0])

    assert svg_width(wide) - svg_width(narrow) == 2.0 * to_svg.SCALE


def test_a_pitch_with_no_headroom_still_renders() -> None:
    """At 15° there's no usable strip; it still draws, with a decimal comma."""
    markup = to_svg.card_svg(
        HouseSpec(width=9.0, length=10.0),
        RoofSpec(pitch_deg=15.0, **OVERHANGS),
        AtticSpec(
            h_min=1.9,
            roof_buildup=0.30,
            floor_buildup=0.20,
            knee_height=0.0,
            collar_above_wall_top=None,
        ),
    )
    assert "nikde nie je výška 1,9 m" in markup
    assert "url(#hatch)" not in markup
