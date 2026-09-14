"""Every sweep input must be typed; nothing falls back to a default."""

import sys

import pytest

from roof import cli

# A complete invocation for the parser, not the current design.
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
    "--collar",
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
    """No input has a default, `--knee` included."""
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args(_without(flag))


def test_zero_is_how_the_collar_flag_says_there_is_none(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """`--collar 0` means none; a negative collar fails with the spec's message."""
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
    """A bad flag exits 2 with the spec's message, not a traceback."""
    monkeypatch.setattr(sys, "argv", ["house", *_without("--h-min"), "--h-min", "-1"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
    assert "h_min must be positive" in capsys.readouterr().err
