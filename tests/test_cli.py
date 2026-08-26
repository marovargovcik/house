"""The entry point is the whole input surface, so pin what that promises.

The promise is that nothing is assumed on your behalf: every sweep input has to
be typed, so no figure can reach a report by being inherited from a default
nobody looked at.
"""

import sys

import pytest

from house import cli

# One complete invocation. Deliberately not the current design — these tests
# check the parser, and README.md is where the design's own numbers live.
FULL = [
    "--widths", "9", "11",
    "--length", "25",
    "--pitches", "30", "45",
    "--overhang-eave", "0.6",
    "--overhang-gable", "0.4",
    "--h-min", "1.9",
    "--roof-buildup", "0.3",
    "--floor-buildup", "0.2",
    "--knee", "0",
    "--collar", "0",
    "--eur-per-m2", "110",
]  # fmt: skip

REQUIRED_FLAGS = [
    "--widths",
    "--length",
    "--pitches",
    "--overhang-eave",
    "--overhang-gable",
    "--h-min",
    "--roof-buildup",
    "--floor-buildup",
    "--knee",
    "--eur-per-m2",
]


def _without(flag: str) -> list[str]:
    """`FULL` minus one flag and the values that belong to it."""
    start = FULL.index(flag)
    end = start + 1
    while end < len(FULL) and not FULL[end].startswith("--"):
        end += 1
    return FULL[:start] + FULL[end:]


def test_a_complete_invocation_parses() -> None:
    args = cli.build_parser().parse_args(FULL)
    assert args.widths == [9.0, 11.0]
    assert args.pitches == [30.0, 45.0]
    assert (args.length, args.overhang_eave, args.overhang_gable) == (25.0, 0.6, 0.4)
    assert (args.h_min, args.roof_buildup, args.floor_buildup) == (1.9, 0.3, 0.2)
    assert (args.knee, args.eur_per_m2) == (0.0, 110.0)


@pytest.mark.parametrize("flag", REQUIRED_FLAGS)
def test_dropping_any_input_is_an_error(flag: str) -> None:
    """No input may quietly fall back to a value nobody chose — including `--knee`,
    where 0 is the current design rather than a safe blank."""
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(_without(flag))


def test_zero_is_how_the_collar_flag_says_there_is_none(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """A required flag cannot also be omitted, so 0 stands in for absence — and
    the translation to `None` must happen at this boundary, since `AtticSpec`
    rejects a collar sitting at or below the wall top.
    """
    monkeypatch.setattr(sys, "argv", ["house", *FULL])
    cli.main()
    assert "klieština musí byť najmenej" not in capsys.readouterr().out

    monkeypatch.setattr(sys, "argv", ["house", *_without("--collar"), "--collar", "-1"])
    with pytest.raises(SystemExit):
        cli.main()
    assert "collar must sit above the wall top" in capsys.readouterr().err


def test_an_invalid_value_exits_with_the_specs_own_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The spec constructors are the validation boundary and already say what is
    wrong, so a bad flag must surface as that message, not as a traceback."""
    monkeypatch.setattr(sys, "argv", ["house", *_without("--h-min"), "--h-min", "-1"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
    assert "h_min must be positive" in capsys.readouterr().err
