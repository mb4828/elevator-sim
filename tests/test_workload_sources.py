"""Tests for passenger workload sources."""

import pytest

from elevator_sim.workload.passenger_source import PassengerSource


def test_source_releases_passengers_by_request_time() -> None:
    """Passenger source returns only passengers scheduled for the requested tick."""
    source = PassengerSource(floors=3, probability=1.0, duration=3, seed=1)

    for time in range(3):
        for passenger in source.passengers_at(time):
            assert passenger.request_time == time

    assert source.is_exhausted(3)


def test_source_generates_zero_based_floor_ids() -> None:
    """Passenger source generates floor IDs from 0 through floors - 1."""
    source = PassengerSource(floors=2, probability=1.0, duration=10, seed=1)

    generated_floors = {
        floor for passenger in source.passengers for floor in (passenger.start_floor, passenger.destination_floor)
    }

    assert generated_floors == {0, 1}


def test_source_is_reproducible_with_seed() -> None:
    """Identical source seeds produce identical passenger workloads."""
    first = PassengerSource(floors=6, probability=0.5, duration=10, seed=42)
    second = PassengerSource(floors=6, probability=0.5, duration=10, seed=42)

    assert first.passengers == second.passengers


def test_source_rejects_invalid_probability() -> None:
    """Passenger source validates arrival probability bounds."""
    with pytest.raises(ValueError, match="probability"):
        PassengerSource(floors=3, probability=1.5, duration=10)
