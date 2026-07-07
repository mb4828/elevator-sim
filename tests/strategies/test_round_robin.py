"""Tests for round-robin elevator scheduling."""

from elevator_sim.core.models import ElevatorServicePhase, PassengerStatus
from elevator_sim.strategies.round_robin import RoundRobinStrategy
from tests.strategies.conftest import build_elevator, build_passenger, build_snapshot


def test_plan_assigns_waiting_passengers_across_elevators_round_robin() -> None:
    """Round-robin assigns passenger one to elevator one, two to two, three to three, then wraps."""
    state = build_snapshot(
        elevators=(build_elevator(1), build_elevator(2), build_elevator(3)),
        passengers=(
            build_passenger(1, start_floor=1, destination_floor=7),
            build_passenger(2, start_floor=2, destination_floor=8),
            build_passenger(3, start_floor=3, destination_floor=9),
            build_passenger(4, start_floor=4, destination_floor=0),
        ),
    )

    decisions = RoundRobinStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1, 4)
    assert decisions[1].assigned_passenger_ids == (2,)
    assert decisions[2].assigned_passenger_ids == (3,)
    assert decisions[0].stop_floors == (1, 7, 4, 0)
    assert decisions[1].stop_floors == (2, 8)
    assert decisions[2].stop_floors == (3, 9)


def test_plan_preserves_existing_assignments_and_continues_cycle() -> None:
    """Round-robin keeps existing assigned passengers and assigns only new waiting passengers."""
    strategy = RoundRobinStrategy()
    first_state = build_snapshot(
        elevators=(build_elevator(1), build_elevator(2), build_elevator(3)),
        passengers=(
            build_passenger(1, start_floor=1, destination_floor=7),
            build_passenger(2, start_floor=2, destination_floor=8),
        ),
    )
    strategy.plan(first_state)
    second_state = build_snapshot(
        elevators=(
            build_elevator(1, assigned_passenger_ids=(1,)),
            build_elevator(2, assigned_passenger_ids=(2,)),
            build_elevator(3),
        ),
        passengers=(
            build_passenger(1, start_floor=1, destination_floor=7),
            build_passenger(2, start_floor=2, destination_floor=8),
            build_passenger(3, start_floor=3, destination_floor=9, request_time=1),
        ),
    )

    decisions = strategy.plan(second_state)

    assert decisions[0].assigned_passenger_ids == (1,)
    assert decisions[1].assigned_passenger_ids == (2,)
    assert decisions[2].assigned_passenger_ids == (3,)


def test_plan_includes_current_rider_destinations_before_new_pickups() -> None:
    """Round-robin keeps current rider destinations in the stop queue."""
    state = build_snapshot(
        elevators=(build_elevator(1),),
        passengers=(
            build_passenger(
                1,
                start_floor=0,
                destination_floor=6,
                status=PassengerStatus.RIDING,
                elevator_id=1,
            ),
            build_passenger(2, start_floor=3, destination_floor=1),
        ),
    )

    decisions = RoundRobinStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (2,)
    assert decisions[0].stop_floors == (6, 3, 1)


def test_plan_defers_current_floor_pickup_behind_onward_work() -> None:
    """Round-robin defers a current-floor opposite-direction pickup until after the onward sweep."""
    state = build_snapshot(
        elevators=(
            build_elevator(
                1,
                current_floor=2,
                assigned_passenger_ids=(1,),
                service_phase=ElevatorServicePhase.LOADING,
                target_floors=(2, 6),
            ),
        ),
        passengers=(
            build_passenger(1, start_floor=2, destination_floor=0),
            build_passenger(2, start_floor=4, destination_floor=8),
        ),
    )

    decisions = RoundRobinStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1, 2)
    assert decisions[0].stop_floors == (4, 8, 2, 0)


def test_plan_keeps_current_floor_pickup_when_it_matches_next_stop_direction() -> None:
    """Round-robin keeps boardable current-floor pickups during an existing stop."""
    state = build_snapshot(
        elevators=(
            build_elevator(
                1,
                current_floor=3,
                assigned_passenger_ids=(1, 2),
                service_phase=ElevatorServicePhase.STOPPING,
                target_floors=(3, 2, 1),
            ),
        ),
        passengers=(
            build_passenger(1, start_floor=3, destination_floor=1),
            build_passenger(2, start_floor=4, destination_floor=9),
        ),
    )

    decisions = RoundRobinStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1, 2)
    assert decisions[0].stop_floors == (3, 1, 4, 9)


def test_plan_keeps_current_floor_pickup_when_no_onward_work_exists() -> None:
    """Round-robin can still stop for an assigned current-floor passenger when there is nowhere else to go."""
    state = build_snapshot(
        elevators=(build_elevator(1, current_floor=2, assigned_passenger_ids=(1,)),),
        passengers=(build_passenger(1, start_floor=2, destination_floor=0),),
    )

    decisions = RoundRobinStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1,)
    assert decisions[0].stop_floors == (2, 0)


def test_plan_skips_pickup_stops_when_elevator_is_full() -> None:
    """Round-robin keeps a full elevator moving to rider destinations instead of pickup stops."""
    state = build_snapshot(
        elevators=(
            build_elevator(
                1,
                current_floor=3,
                assigned_passenger_ids=(2,),
                passenger_count=4,
                capacity=4,
            ),
        ),
        passengers=(
            build_passenger(1, start_floor=0, destination_floor=4, status=PassengerStatus.RIDING, elevator_id=1),
            build_passenger(2, start_floor=3, destination_floor=8),
        ),
    )

    decisions = RoundRobinStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (2,)
    assert decisions[0].stop_floors == (4,)
