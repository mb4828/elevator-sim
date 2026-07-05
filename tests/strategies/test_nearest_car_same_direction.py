"""Tests for nearest-car same-direction elevator scheduling."""

from elevator_sim.core.models import Direction, PassengerStatus
from elevator_sim.strategies.nearest_car_same_direction import NearestCarSameDirectionStrategy
from tests.strategies.conftest import build_elevator, build_passenger, build_snapshot


def test_plan_assigns_passenger_to_nearest_elevator_moving_toward_start_floor() -> None:
    """Nearest-car same-direction assigns to the closest elevator moving toward the passenger's direction."""
    state = build_snapshot(
        elevators=(
            build_elevator(1, current_floor=1, direction=Direction.UP),
            build_elevator(2, current_floor=7, direction=Direction.DOWN),
        ),
        passengers=(build_passenger(1, start_floor=5, destination_floor=8),),
    )

    decisions = NearestCarSameDirectionStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1,)
    assert decisions[0].stop_floors == (5, 8)
    assert decisions[1].assigned_passenger_ids == ()


def test_plan_prefers_idle_car_over_closer_wrong_direction_moving_car() -> None:
    """Nearest-car same-direction does not stop a moving car for an opposite-direction pickup."""
    state = build_snapshot(
        elevators=(
            build_elevator(1, current_floor=4, direction=Direction.UP),
            build_elevator(2, current_floor=0, direction=Direction.IDLE),
        ),
        passengers=(build_passenger(1, start_floor=5, destination_floor=1),),
    )

    decisions = NearestCarSameDirectionStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == ()
    assert decisions[1].assigned_passenger_ids == (1,)
    assert decisions[1].stop_floors == (5, 1)


def test_plan_uses_idle_elevator_when_moving_elevators_are_not_traveling_toward_passenger() -> None:
    """Nearest-car same-direction uses idle elevators when moving elevators would need to reverse before pickup."""
    state = build_snapshot(
        elevators=(
            build_elevator(1, current_floor=8, direction=Direction.UP),
            build_elevator(2, current_floor=2, direction=Direction.IDLE),
        ),
        passengers=(build_passenger(1, start_floor=5, destination_floor=1),),
    )

    decisions = NearestCarSameDirectionStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == ()
    assert decisions[1].assigned_passenger_ids == (1,)
    assert decisions[1].stop_floors == (5, 1)


def test_plan_assigns_nearest_car_same_direction_when_all_cars_are_moving_away() -> None:
    """Nearest-car same-direction still assigns a passenger when every car must reverse before pickup."""
    state = build_snapshot(
        elevators=(
            build_elevator(1, current_floor=8, direction=Direction.UP),
            build_elevator(2, current_floor=2, direction=Direction.DOWN),
        ),
        passengers=(build_passenger(1, start_floor=5, destination_floor=1),),
    )

    decisions = NearestCarSameDirectionStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1,)
    assert decisions[1].assigned_passenger_ids == ()
    assert decisions[0].stop_floors == (5, 1)
    assert decisions[1].stop_floors == ()


def test_plan_orders_stops_for_existing_riders_and_new_pickups() -> None:
    """Nearest-car same-direction defers an assigned opposite-direction pickup until after reversing."""
    state = build_snapshot(
        elevators=(build_elevator(1, current_floor=3, direction=Direction.UP, assigned_passenger_ids=(2,)),),
        passengers=(
            build_passenger(1, start_floor=0, destination_floor=7, status=PassengerStatus.RIDING, elevator_id=1),
            build_passenger(2, start_floor=5, destination_floor=1),
        ),
    )

    decisions = NearestCarSameDirectionStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (2,)
    assert decisions[0].stop_floors == (7,)


def test_plan_schedules_next_waiting_pickup_with_direction_hint() -> None:
    """Nearest-car same-direction queues the next pickup with a destination direction hint."""
    state = build_snapshot(
        elevators=(build_elevator(1, current_floor=0, direction=Direction.IDLE),),
        passengers=(
            build_passenger(1, start_floor=1, destination_floor=9),
            build_passenger(2, start_floor=5, destination_floor=2),
        ),
    )

    decisions = NearestCarSameDirectionStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1, 2)
    assert decisions[0].stop_floors == (1, 9)


def test_plan_uses_simple_pickup_then_destination_queue_for_same_floor_pickups() -> None:
    """Nearest-car relies on the simulation to defer wrong-direction boarding at a shared pickup floor."""
    state = build_snapshot(
        elevators=(build_elevator(1, current_floor=5, direction=Direction.UP, assigned_passenger_ids=(3, 5)),),
        passengers=(
            build_passenger(3, start_floor=5, destination_floor=0),
            build_passenger(5, start_floor=5, destination_floor=6),
        ),
    )

    decisions = NearestCarSameDirectionStrategy().plan(state)

    assert decisions[0].stop_floors == (5, 6)
