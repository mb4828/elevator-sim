"""Strategy decision application helpers."""

from elevator_sim.core.models import Elevator, ElevatorServicePhase, Passenger, PassengerStatus
from elevator_sim.strategies.base import ElevatorDecision


def apply_decisions(
    elevators: list[Elevator],
    passengers: dict[int, Passenger],
    decisions: list[ElevatorDecision],
    floors: int,
) -> None:
    """Validate and apply strategy decisions to mutable simulation state."""
    elevator_by_id = {elevator.id: elevator for elevator in elevators}
    assigned_elevator_ids = build_assigned_elevator_index(elevators)
    seen_elevators: set[int] = set()
    for decision in decisions:
        if decision.elevator_id in seen_elevators:
            raise ValueError(f"duplicate decision for elevator {decision.elevator_id}")
        seen_elevators.add(decision.elevator_id)
        elevator = elevator_by_id.get(decision.elevator_id)
        if elevator is None:
            raise ValueError(f"unknown elevator ID in strategy decision: {decision.elevator_id}")
        apply_stop_floors(elevator, decision.stop_floors, floors)
        assign_passengers(passengers, elevator, decision.assigned_passenger_ids, assigned_elevator_ids)


def apply_stop_floors(elevator: Elevator, stop_floors: tuple[int, ...], floors: int) -> None:
    """Validate and apply an elevator's ordered stop queue."""
    normalized_stop_floors = normalize_stop_floors(stop_floors, floors)
    if elevator.service_phase in (ElevatorServicePhase.MOVING, ElevatorServicePhase.IDLE):
        elevator.target_floors = normalized_stop_floors
        return

    future_stop_floors = [floor for floor in normalized_stop_floors if floor != elevator.current_floor]
    elevator.target_floors = [elevator.current_floor, *future_stop_floors]


def normalize_stop_floors(stop_floors: tuple[int, ...], floors: int) -> list[int]:
    """Return valid stop floors with duplicates removed while preserving order."""
    normalized_stop_floors: list[int] = []
    seen_floors: set[int] = set()
    for stop_floor in stop_floors:
        if stop_floor < 0 or stop_floor >= floors:
            raise ValueError(f"stop floor is outside building bounds: {stop_floor}")
        if stop_floor not in seen_floors:
            normalized_stop_floors.append(stop_floor)
            seen_floors.add(stop_floor)
    return normalized_stop_floors


def assign_passengers(
    passengers: dict[int, Passenger],
    elevator: Elevator,
    passenger_ids: tuple[int, ...],
    assigned_elevator_ids: dict[int, int],
) -> None:
    """Assign waiting passengers to one elevator."""
    for passenger_id in passenger_ids:
        passenger = passengers.get(passenger_id)
        if passenger is None:
            raise ValueError(f"unknown passenger ID in strategy decision: {passenger_id}")
        if passenger.status != PassengerStatus.WAITING:
            raise ValueError(f"passenger {passenger_id} is not waiting")
        if assigned_elevator_ids.get(passenger_id) not in (None, elevator.id):
            raise ValueError(f"passenger {passenger_id} is already assigned to another elevator")
        elevator.assigned_passenger_ids.add(passenger_id)
        assigned_elevator_ids[passenger_id] = elevator.id


def build_assigned_elevator_index(elevators: list[Elevator]) -> dict[int, int]:
    """Return current passenger assignment ownership by passenger ID."""
    assigned_elevator_ids: dict[int, int] = {}
    for elevator in elevators:
        for passenger_id in elevator.assigned_passenger_ids:
            assigned_elevator_ids[passenger_id] = elevator.id
    return assigned_elevator_ids
