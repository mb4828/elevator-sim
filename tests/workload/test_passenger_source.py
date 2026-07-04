"""Tests for passenger workload sources."""

import pytest

from elevator_sim.workload.passenger_source import PassengerSource


def test_source_releases_passengers_by_request_time() -> None:
    """Passenger source returns only passengers scheduled for the requested tick."""
    source = PassengerSource(floors=3, passengers=3, duration=3, seed=1)

    for time in range(3):
        for passenger in source.passengers_at(time):
            assert passenger.request_time == time

    assert source.is_exhausted(3)


def test_source_generates_exact_passenger_count() -> None:
    """Passenger source generates exactly the requested number of passengers."""
    source = PassengerSource(floors=5, passengers=100, duration=10, seed=1)

    assert len(source.passengers) == 100


def test_source_generates_zero_based_floor_ids() -> None:
    """Passenger source generates floor IDs from 0 through floors - 1."""
    source = PassengerSource(floors=2, passengers=10, duration=10, seed=1)

    generated_floors = {
        floor for passenger in source.passengers for floor in (passenger.start_floor, passenger.destination_floor)
    }

    assert generated_floors == {0, 1}


def test_source_is_reproducible_with_seed() -> None:
    """Identical source seeds produce identical passenger workloads."""
    first = PassengerSource(floors=6, passengers=5, duration=10, seed=42)
    second = PassengerSource(floors=6, passengers=5, duration=10, seed=42)

    assert first.passengers == second.passengers


def test_source_generates_request_times_within_duration() -> None:
    """Passenger request times are generated within the configured duration."""
    source = PassengerSource(floors=5, passengers=100, duration=10, seed=1)

    assert {passenger.request_time for passenger in source.passengers} <= set(range(10))


def test_source_allows_zero_passengers_with_zero_duration() -> None:
    """Passenger source allows empty workloads with no duration."""
    source = PassengerSource(floors=3, passengers=0, duration=0, seed=1)

    assert source.passengers == ()
    assert source.passengers_at(0) == []
    assert source.is_exhausted(0)


def test_source_rejects_passengers_with_zero_duration() -> None:
    """Passenger source rejects positive passenger counts with no request window."""
    with pytest.raises(ValueError, match="duration"):
        PassengerSource(floors=3, passengers=1, duration=0)


def test_source_rejects_invalid_passenger_count() -> None:
    """Passenger source validates requested passenger count."""
    with pytest.raises(ValueError, match="passengers"):
        PassengerSource(floors=3, passengers=-1, duration=10)
