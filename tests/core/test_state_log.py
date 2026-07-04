"""Tests for compact state-log serialization."""

import json

from elevator_sim.core.models import (
    Direction,
    ElevatorServicePhase,
    ElevatorSnapshot,
    PassengerSnapshot,
    PassengerStatus,
    SimulationSnapshot,
)
from elevator_sim.core.state_log import write_state_log


def test_write_state_log_creates_visualization_json(tmp_path) -> None:
    """State-log writer persists compact visualization metadata and active passenger frames."""
    state_log = (
        _snapshot(time=0, passenger_status=PassengerStatus.SCHEDULED, complete=False),
        _snapshot(time=1, passenger_status=PassengerStatus.WAITING, complete=False),
        _snapshot(time=2, passenger_status=PassengerStatus.RIDING, elevator_id=1, passenger_count=1, complete=False),
        _snapshot(time=3, passenger_status=PassengerStatus.COMPLETED, complete=True),
    )
    output_path = tmp_path / "_log.json"

    write_state_log(state_log, output_path)

    data = json.loads(output_path.read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["floors"] == 3
    assert data["elevators"] == [{"id": 1, "capacity": 2}]
    assert data["passengers"] == [
        {"id": 1, "request_time": 0, "start_floor": 1, "destination_floor": 2}
    ]
    assert data["frames"][0]["time"] == 0
    assert data["frames"][0]["elevators"] == [
        {"id": 1, "floor": 1, "direction": "idle", "phase": "moving", "passenger_count": 0}
    ]
    assert data["frames"][1]["passengers"] == [{"id": 1, "status": "waiting", "elevator_id": None}]
    assert data["frames"][2]["passengers"] == [{"id": 1, "status": "riding", "elevator_id": 1}]
    assert data["frames"][-1]["complete"] is True
    assert data["frames"][-1]["passengers"] == []
    assert "elevator_positions" not in data["frames"][0]
    assert "capacity" not in data["frames"][0]["elevators"][0]
    assert "request_time" not in data["frames"][1]["passengers"][0]


def _snapshot(
    *,
    time: int,
    passenger_status: PassengerStatus,
    complete: bool,
    elevator_id: int | None = None,
    passenger_count: int = 0,
) -> SimulationSnapshot:
    """Build a simulation snapshot for state-log serialization tests."""
    return SimulationSnapshot(
        time=time,
        floors=3,
        elevators=(
            ElevatorSnapshot(
                id=1,
                current_floor=1,
                direction=Direction.IDLE,
                service_phase=ElevatorServicePhase.MOVING,
                passenger_count=passenger_count,
                capacity=2,
                target_floors=(),
                assigned_passenger_ids=(),
            ),
        ),
        passengers=(
            PassengerSnapshot(
                id=1,
                request_time=0,
                start_floor=1,
                destination_floor=2,
                status=passenger_status,
                elevator_id=elevator_id,
                pickup_time=2 if passenger_status in {PassengerStatus.RIDING, PassengerStatus.COMPLETED} else None,
                dropoff_time=3 if passenger_status == PassengerStatus.COMPLETED else None,
            ),
        ),
        complete=complete,
    )
