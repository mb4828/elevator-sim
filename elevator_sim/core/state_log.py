"""JSON state-log serialization for simulation timelines."""

import json
from pathlib import Path
from typing import Any

from elevator_sim.core.models import ElevatorSnapshot, PassengerSnapshot, SimulationSnapshot


def write_state_log(state_log: tuple[SimulationSnapshot, ...], output_path: Path) -> None:
    """Write a complete simulation state timeline to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps([snapshot_to_dict(snapshot) for snapshot in state_log], indent=2),
        encoding="utf-8",
    )


def snapshot_to_dict(snapshot: SimulationSnapshot) -> dict[str, Any]:
    """Convert a snapshot into a visualization-friendly dictionary."""
    return {
        "time": snapshot.time,
        "floors": snapshot.floors,
        "complete": snapshot.complete,
        "elevator_positions": {str(elevator.id): elevator.current_floor for elevator in snapshot.elevators},
        "elevators": [_elevator_to_dict(elevator) for elevator in snapshot.elevators],
        "passengers": [_passenger_to_dict(passenger) for passenger in snapshot.passengers],
    }


def _elevator_to_dict(elevator: ElevatorSnapshot) -> dict[str, Any]:
    """Convert an elevator snapshot into primitive JSON values."""
    return {
        "id": elevator.id,
        "current_floor": elevator.current_floor,
        "direction": elevator.direction.value,
        "service_phase": elevator.service_phase.value,
        "passenger_count": elevator.passenger_count,
        "capacity": elevator.capacity,
        "target_floors": list(elevator.target_floors),
        "assigned_passenger_ids": list(elevator.assigned_passenger_ids),
    }


def _passenger_to_dict(passenger: PassengerSnapshot) -> dict[str, Any]:
    """Convert a passenger snapshot into primitive JSON values."""
    return {
        "id": passenger.id,
        "request_time": passenger.request_time,
        "start_floor": passenger.start_floor,
        "destination_floor": passenger.destination_floor,
        "status": passenger.status.value,
        "elevator_id": passenger.elevator_id,
        "pickup_time": passenger.pickup_time,
        "dropoff_time": passenger.dropoff_time,
    }
