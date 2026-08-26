"""Sweep rows → a self-contained HTML report in Slovak, one drawn card per row.

The report is what goes to the projektant and the builders, so the whole page —
prose, dimension labels, table headers, number formatting — is Slovak. The core
stays in English: only this boundary translates (`CLAUDE.md`, units & vocabulary).

Split in two: `render_html` builds the page and `write_html` puts it on disk, so
a caller with nowhere to write can still have the page. Each card's drawing
is rebuilt from that row's own `width_m` and `pitch_deg`, so the picture and the
numbers printed beside it are the same configuration by construction — there is
no second source of truth to fall out of step.
"""

import math
from collections.abc import Iterable, Sequence
from dataclasses import asdict
from pathlib import Path

from house.core import attic as attic_calc
from house.core.specs import AtticSpec, CostSpec, HouseSpec, RoofSpec
from house.core.sweep import SweepRow
from house.interpreters import sk, to_svg

_COLUMNS: tuple[tuple[str, str, str], ...] = (
    # sweep column, Slovak label, unit ("" for none)
    ("width_m", "šírka", "m"),
    ("pitch_deg", "sklon", "°"),
    ("roof_area_m2", "plocha strechy", "m²"),
    ("ridge_above_wall_top_m", "hrebeň nad korunou muriva", "m"),
    ("clear_ridge_m", "svetlá výška v hrebeni", "m"),
    ("usable_width_m", "úžitková šírka", "m"),
    ("usable_area_m2", "úžitková plocha", "m²"),
    ("usable_fraction", "podiel úžitkovej plochy", "%"),
    ("total_eur", "cena spolu", "€"),
    ("eur_per_usable_m2", "cena za úžitkový m²", "€"),
)
"""Sweep columns as the report names them. One registry so a card panel, a table
header, and a unit can never drift apart."""

_PLACES = {"m": 2, "m²": 1, "°": 0, "%": 0, "€": 0}

# Width and pitch head each card, so repeating them inside it is noise.
_CARD_ROWS = tuple(row for row in _COLUMNS if row[0] not in {"width_m", "pitch_deg"})


def _number(unit: str, value: float) -> str:
    """The bare figure, Slovak-formatted, with no unit attached.

    NaN reaches here from `eur_per_usable_m2` where no attic is habitable — see
    `sweep.width_by_pitch`. A dash keeps the row honest instead of printing a
    stray `nan`.
    """
    if math.isnan(value):
        return "—"
    return sk.fixed(value * 100 if unit == "%" else value, _PLACES[unit])


def _with_unit(unit: str, value: float) -> str:
    """Slovak spaces a unit off its number — except the degree sign.

    A no-break space, so a figure and its unit never land on separate lines. It
    is the wider U+00A0 rather than the U+202F used between thousands: that one
    is deliberately tight enough to read as a group separator, which is exactly
    what a unit gap must not look like.
    """
    figure = _number(unit, value)
    if not unit or figure == "—":
        return figure
    return f"{figure}°" if unit == "°" else f"{figure}\u00a0{unit}"


def _card(
    row: SweepRow,
    length: float,
    attic: AtticSpec,
    overhang_eave: float,
    overhang_gable: float,
) -> str:
    house = HouseSpec(width=row.width_m, length=length)
    values = asdict(row)
    roof = RoofSpec(
        pitch_deg=row.pitch_deg,
        overhang_eave=overhang_eave,
        overhang_gable=overhang_gable,
    )
    numbers = "".join(
        f"<div><dt>{label}</dt><dd>{_with_unit(unit, float(values[column]))}</dd></div>"
        for column, label, unit in _CARD_ROWS
    )
    return (
        '<figure class="card">'
        f"<figcaption>šírka <b>{sk.trimmed(house.width)} m</b> "
        f"· sklon <b>{sk.trimmed(roof.pitch_deg)}°</b></figcaption>"
        f"{to_svg.card_svg(house, roof, attic)}"
        f'<dl class="numbers">{numbers}</dl>'
        "</figure>"
    )


def _sections(
    rows: Sequence[SweepRow],
    length: float,
    attic: AtticSpec,
    overhang_eave: float,
    overhang_gable: float,
) -> str:
    """Cards grouped by width, so reading down a group is a pure pitch sweep."""
    widths: list[float] = []
    for row in rows:
        if row.width_m not in widths:
            widths.append(row.width_m)
    return "".join(
        f"<h2>šírka {sk.trimmed(width)} m</h2><div class='grid'>"
        + "".join(
            _card(row, length, attic, overhang_eave, overhang_gable)
            for row in rows
            if row.width_m == width
        )
        + "</div>"
        for width in widths
    )


def _collar_note(attic: AtticSpec) -> str:
    """What the collar tie does to this sweep, stated either way.

    Without one the useful figure is the constraint — the lowest a klieština can
    sit and still leave `h_min` under it. With one, the page has to say whether
    it clears, because a collar that does not zeroes every row and the drawings
    would otherwise show that with no reason given.
    """
    lowest = sk.trimmed(attic_calc.min_collar_height(attic))
    if attic.collar_above_wall_top is None:
        return (
            f"klieština musí byť najmenej {lowest} m nad korunou muriva, inak pod "
            "ňou nikde nie je podchodná výška (v tomto prehľade žiadna nie je)"
        )
    height = sk.trimmed(attic.collar_above_wall_top)
    if attic_calc.collar_blocks(attic):
        return (
            f"klieština {height} m nad korunou muriva — príliš nízko, musela by "
            f"byť najmenej {lowest} m, takže podkrovie nie je využiteľné pri "
            "žiadnom sklone"
        )
    return (
        f"klieština {height} m nad korunou muriva — vyhovuje, najmenej je "
        f"potrebných {lowest} m"
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
        f"dĺžka {sk.trimmed(length)} m",
        (
            f"h_min {sk.trimmed(attic.h_min)} m "
            "(predpoklad — slovenská norma zatiaľ nie je potvrdená)"
        ),
        f"nadmurovka {sk.trimmed(attic.knee_height)} m",
        (
            f"skladba strechy {sk.trimmed(attic.roof_buildup)} m kolmo na rovinu "
            "strechy (krokvy, izolácia, podhľad) — zvislo teda viac, tým viac, "
            "čím je strecha strmšia"
        ),
        (f"skladba podlahy {sk.trimmed(attic.floor_buildup)} m nad korunou muriva"),
        _collar_note(attic),
        (
            f"odkvapový presah {sk.trimmed(overhang_eave)} m, "
            f"štítový presah {sk.trimmed(overhang_gable)} m"
        ),
        (
            f"strecha {sk.trimmed(costs.eur_per_m2)} €/m² plochy strechy — "
            "všetko v cene: krov, izolácia, poistná fólia, latovanie, krytina, "
            "odkvapy, práca"
        ),
        "účtované z hrubej plochy vrátane presahu (zámerne nadhodnotené)",
    )
    return "".join(f"<li>{item}</li>" for item in items)


def _table(rows: Sequence[SweepRow]) -> str:
    """The sweep as a table, formatted exactly as the cards format it.

    Headers carry the Slovak names and units from `_COLUMNS`, and the figures go
    through the same formatter the cards use, so the two never disagree.
    """
    head = "".join(
        f"<th>{label}{f' ({unit})' if unit else ''}</th>" for _, label, unit in _COLUMNS
    )
    body = "".join(
        "<tr>"
        + "".join(
            f"<td>{_number(unit, float(values[column]))}</td>"
            for column, _, unit in _COLUMNS
        )
        + "</tr>"
        for values in (asdict(row) for row in rows)
    )
    return f'<table class="sweep"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>'


def render_html(
    rows: Sequence[SweepRow],
    length: float,
    attic: AtticSpec,
    costs: CostSpec,
    overhang_eave: float,
    overhang_gable: float,
) -> str:
    """The sweep as a drawn report. Self-contained: no external assets."""
    return _PAGE.format(
        style=_STYLE + to_svg.STYLE,
        defs=to_svg.defs_svg(),
        assumptions=_assumptions(length, attic, costs, overhang_eave, overhang_gable),
        sections=_sections(rows, length, attic, overhang_eave, overhang_gable),
        table=_table(rows),
    )


def write_html(
    rows: Sequence[SweepRow],
    length: float,
    attic: AtticSpec,
    costs: CostSpec,
    overhang_eave: float,
    overhang_gable: float,
    path: Path,
) -> None:
    path.write_text(
        render_html(rows, length, attic, costs, overhang_eave, overhang_gable),
        encoding="utf-8",
    )


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
.swatch.collar { border-top-width: 5px; border-color: var(--roof); }
.swatch.build { height: 13px; border: none; background: var(--roof); opacity: .3; }
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
<html lang="sk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Strecha — šírka a sklon</title>
<style>{style}</style>
</head>
<body>
{defs}
<main>
<h1>Strecha &mdash; prehľad šírok a sklonov</h1>
<p class="lede">Všetky výkresy sú v rovnakej mierke, takže šírky a sklony
sa dajú porovnať voľným okom.</p>
<ul class="assumptions">{assumptions}</ul>
<div class="legend">
<span><i class="swatch roof"></i>rovina strechy</span>
<span><i class="swatch over"></i>presah &mdash; odkvapový / štítový</span>
<span><i class="swatch ridge"></i>hrebeň</span>
<span><i class="swatch build"></i>skladba strechy a podlahy &mdash; to, čo uberá
podchodnú výšku</span>
<span><i class="swatch collar"></i>klieština</span>
<span><i class="swatch head"></i>h_min &mdash; minimálna podchodná výška</span>
<span><i class="swatch fill"></i>priestor na státie &mdash; jeho základňa je
úžitková šírka</span>
</div>
{sections}
<h2>Čísla</h2>
<div class="scroll">{table}</div>
</main>
</body>
</html>
"""
