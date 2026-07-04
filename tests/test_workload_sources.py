"""Tests for passenger workload sources."""

import pytest

from elevator_sim.workload.passenger_source import PassengerSource


def test_source_releases_passengers_by_request_time() -> None:
    """Passenger source returns only passengers scheduled for the requested tick."""
    source = PassengerSource(floors=3, arrival_probability=1.0, duration=3, seed=1)

    for time in range(3):
        for passenger in source.passengers_at(time):
            assert passenger.request_time == time

    assert source.is_exhausted(3)


def test_source_is_reproducible_with_seed() -> None:
    """Identical source seeds produce identical passenger workloads."""
    first = PassengerSource(floors=6, arrival_probability=0.5, duration=10, seed=42)
    second = PassengerSource(floors=6, arrival_probability=0.5, duration=10, seed=42)

    assert first.passengers == second.passengers


def test_source_rejects_invalid_probability() -> None:
    """Passenger source validates arrival probability bounds."""
    with pytest.raises(ValueError, match="arrival_probability"):
        PassengerSource(floors=3, arrival_probability=1.5, duration=10)
