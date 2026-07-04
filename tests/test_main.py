"""Tests for the top-level CLI."""

import json
from pathlib import Path

import pytest
from rich_argparse import RichHelpFormatter

from main import _build_parser, main


def test_main_runs_with_only_required_building_configuration(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI accepts only required building configuration and skips comparison without strategies."""
    exit_code = main(["--floors", "5", "--elevators", "2", "--capacity", "4"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Generated passengers:" in output
    assert "No strategies provided" in output


def test_main_prints_summary_and_performance_tables(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI prints comparison tables and writes a per-strategy state log."""
    monkeypatch.chdir(tmp_path)

    exit_code = main(
        [
            "--floors",
            "4",
            "--elevators",
            "1",
            "--capacity",
            "4",
            "--duration",
            "1",
            "--probability",
            "1.0",
            "--strategy",
            "tests.test_workload.CompletingStrategy",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Summary Statistics" in output
    assert "Min Wait" in output
    assert "Max Wait" in output
    assert "Avg Wait" in output
    assert "Min Total" in output
    assert "Max Total" in output
    assert "Avg Total" in output
    assert "Performance Analysis" in output
    assert "Total Ticks" in output
    assert "Avg Passengers/Tick" in output
    assert "Peak Queue" in output
    assert "Efficiency Score" in output

    state_log_path = tmp_path / "tests.test_workload.CompletingStrategy.state-log.json"
    state_log = json.loads(state_log_path.read_text(encoding="utf-8"))
    assert state_log[0]["elevator_positions"] == {"1": 0}
    assert state_log[-1]["complete"] is True


def test_main_requires_building_configuration() -> None:
    """CLI fails when a required building configuration argument is missing."""
    with pytest.raises(SystemExit):
        main(["--floors", "5", "--elevators", "2"])


def test_main_help_groups_required_and_optional_options(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI help groups required and optional options for readability."""
    with pytest.raises(SystemExit):
        main(["--help"])

    output = capsys.readouterr().out

    assert "Required:" in output
    assert "Optional:" in output


def test_parser_uses_rich_help_formatter() -> None:
    """CLI parser uses rich-argparse for help rendering."""
    parser = _build_parser()

    assert parser.formatter_class is RichHelpFormatter
