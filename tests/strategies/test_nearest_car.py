"""Tests for nearest-car elevator scheduling."""

from elevator_sim.core.models import Direction
from elevator_sim.strategies.nearest_car import NearestCarStrategy
from tests.strategies.conftest import build_elevator, build_passenger, build_snapshot


def test_plan_assigns_passenger_to_nearest_elevator_regardless_of_direction() -> None:
    """Nearest-car picks the closest elevator even when it is moving opposite the passenger request."""
    state = build_snapshot(
        elevators=(
            build_elevator(1, current_floor=8, direction=Direction.DOWN),
            build_elevator(2, current_floor=0, direction=Direction.IDLE),
        ),
        passengers=(build_passenger(1, start_floor=7, destination_floor=9),),
    )

    decisions = NearestCarStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1,)
    assert decisions[0].stop_floors == (7, 9)
    assert decisions[1].assigned_passenger_ids == ()


def test_plan_uses_elevator_id_as_nearest_tie_breaker() -> None:
    """Nearest-car uses elevator ID order when multiple cars are equally close."""
    state = build_snapshot(
        elevators=(
            build_elevator(2, current_floor=3),
            build_elevator(1, current_floor=7),
        ),
        passengers=(build_passenger(1, start_floor=5, destination_floor=9),),
    )

    decisions = NearestCarStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == ()
    assert decisions[1].assigned_passenger_ids == (1,)


def test_plan_preserves_existing_assignments() -> None:
    """Nearest-car keeps previously assigned passengers and assigns only new waiting passengers."""
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

    decisions = NearestCarStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1,)
    assert decisions[1].assigned_passenger_ids == (2,)
