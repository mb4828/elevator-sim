"""Strategy decision application helpers."""

from __future__ import annotations

from elevator_sim.core.models import Elevator, Passenger, PassengerStatus
from elevator_sim.simulation.events import apply_direction
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
        apply_direction(elevator, decision.direction, floors)
        assign_passengers(passengers, elevator, decision.assigned_passenger_ids, assigned_elevator_ids)


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
