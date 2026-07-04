"""Tests for the top-level CLI."""

import pytest

from main import main


def test_main_runs_with_only_required_building_configuration(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI accepts only required building configuration and skips comparison without strategies."""
    exit_code = main(["--floors", "5", "--elevators", "2", "--max-passengers", "4"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Generated passengers:" in output
    assert "No strategies provided" in output


def test_main_accepts_capacity_alias(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI keeps --capacity as an alias for maximum passengers."""
    exit_code = main(["--floors", "5", "--elevators", "2", "--capacity", "4"])

    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Generated passengers:" in output


def test_main_requires_building_configuration() -> None:
    """CLI fails when a required building configuration argument is missing."""
    with pytest.raises(SystemExit):
        main(["--floors", "5", "--elevators", "2"])


def test_main_help_groups_required_and_optional_options(capsys: pytest.CaptureFixture[str]) -> None:
    """CLI help groups required and optional options for readability."""
    with pytest.raises(SystemExit):
        main(["--help"])

    output = capsys.readouterr().out

    assert "required:" in output
    assert "optional:" in output
