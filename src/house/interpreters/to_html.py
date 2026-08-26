"""Sweep table → a self-contained HTML report, one drawn card per row.

An interpreter: the only place the report touches the disk. Each card's drawing
is rebuilt from that row's own `width_m` and `pitch_deg`, so the picture and the
numbers printed beside it are the same configuration by construction — there is
no second source of truth to fall out of step.
"""

import math
from collections.abc import Hashable, Iterable, Sequence
from pathlib import Path
from typing import Any

import pandas as pd

from house.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec
from house.interpreters import to_svg

_NUMBERS: tuple[tuple[str, str], ...] = (
    ("roof area", "roof_area_m2"),
    ("ridge above wall top", "ridge_above_wall_top_m"),
    ("usable width", "usable_width_m"),
    ("usable area", "usable_area_m2"),
    ("usable fraction", "usable_fraction"),
    ("total cost", "total_eur"),
    ("per usable m²", "eur_per_usable_m2"),
)


def _cell(column: str, value: float) -> str:
    """One number formatted for its column, NaN shown as a dash.

    NaN reaches here from `eur_per_usable_m2` where no attic is habitable — see
    `sweep.width_by_pitch`. Printing it as a dash keeps the row honest instead of
    rendering a stray `nan`.
    """
    if math.isnan(value):
        return "—"
    if column.endswith("_eur") or column.startswith("eur_"):
        return f"{value:,.0f} €".replace(",", "&#8239;")
    if column.endswith("_m2"):
        return f"{value:,.1f} m²"
    if column.endswith("_m"):
        return f"{value:.2f} m"
    return f"{value:.0%}"


def _card(
    record: dict[Hashable, Any],
    length: float,
    attic: AtticSpec,
    overhang_eave: float,
    overhang_gable: float,
) -> str:
    house = HouseSpec(width=float(record["width_m"]), length=length)
    roof = RoofSpec(
        pitch_deg=float(record["pitch_deg"]),
        overhang_eave=overhang_eave,
        overhang_gable=overhang_gable,
    )
    numbers = "".join(
        f"<div><dt>{label}</dt><dd>{_cell(column, float(record[column]))}</dd></div>"
        for label, column in _NUMBERS
    )
    return (
        '<figure class="card">'
        f"<figcaption><b>{house.width:g} m</b> wide "
        f"· <b>{roof.pitch_deg:g}°</b></figcaption>"
        f"{to_svg.card_svg(house, roof, attic)}"
        f'<dl class="numbers">{numbers}</dl>'
        "</figure>"
    )


def _sections(
    records: Sequence[dict[Hashable, Any]],
    length: float,
    attic: AtticSpec,
    overhang_eave: float,
    overhang_gable: float,
) -> str:
    """Cards grouped by width, so reading down a group is a pure pitch sweep."""
    widths: list[float] = []
    for record in records:
        width = float(record["width_m"])
        if width not in widths:
            widths.append(width)
    return "".join(
        f"<h2>{width:g} m wide</h2><div class='grid'>"
        + "".join(
            _card(record, length, attic, overhang_eave, overhang_gable)
            for record in records
            if float(record["width_m"]) == width
        )
        + "</div>"
        for width in widths
    )


def _assumptions(
    length: float,
    attic: AtticSpec,
    costs: CostSpec,
    overhang_eave: float,
    overhang_gable: float,
) -> str:
    """Every input the cards are drawn and priced from, stated on the page.

    A cost figure with no rate beside it is unreadable a month later, so the rate
    travels with the report rather than living only in the entry point.
    """
    items: Iterable[str] = (
        f"length {length:g} m",
        f"h_min {attic.h_min:g} m (assumption — the Slovak norm is still open)",
        f"knee wall {attic.knee_height:g} m",
        f"odkvapový presah {overhang_eave:g} m, štítový presah {overhang_gable:g} m",
        (
            f"roof {costs.eur_per_m2:g} €/m² of roof surface — all-in: krov, "
            "insulation, membrane, battens, covering, gutters, labour"
        ),
        "charged on gross area, overhang included (a deliberate over-estimate)",
    )
    return "".join(f"<li>{item}</li>" for item in items)


def write_html(
    table: pd.DataFrame,
    length: float,
    attic: AtticSpec,
    costs: CostSpec,
    overhang_eave: float,
    overhang_gable: float,
    path: Path,
) -> None:
    """Write the sweep as a drawn report. Self-contained: no external assets."""
    records: list[dict[Hashable, Any]] = table.to_dict(orient="records")
    page = _PAGE.format(
        style=_STYLE + to_svg.STYLE,
        defs=to_svg.defs_svg(),
        assumptions=_assumptions(length, attic, costs, overhang_eave, overhang_gable),
        sections=_sections(records, length, attic, overhang_eave, overhang_gable),
        table=table.round(2).to_html(
            index=False, border=0, classes="sweep", na_rep="—"
        ),
    )
    path.write_text(page, encoding="utf-8")


_STYLE = """
:root {
  --bg: #fbfaf8; --panel: #fff; --ink: #1c1a17; --dim: #7a736a;
  --roof: #b4530f; --usable: #2f7d6b; --accent: #b4530f; --wall-fill: #efece7;
  --rule: #e2ded7;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #171614; --panel: #201e1b; --ink: #ece8e1; --dim: #9c948a;
    --roof: #e2853b; --usable: #5cbfa6; --accent: #e2853b; --wall-fill: #2a2723;
    --rule: #322e29;
  }
}
* { box-sizing: border-box; }
body { margin: 0; padding: 2rem 1.5rem 4rem; background: var(--bg); color: var(--ink);
  font: 15px/1.5 ui-sans-serif, system-ui, sans-serif; }
main { max-width: 1600px; margin: 0 auto; }
h1 { font-size: 1.5rem; margin: 0 0 .25rem; }
h2 { font-size: 1.05rem; margin: 2.5rem 0 .75rem; padding-bottom: .4rem;
  border-bottom: 1px solid var(--rule); }
.lede { color: var(--dim); margin: 0 0 1.25rem; }
.assumptions { margin: 0 0 1.5rem; padding-left: 1.1rem; color: var(--dim);
  font-size: .875rem; }
.legend { display: flex; flex-wrap: wrap; gap: 1.25rem; padding: .75rem 1rem;
  background: var(--panel); border: 1px solid var(--rule); border-radius: 8px;
  font-size: .8125rem; color: var(--dim); }
.legend span { display: flex; align-items: center; gap: .45rem; }
.swatch { width: 22px; height: 0; border-top-width: 3px; border-top-style: solid; }
.swatch.roof { border-color: var(--roof); }
.swatch.over { border-color: var(--roof); opacity: .45; }
.swatch.head { border-color: var(--usable); border-top-style: dashed; }
.swatch.ridge { border-color: var(--roof); border-top-style: dashed; }
.swatch.fill { height: 13px; border: 1px solid var(--usable); background:
  repeating-linear-gradient(45deg, transparent 0 3px, var(--usable) 3px 5px); }
.grid { display: flex; flex-wrap: wrap; gap: 1rem; align-items: flex-start; }
.card { margin: 0; padding: 1rem; background: var(--panel); flex: 0 0 auto;
  border: 1px solid var(--rule); border-radius: 10px; }
figcaption { font-size: .875rem; margin-bottom: .5rem; color: var(--dim); }
figcaption b { color: var(--ink); }
.numbers { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: .15rem 1.25rem; margin: .75rem 0 0; font-size: .8125rem; }
.numbers div { display: flex; justify-content: space-between; gap: .75rem;
  border-bottom: 1px dotted var(--rule); padding: .15rem 0; }
.numbers dt { color: var(--dim); }
.numbers dd { margin: 0; font-variant-numeric: tabular-nums; }
table.sweep { border-collapse: collapse; font-size: .8125rem;
  font-variant-numeric: tabular-nums; }
table.sweep th, table.sweep td { padding: .3rem .6rem; text-align: right;
  border-bottom: 1px solid var(--rule); }
table.sweep th { color: var(--dim); font-weight: 500; white-space: nowrap; }
.scroll { overflow-x: auto; }
@media print {
  body { background: #fff; padding: 0; }
  .card { break-inside: avoid; }
}
"""

_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Roof sweep — section and plan</title>
<style>{style}</style>
</head>
<body>
{defs}
<main>
<h1>Roof sweep &mdash; width &times; pitch</h1>
<p class="lede">Every drawing is at the same scale, so widths and pitches
compare by eye across cards.</p>
<ul class="assumptions">{assumptions}</ul>
<div class="legend">
<span><i class="swatch roof"></i>roof plane</span>
<span><i class="swatch over"></i>overhang &mdash; odkvap (eave) / štít (gable)</span>
<span><i class="swatch ridge"></i>hrebeň (ridge)</span>
<span><i class="swatch head"></i>h_min headroom line</span>
<span><i class="swatch fill"></i>standing room — its base is the usable width</span>
</div>
{sections}
<h2>The numbers</h2>
<div class="scroll">{table}</div>
</main>
</body>
</html>
"""
