"""Tests for elevator simulation domain models."""

import pytest

from elevator_sim.core.models import Direction, Elevator, Passenger


def test_passenger_direction_for_up_and_down_trips() -> None:
    """Passenger direction reflects destination relative to origin."""
    assert Passenger(id=1, request_time=0, start_floor=0, destination_floor=4).direction == Direction.UP
    assert Passenger(id=2, request_time=0, start_floor=4, destination_floor=0).direction == Direction.DOWN


def test_models_accept_floor_zero() -> None:
    """Passenger and elevator models accept zero-based floor identifiers."""
    passenger = Passenger(id=1, request_time=0, start_floor=0, destination_floor=1)
    elevator = Elevator(id=1, current_floor=0, capacity=2, target_floors=[0, 1])

    passenger.validate_for_building(floors=2, current_time=0)
    elevator.validate_for_building(floors=2)


def test_passenger_timing_metrics_are_none_until_events_occur() -> None:
    """Wait and total time stay unset until pickup and drop-off timestamps exist."""
    passenger = Passenger(id=1, request_time=3, start_floor=1, destination_floor=2)

    assert passenger.wait_time is None
    assert passenger.total_time is None

    passenger.pickup_time = 5
    passenger.dropoff_time = 8

    assert passenger.wait_time == 2
    assert passenger.total_time == 5


def test_passenger_rejects_same_origin_and_destination() -> None:
    """Passenger model rejects requests with identical start and destination floors."""
    with pytest.raises(ValueError, match="start and destination floors"):
        Passenger(id=1, request_time=0, start_floor=2, destination_floor=2)


def test_elevator_rejects_non_positive_capacity() -> None:
    """Elevator model rejects non-positive passenger capacity."""
    with pytest.raises(ValueError, match="greater than 0"):
        Elevator(id=1, current_floor=1, capacity=0)


def test_models_validate_building_specific_bounds() -> None:
    """Domain models expose validation for configured building floor counts."""
    passenger = Passenger(id=1, request_time=0, start_floor=1, destination_floor=3)
    elevator = Elevator(id=1, current_floor=3, capacity=2)

    with pytest.raises(ValueError, match="destination_floor"):
        passenger.validate_for_building(floors=3, current_time=0)

    with pytest.raises(ValueError, match="current_floor"):
        elevator.validate_for_building(floors=3)


def test_elevator_validates_initial_target_floors() -> None:
    """Elevator building validation rejects target floors outside configured bounds."""
    elevator = Elevator(id=1, current_floor=1, capacity=2, target_floors=[3])

    with pytest.raises(ValueError, match="target_floor"):
        elevator.validate_for_building(floors=3)
