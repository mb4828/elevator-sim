"""Tests for the top-level CLI."""

import json
from pathlib import Path

import pytest
from rich_argparse import RichHelpFormatter

from main import _build_parser, main


def test_main_prints_summary_and_performance_tables(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI prints comparison tables and writes a per-strategy state log."""
    monkeypatch.chdir(tmp_path)
    perf_counter_values = iter((100.0, 100.25))
    monkeypatch.setattr("main.perf_counter", lambda: next(perf_counter_values))
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,source,dest\n0,passenger1,0,1\n", encoding="utf-8")

    exit_code = main(
        [
            "--floors",
            "4",
            "--elevators",
            "1",
            "--capacity",
            "4",
            "--input-file",
            str(input_file),
            "--max-ticks",
            "80",
            "--strategy",
            "nearest_car_same_direction",
        ]
    )

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Simulation runtime: 0.250000 seconds" in output
    assert "Summary Statistics" in output
    assert "Wait Time" in output
    assert "Total Time" in output
    assert "Min" in output
    assert "Max" in output
    assert "Avg" in output
    assert "Peak Queue" in output
    assert "Performance Analysis" in output
    assert "Total Ticks" in output
    assert "Utilization %" in output
    assert "Wait Time Avg" in output
    assert "Wait Time P90" in output

    state_log_path = tmp_path / "nearest_car_same_direction_log.json"
    state_log = json.loads(state_log_path.read_text(encoding="utf-8"))
    assert state_log["version"] == 1
    assert state_log["frames"][0]["elevators"][0]["floor"] == 0
    assert state_log["frames"][-1]["complete"] is True


def test_main_uses_input_file_for_workload(
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """CLI can run a strategy against a CSV workload."""
    monkeypatch.chdir(tmp_path)
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,source,dest\n0,passenger1,0,1\n", encoding="utf-8")

    exit_code = main(
        [
            "--floors",
            "2",
            "--elevators",
            "1",
            "--capacity",
            "4",
            "--input-file",
            str(input_file),
            "--max-ticks",
            "20",
            "--strategy",
            "nearest_car_same_direction",
        ]
    )

    capsys.readouterr()

    assert exit_code == 0
    state_log = json.loads((tmp_path / "nearest_car_same_direction_log.json").read_text(encoding="utf-8"))
    assert len(state_log["passengers"]) == 1


def test_main_requires_building_configuration() -> None:
    """CLI fails when a required building configuration argument is missing."""
    with pytest.raises(SystemExit):
        main(["--floors", "5", "--input-file", "workload.csv", "--strategy", "nearest_car_same_direction"])


def test_main_requires_strategy_and_input_file() -> None:
    """CLI fails unless both strategy and input-file arguments are provided."""
    with pytest.raises(SystemExit):
        main(["--floors", "5", "--elevators", "2", "--capacity", "4"])


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
