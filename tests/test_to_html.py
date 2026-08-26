"""The report is a rendering, so it is checked for what it must not get wrong:
one card per swept row, drawn to a shared scale, and no external assets."""

from pathlib import Path

import pandas as pd

from house.core import sweep
from house.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec
from house.interpreters import to_html, to_svg

COSTS = CostSpec(eur_per_m2=110.0)


def _table() -> pd.DataFrame:
    return sweep.width_by_pitch(
        widths=(9.0, 11.0),
        pitches_deg=(25.0, 45.0),
        length=10.0,
        attic=AtticSpec(h_min=1.9, roof_buildup=0.30, floor_buildup=0.20),
        costs=COSTS,
        overhang_eave=0.6,
        overhang_gable=0.4,
    )


def test_report_has_a_card_per_row_and_no_external_assets(tmp_path: Path) -> None:
    table = _table()
    path = tmp_path / "roof.html"
    to_html.write_html(
        table,
        length=10.0,
        attic=AtticSpec(h_min=1.9, roof_buildup=0.30, floor_buildup=0.20),
        costs=COSTS,
        overhang_eave=0.6,
        overhang_gable=0.4,
        path=path,
    )
    page = path.read_text(encoding="utf-8")

    assert page.count('<figure class="card">') == 4
    # A single fetched asset would break the "open this one file" promise.
    # (`xmlns="http://..."` is a namespace name, never requested, so it stays.)
    assert "<link" not in page
    assert "<script" not in page
    assert "src=" not in page
    # The defs are shared by every inline SVG, so exactly one copy may exist.
    assert page.count('id="arrow"') == 1


def test_a_wider_house_is_drawn_wider_at_the_same_scale() -> None:
    """Comparability by eye is the reason the page exists — pin it."""
    attic = AtticSpec(h_min=1.9, roof_buildup=0.30, floor_buildup=0.20)
    roof = RoofSpec(pitch_deg=30.0)
    narrow = to_svg.card_svg(HouseSpec(width=9.0, length=10.0), roof, attic)
    wide = to_svg.card_svg(HouseSpec(width=11.0, length=10.0), roof, attic)

    def svg_width(markup: str) -> float:
        return float(markup.split('width="', 1)[1].split('"', 1)[0])

    assert svg_width(wide) - svg_width(narrow) == 2.0 * to_svg.SCALE


def test_a_pitch_with_no_headroom_still_renders() -> None:
    """The 15° case has no usable strip; it must draw, not crash or go blank.

    Also pins the decimal comma: an English-formatted 1.9 on a Slovak drawing is
    the kind of thing that survives review unnoticed.
    """
    markup = to_svg.card_svg(
        HouseSpec(width=9.0, length=10.0),
        RoofSpec(pitch_deg=15.0),
        AtticSpec(h_min=1.9, roof_buildup=0.30, floor_buildup=0.20),
    )
    assert "nikde nie je výška 1,9 m" in markup
    assert "url(#hatch)" not in markup
