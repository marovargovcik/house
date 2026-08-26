"""Slovak number formatting for the report.

Interpreter-side by design: the core speaks plain floats and metres, and the
convention — decimal comma, narrow no-break space between thousands — is put on
at the boundary where the numbers become something a projektant reads.
"""

_GROUP = "\u202f"
"""Narrow no-break space between thousands, so a figure never wraps mid-number."""


def _localize(text: str) -> str:
    """`"12,560.75"` -> `"12 560,75"`, in that order.

    Thousands first: swapping the decimal point to a comma while the group
    separators are still commas would leave two kinds of comma to tell apart.
    """
    return text.replace(",", _GROUP).replace(".", ",")


def fixed(value: float, places: int) -> str:
    """Exactly `places` decimals — for values read down a column against each other."""
    return _localize(f"{value:,.{places}f}")


def trimmed(value: float) -> str:
    """Up to two decimals, trailing zeros dropped: 2.60 -> `2,6`, 9.0 -> `9`.

    For labels on a drawing, where a trailing zero is noise rather than a claim
    about precision.
    """
    text = f"{value:,.2f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return _localize(text)
