"""The entry point is now the whole input surface, so pin what that promises."""

import sys

import pytest

from house import cli


def test_every_sweep_input_is_reachable_as_a_flag() -> None:
    """Defaults are the documented constants, and every one can be overridden.

    Knee and collar are checked too: the sweep never varies them, and the point
    of the flags is that "what would a 0.5 m nadmurovka buy me?" is a command
    line rather than an edit (`docs/decisions.md`).
    """
    defaults = cli.build_parser().parse_args([])
    assert defaults.widths == list(cli.WIDTHS)
    assert defaults.pitches == list(cli.PITCHES_DEG)
    assert defaults.length == cli.LENGTH
    assert defaults.overhang_eave == cli.OVERHANG_EAVE
    assert defaults.overhang_gable == cli.OVERHANG_GABLE
    assert defaults.h_min == cli.H_MIN
    assert defaults.roof_buildup == cli.ROOF_BUILDUP
    assert defaults.floor_buildup == cli.FLOOR_BUILDUP
    assert defaults.knee == cli.KNEE_HEIGHT
    assert defaults.collar is None
    assert defaults.eur_per_m2 == cli.EUR_PER_M2

    custom = cli.build_parser().parse_args(
        [
            "--widths",
            "8",
            "12",
            "--pitches",
            "35",
            "--length",
            "18",
            "--overhang-eave",
            "0.5",
            "--overhang-gable",
            "0.3",
            "--h-min",
            "2",
            "--roof-buildup",
            "0.25",
            "--floor-buildup",
            "0.15",
            "--knee",
            "0.5",
            "--collar",
            "2.6",
            "--eur-per-m2",
            "95",
        ]
    )
    assert custom.widths == [8.0, 12.0]
    assert custom.pitches == [35.0]
    assert (custom.length, custom.overhang_eave, custom.overhang_gable) == (
        18.0,
        0.5,
        0.3,
    )
    assert (custom.h_min, custom.roof_buildup, custom.floor_buildup) == (
        2.0,
        0.25,
        0.15,
    )
    assert (custom.knee, custom.collar, custom.eur_per_m2) == (0.5, 2.6, 95.0)


def test_an_invalid_value_exits_with_the_specs_own_message(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """The spec constructors are the validation boundary and already say what is
    wrong, so a bad flag must surface as that message, not as a traceback."""
    monkeypatch.setattr(sys, "argv", ["house", "--h-min", "-1"])

    with pytest.raises(SystemExit) as exit_info:
        cli.main()

    assert exit_info.value.code == 2
    assert "h_min must be positive" in capsys.readouterr().err
