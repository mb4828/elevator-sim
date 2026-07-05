"""Tests for CSV-backed workload sources."""

from pathlib import Path

import pytest

from elevator_sim.workload.file_source import FileSource


def test_file_source_loads_passengers_from_csv(tmp_path: Path) -> None:
    """File source converts CSV rows into scheduled passengers."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text(
        "time,id,source,dest\n"
        "0,passenger1,1,51\n"
        "0,passenger2,1,37\n"
        "10,passenger3,20,1\n",
        encoding="utf-8",
    )

    source = FileSource(input_file)

    assert [passenger.id for passenger in source.passengers] == [1, 2, 3]
    passenger_routes = [
        (passenger.request_time, passenger.start_floor, passenger.destination_floor)
        for passenger in source.passengers
    ]
    assert passenger_routes == [
        (0, 1, 51),
        (0, 1, 37),
        (10, 20, 1),
    ]
    assert [passenger.id for passenger in source.passengers_at(0)] == [1, 2]
    assert [passenger.id for passenger in source.passengers_at(10)] == [3]
    assert source.is_exhausted(11)


def test_file_source_rejects_invalid_header(tmp_path: Path) -> None:
    """File source requires the documented CSV header."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,start,dest\n0,passenger1,1,2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="time,id,source,dest"):
        FileSource(input_file)


def test_file_source_rejects_id_without_digits(tmp_path: Path) -> None:
    """File source rejects passenger labels that cannot be converted to integer IDs."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,source,dest\n0,passenger,1,2\n", encoding="utf-8")

    with pytest.raises(ValueError, match="id"):
        FileSource(input_file)
