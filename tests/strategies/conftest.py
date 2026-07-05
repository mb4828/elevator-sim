"""Shared snapshot builders for strategy tests."""

from elevator_sim.core.models import (
    Direction,
    ElevatorServicePhase,
    ElevatorSnapshot,
    PassengerSnapshot,
    PassengerStatus,
    SimulationSnapshot,
)


def build_elevator(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    elevator_id: int,
    current_floor: int = 0,
    direction: Direction = Direction.IDLE,
    service_phase: ElevatorServicePhase = ElevatorServicePhase.IDLE,
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
        service_phase=service_phase,
        passenger_count=passenger_count,
        capacity=capacity,
        target_floors=target_floors,
        assigned_passenger_ids=assigned_passenger_ids,
    )


def build_passenger(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    passenger_id: int,
    start_floor: int,
    destination_floor: int,
    request_time: int = 0,
    status: PassengerStatus = PassengerStatus.WAITING,
    elevator_id: int | None = None,
) -> PassengerSnapshot:
    """Build a passenger snapshot for strategy tests."""
    return PassengerSnapshot(
        id=passenger_id,
        request_time=request_time,
        start_floor=start_floor,
        destination_floor=destination_floor,
        status=status,
        elevator_id=elevator_id,
        pickup_time=None,
        dropoff_time=None,
    )


def build_snapshot(
    elevators: tuple[ElevatorSnapshot, ...],
    passengers: tuple[PassengerSnapshot, ...],
) -> SimulationSnapshot:
    """Build a simulation snapshot for strategy tests."""
    return SimulationSnapshot(time=0, floors=10, elevators=elevators, passengers=passengers, complete=False)
