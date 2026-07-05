"""Tests for CSV-backed workload sources."""

from pathlib import Path

import pytest

from elevator_sim.workload.file_source import FileSource


def test_file_source_loads_passengers_from_csv(tmp_path: Path) -> None:
    """File source converts CSV rows into scheduled passengers."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text(
        "time,id,source,dest\n0,passenger1,1,51\n0,passenger2,1,37\n10,passenger3,20,1\n",
        encoding="utf-8",
    )

    source = FileSource(input_file)

    assert [passenger.id for passenger in source.passengers] == [0, 1, 2]
    assert [passenger.full_id for passenger in source.passengers] == ["passenger1", "passenger2", "passenger3"]
    passenger_routes = [
        (passenger.request_time, passenger.start_floor, passenger.destination_floor) for passenger in source.passengers
    ]
    assert passenger_routes == [
        (0, 1, 51),
        (0, 1, 37),
        (10, 20, 1),
    ]
    assert [passenger.id for passenger in source.passengers_at(0)] == [0, 1]
    assert [passenger.id for passenger in source.passengers_at(10)] == [2]
    assert source.is_exhausted(11)


def test_file_source_rejects_invalid_header(tmp_path: Path) -> None:
    """File source requires the documented CSV header."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,start,dest\n0,passenger1,1,2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="time,id,source,dest"):
        FileSource(input_file)


def test_file_source_accepts_plain_integer_ids(tmp_path: Path) -> None:
    """File source accepts purely numeric passenger IDs without a label prefix."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,source,dest\n0,7,1,2\n", encoding="utf-8")

    source = FileSource(input_file)

    assert [passenger.id for passenger in source.passengers] == [0]
    assert [passenger.full_id for passenger in source.passengers] == ["7"]


def test_file_source_rejects_empty_file(tmp_path: Path) -> None:
    """File source rejects a workload file with no header row."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("", encoding="utf-8")

    with pytest.raises(ValueError, match="is empty"):
        FileSource(input_file)


def test_file_source_with_header_only_is_immediately_exhausted(tmp_path: Path) -> None:
    """File source with no passenger rows produces an empty, exhausted workload."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,source,dest\n", encoding="utf-8")

    source = FileSource(input_file)

    assert source.passengers == ()
    assert source.is_exhausted(0)


def test_file_source_rejects_non_integer_fields(tmp_path: Path) -> None:
    """File source reports the offending field and row for non-integer values."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,source,dest\n0,passenger1,x,2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="source must be an integer on row 2"):
        FileSource(input_file)


def test_file_source_accepts_id_without_digits(tmp_path: Path) -> None:
    """File source accepts arbitrary non-empty passenger display IDs."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,source,dest\n0,passenger,1,2\n", encoding="utf-8")

    source = FileSource(input_file)

    assert source.passengers[0].id == 0
    assert source.passengers[0].full_id == "passenger"
