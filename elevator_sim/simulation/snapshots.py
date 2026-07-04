"""Immutable simulation snapshot builders."""

from elevator_sim.core.models import Elevator, ElevatorSnapshot, Passenger, PassengerSnapshot, SimulationSnapshot


def build_snapshot(
    time: int,
    floors: int,
    elevators: list[Elevator],
    passengers: dict[int, Passenger],
    complete: bool,
) -> SimulationSnapshot:
    """Build an immutable simulation snapshot."""
    return SimulationSnapshot(
        time=time,
        floors=floors,
        elevators=tuple(build_elevator_snapshot(elevator) for elevator in elevators),
        passengers=tuple(build_passenger_snapshot(passenger) for passenger in passengers.values()),
        complete=complete,
    )


def build_elevator_snapshot(elevator: Elevator) -> ElevatorSnapshot:
    """Build an immutable snapshot for one elevator."""
    return ElevatorSnapshot(
        id=elevator.id,
        current_floor=elevator.current_floor,
        direction=elevator.direction,
        service_phase=elevator.service_phase,
        passenger_count=len(elevator.passengers),
        capacity=elevator.capacity,
        target_floors=tuple(elevator.target_floors),
        assigned_passenger_ids=tuple(sorted(elevator.assigned_passenger_ids)),
    )


def build_passenger_snapshot(passenger: Passenger) -> PassengerSnapshot:
    """Build an immutable snapshot for one passenger."""
    return PassengerSnapshot(
        id=passenger.id,
        request_time=passenger.request_time,
        start_floor=passenger.start_floor,
        destination_floor=passenger.destination_floor,
        status=passenger.status,
        elevator_id=passenger.elevator_id,
        pickup_time=passenger.pickup_time,
        dropoff_time=passenger.dropoff_time,
    )
