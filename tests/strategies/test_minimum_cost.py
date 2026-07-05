"""Tests for minimum-cost elevator scheduling."""

from elevator_sim.core.models import Direction, ElevatorServicePhase, PassengerStatus
from elevator_sim.strategies.minimum_cost import MinimumCostStrategy
from tests.strategies.conftest import build_elevator, build_passenger, build_snapshot


def test_plan_assigns_passenger_to_cheapest_idle_elevator() -> None:
    """Minimum-cost assigns to the closest idle elevator and queues the pickup with a direction hint."""
    state = build_snapshot(
        elevators=(
            build_elevator(1, current_floor=0),
            build_elevator(2, current_floor=8),
        ),
        passengers=(build_passenger(1, start_floor=2, destination_floor=5),),
    )

    decisions = MinimumCostStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1,)
    assert decisions[0].stop_floors == (2, 5)
    assert decisions[1].assigned_passenger_ids == ()
    assert decisions[1].stop_floors == ()


def test_plan_prefers_elevator_already_sweeping_toward_passenger() -> None:
    """Minimum-cost penalizes cars moving against the passenger's requested direction."""
    state = build_snapshot(
        elevators=(
            build_elevator(1, current_floor=4, direction=Direction.UP),
            build_elevator(2, current_floor=6, direction=Direction.DOWN),
        ),
        passengers=(build_passenger(1, start_floor=5, destination_floor=7),),
    )

    decisions = MinimumCostStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1,)
    assert decisions[1].assigned_passenger_ids == ()


def test_plan_avoids_full_elevator_when_a_nearby_car_has_room() -> None:
    """Minimum-cost steers new assignments away from a full car even when it is closer."""
    state = build_snapshot(
        elevators=(
            build_elevator(1, current_floor=3, passenger_count=4, capacity=4),
            build_elevator(2, current_floor=4),
        ),
        passengers=(build_passenger(1, start_floor=3, destination_floor=5),),
    )

    decisions = MinimumCostStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == ()
    assert decisions[1].assigned_passenger_ids == (1,)


def test_plan_preserves_existing_assignments() -> None:
    """Minimum-cost keeps previously assigned passengers and assigns only new waiting passengers."""
    state = build_snapshot(
        elevators=(
            build_elevator(1, current_floor=0, assigned_passenger_ids=(1,)),
            build_elevator(2, current_floor=8),
        ),
        passengers=(
            build_passenger(1, start_floor=0, destination_floor=4),
            build_passenger(2, start_floor=7, destination_floor=1, request_time=1),
        ),
    )

    decisions = MinimumCostStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1,)
    assert decisions[1].assigned_passenger_ids == (2,)


def test_plan_pools_identical_requests_onto_one_car() -> None:
    """Minimum-cost boards identical origin/destination requests together instead of dispatching a second car."""
    state = build_snapshot(
        elevators=(
            build_elevator(1, current_floor=2),
            build_elevator(2, current_floor=2),
        ),
        passengers=(
            build_passenger(1, start_floor=2, destination_floor=8),
            build_passenger(2, start_floor=2, destination_floor=8),
        ),
    )

    decisions = MinimumCostStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1, 2)
    assert decisions[1].assigned_passenger_ids == ()


def test_plan_keeps_rider_destinations_in_stop_queue() -> None:
    """Minimum-cost keeps current rider destinations ahead of far-away new pickups."""
    state = build_snapshot(
        elevators=(build_elevator(1, current_floor=3, direction=Direction.UP, passenger_count=1),),
        passengers=(
            build_passenger(1, start_floor=0, destination_floor=6, status=PassengerStatus.RIDING, elevator_id=1),
            build_passenger(2, start_floor=9, destination_floor=0),
        ),
    )

    decisions = MinimumCostStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (2,)
    assert decisions[0].stop_floors == (6,)


def test_plan_preserves_onward_rider_stop_while_unloading_current_floor() -> None:
    """Minimum-cost keeps a future rider destination queued while unloading at the current floor."""
    state = build_snapshot(
        elevators=(
            build_elevator(
                1,
                current_floor=3,
                service_phase=ElevatorServicePhase.UNLOADING,
                passenger_count=2,
                target_floors=(3,),
            ),
        ),
        passengers=(
            build_passenger(1, start_floor=5, destination_floor=3, status=PassengerStatus.RIDING, elevator_id=1),
            build_passenger(2, start_floor=4, destination_floor=2, status=PassengerStatus.RIDING, elevator_id=1),
        ),
    )

    decisions = MinimumCostStrategy().plan(state)

    assert decisions[0].stop_floors == (3, 2)
