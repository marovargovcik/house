"""Slovak number formatting: decimal comma, narrow no-break space for thousands."""

_GROUP = "\u202f"


def _localize(text: str) -> str:
    """`"12,560.75"` -> `"12 560,75"`. Thousands first, or the commas mix."""
    return text.replace(",", _GROUP).replace(".", ",")


def fixed(value: float, places: int) -> str:
    """Exactly `places` decimals, for columns."""
    return _localize(f"{value:,.{places}f}")


def trimmed(value: float) -> str:
    """Up to two decimals, trailing zeros dropped: 2.60 -> `2,6`. For labels."""
    text = f"{value:,.2f}"
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return _localize(text)
