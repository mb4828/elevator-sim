"""JSON state-log serialization for simulation timelines."""

import json
from pathlib import Path
from typing import Any

from elevator_sim.core.models import ElevatorSnapshot, PassengerSnapshot, PassengerStatus, SimulationSnapshot

VISIBLE_PASSENGER_STATUSES = frozenset((PassengerStatus.WAITING, PassengerStatus.RIDING))


def write_state_log(state_log: tuple[SimulationSnapshot, ...], output_path: Path) -> None:
    """Write a compact visualization state timeline to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(state_log_to_dict(state_log), separators=(",", ":")),
        encoding="utf-8",
    )


def state_log_to_dict(state_log: tuple[SimulationSnapshot, ...]) -> dict[str, Any]:
    """Convert a simulation state log into compact visualization data."""
    if not state_log:
        return {
            "version": 1,
            "floors": 0,
            "elevators": [],
            "passengers": [],
            "frames": [],
        }

    initial_snapshot = state_log[0]
    return {
        "version": 1,
        "floors": initial_snapshot.floors,
        "elevators": [_elevator_metadata_to_dict(elevator) for elevator in initial_snapshot.elevators],
        "passengers": _passenger_metadata(state_log),
        "frames": [_frame_to_dict(snapshot) for snapshot in state_log],
    }


def _frame_to_dict(snapshot: SimulationSnapshot) -> dict[str, Any]:
    """Convert a snapshot into one compact animation frame."""
    assigned_elevator_by_passenger_id = _assigned_elevator_by_passenger_id(snapshot.elevators)
    return {
        "time": snapshot.time,
        "complete": snapshot.complete,
        "elevators": [_elevator_frame_to_dict(elevator) for elevator in snapshot.elevators],
        "passengers": [
            _passenger_frame_to_dict(passenger, assigned_elevator_by_passenger_id)
            for passenger in snapshot.passengers
            if passenger.status in VISIBLE_PASSENGER_STATUSES
        ],
    }


def _elevator_metadata_to_dict(elevator: ElevatorSnapshot) -> dict[str, Any]:
    """Convert static elevator metadata into primitive JSON values."""
    return {
        "id": elevator.id,
        "capacity": elevator.capacity,
    }


def _passenger_metadata(state_log: tuple[SimulationSnapshot, ...]) -> list[dict[str, Any]]:
    """Return static passenger metadata once per passenger."""
    passengers_by_id: dict[int, PassengerSnapshot] = {}
    for snapshot in state_log:
        for passenger in snapshot.passengers:
            passengers_by_id.setdefault(passenger.id, passenger)

    return [_passenger_metadata_to_dict(passenger) for passenger in passengers_by_id.values()]


def _passenger_metadata_to_dict(passenger: PassengerSnapshot) -> dict[str, Any]:
    """Convert static passenger metadata into primitive JSON values."""
    return {
        "id": passenger.id,
        "request_time": passenger.request_time,
        "start_floor": passenger.start_floor,
        "destination_floor": passenger.destination_floor,
    }


def _elevator_frame_to_dict(elevator: ElevatorSnapshot) -> dict[str, Any]:
    """Convert per-frame elevator state into primitive JSON values."""
    return {
        "id": elevator.id,
        "floor": elevator.current_floor,
        "direction": elevator.direction.value,
        "phase": elevator.service_phase.value,
        "passenger_count": elevator.passenger_count,
        "target_floor": elevator.target_floors[0] if elevator.target_floors else None,
    }


def _assigned_elevator_by_passenger_id(elevators: tuple[ElevatorSnapshot, ...]) -> dict[int, int]:
    """Return the current elevator assignment for each waiting passenger."""
    return {passenger_id: elevator.id for elevator in elevators for passenger_id in elevator.assigned_passenger_ids}


def _passenger_frame_to_dict(
    passenger: PassengerSnapshot,
    assigned_elevator_by_passenger_id: dict[int, int],
) -> dict[str, Any]:
    """Convert per-frame passenger state into primitive JSON values."""
    return {
        "id": passenger.id,
        "status": passenger.status.value,
        "elevator_id": passenger.elevator_id or assigned_elevator_by_passenger_id.get(passenger.id),
    }
