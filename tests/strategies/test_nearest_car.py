"""Tests for nearest-car elevator scheduling."""

from elevator_sim.core.models import (
    Direction,
    ElevatorServicePhase,
    ElevatorSnapshot,
    PassengerSnapshot,
    PassengerStatus,
    SimulationSnapshot,
)
from elevator_sim.strategies.nearest_car import NearestCarStrategy


def _elevator(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    elevator_id: int,
    current_floor: int,
    direction: Direction = Direction.IDLE,
    passenger_count: int = 0,
    capacity: int = 4,
    target_floors: tuple[int, ...] = (),
    assigned_passenger_ids: tuple[int, ...] = (),
) -> ElevatorSnapshot:
    """Build an elevator snapshot for strategy tests."""
    return ElevatorSnapshot(
        id=elevator_id,
        current_floor=current_floor,
        direction=direction,
        service_phase=ElevatorServicePhase.MOVING,
        passenger_count=passenger_count,
        capacity=capacity,
        target_floors=target_floors,
        assigned_passenger_ids=assigned_passenger_ids,
    )


def _passenger(
    passenger_id: int,
    start_floor: int,
    destination_floor: int,
    status: PassengerStatus = PassengerStatus.WAITING,
    elevator_id: int | None = None,
) -> PassengerSnapshot:
    """Build a passenger snapshot for strategy tests."""
    return PassengerSnapshot(
        id=passenger_id,
        request_time=0,
        start_floor=start_floor,
        destination_floor=destination_floor,
        status=status,
        elevator_id=elevator_id,
        pickup_time=None,
        dropoff_time=None,
    )


def _snapshot(
    elevators: tuple[ElevatorSnapshot, ...],
    passengers: tuple[PassengerSnapshot, ...],
) -> SimulationSnapshot:
    """Build a simulation snapshot for strategy tests."""
    return SimulationSnapshot(time=0, floors=10, elevators=elevators, passengers=passengers, complete=False)


def test_plan_assigns_passenger_to_nearest_elevator_moving_toward_start_floor() -> None:
    """Nearest-car assigns to the closest elevator moving toward the passenger's requested direction."""
    state = _snapshot(
        elevators=(
            _elevator(1, current_floor=1, direction=Direction.UP),
            _elevator(2, current_floor=7, direction=Direction.DOWN),
        ),
        passengers=(_passenger(1, start_floor=5, destination_floor=8),),
    )

    decisions = NearestCarStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1,)
    assert decisions[0].stop_floors == (5, 8)
    assert decisions[1].assigned_passenger_ids == ()


def test_plan_prefers_idle_car_over_closer_wrong_direction_moving_car() -> None:
    """Nearest-car does not stop a moving car for an opposite-direction pickup."""
    state = _snapshot(
        elevators=(
            _elevator(1, current_floor=4, direction=Direction.UP),
            _elevator(2, current_floor=0, direction=Direction.IDLE),
        ),
        passengers=(_passenger(1, start_floor=5, destination_floor=1),),
    )

    decisions = NearestCarStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == ()
    assert decisions[1].assigned_passenger_ids == (1,)
    assert decisions[1].stop_floors == (5, 1)


def test_plan_uses_idle_elevator_when_moving_elevators_are_not_traveling_toward_passenger() -> None:
    """Nearest-car uses idle elevators when moving elevators would need to reverse before pickup."""
    state = _snapshot(
        elevators=(
            _elevator(1, current_floor=8, direction=Direction.UP),
            _elevator(2, current_floor=2, direction=Direction.IDLE),
        ),
        passengers=(_passenger(1, start_floor=5, destination_floor=1),),
    )

    decisions = NearestCarStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == ()
    assert decisions[1].assigned_passenger_ids == (1,)
    assert decisions[1].stop_floors == (5, 1)


def test_plan_leaves_passenger_waiting_when_all_cars_are_moving_away() -> None:
    """Nearest-car leaves a passenger unassigned rather than pulling a car off its route to reverse."""
    state = _snapshot(
        elevators=(
            _elevator(1, current_floor=8, direction=Direction.UP),
            _elevator(2, current_floor=2, direction=Direction.DOWN),
        ),
        passengers=(_passenger(1, start_floor=5, destination_floor=1),),
    )

    decisions = NearestCarStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == ()
    assert decisions[1].assigned_passenger_ids == ()
    assert decisions[0].stop_floors == ()
    assert decisions[1].stop_floors == ()


def test_plan_orders_stops_for_existing_riders_and_new_pickups() -> None:
    """Nearest-car waits to pick up an already-assigned opposite-direction passenger until after reversing."""
    state = _snapshot(
        elevators=(_elevator(1, current_floor=3, direction=Direction.UP, assigned_passenger_ids=(2,)),),
        passengers=(
            _passenger(1, start_floor=0, destination_floor=7, status=PassengerStatus.RIDING, elevator_id=1),
            _passenger(2, start_floor=5, destination_floor=1),
        ),
    )

    decisions = NearestCarStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (2,)
    assert decisions[0].stop_floors == (7, 5, 1)


def test_plan_places_new_passenger_destinations_after_pickup_floors() -> None:
    """Nearest-car never schedules a new passenger's destination before their pickup."""
    state = _snapshot(
        elevators=(_elevator(1, current_floor=0, direction=Direction.IDLE),),
        passengers=(
            _passenger(1, start_floor=1, destination_floor=9),
            _passenger(2, start_floor=5, destination_floor=2),
        ),
    )

    decisions = NearestCarStrategy().plan(state)

    assert decisions[0].assigned_passenger_ids == (1, 2)
    assert decisions[0].stop_floors == (1, 5, 9, 2)


def test_plan_finishes_current_sweep_before_reversing_for_same_floor_pickups() -> None:
    """A car sweeping up serves an up-bound rider's destination before reversing for a down-bound pickup.

    Both passengers board at floor 5, but the up-bound one (5->6) belongs to the current up sweep and
    the down-bound one (5->0) to the reverse sweep, so the queue must go up to 6 before down to 0.
    """
    state = _snapshot(
        elevators=(_elevator(1, current_floor=5, direction=Direction.UP, assigned_passenger_ids=(3, 5)),),
        passengers=(
            _passenger(3, start_floor=5, destination_floor=0),
            _passenger(5, start_floor=5, destination_floor=6),
        ),
    )

    decisions = NearestCarStrategy().plan(state)

    assert decisions[0].stop_floors == (5, 6, 0)
