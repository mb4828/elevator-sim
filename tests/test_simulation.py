"""Tests for the discrete-time simulation engine."""

import pytest

from elevator_sim.core.models import Direction, Elevator, PassengerStatus, SimulationSnapshot
from elevator_sim.simulation import Simulation
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy
from elevator_sim.workload.passenger_source import PassengerSource


class DirectPassengerStrategy(ElevatorStrategy):
    """Test strategy that assigns one passenger and follows pickup/drop-off floors."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        elevator = state.elevators[0]
        passenger = next(
            passenger for passenger in state.passengers if passenger.status != PassengerStatus.COMPLETED
        )
        assigned_ids = () if passenger.status == PassengerStatus.RIDING else (passenger.id,)
        target_floor = (
            passenger.destination_floor
            if passenger.status == PassengerStatus.RIDING
            else passenger.start_floor
        )
        return [ElevatorDecision(elevator.id, _direction_toward(elevator.current_floor, target_floor), assigned_ids)]


class InvalidElevatorStrategy(ElevatorStrategy):
    """Test strategy that references a missing elevator."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        return [ElevatorDecision(elevator_id=999, direction=Direction.IDLE)]


class BoundaryStrategy(ElevatorStrategy):
    """Test strategy that repeatedly tries to move past the top floor."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        return [ElevatorDecision(elevator_id=1, direction=Direction.UP)]


def test_run_completes_single_passenger_trip() -> None:
    """Simulation releases, picks up, moves, drops off, and records metrics."""
    passenger_source = PassengerSource(floors=5, arrival_probability=1.0, duration=1, seed=1)
    simulation = Simulation(
        floors=5,
        elevators=[Elevator(id=1, current_floor=1, capacity=4)],
        strategy=DirectPassengerStrategy(),
        passenger_source=passenger_source,
    )

    result = simulation.run(max_ticks=10)

    assert result.metrics.completed_passengers == 1
    assert result.passengers[0].status == PassengerStatus.COMPLETED


def test_step_clamps_illegal_boundary_movement() -> None:
    """Simulation prevents a strategy from moving an elevator outside floor bounds."""
    simulation = Simulation(
        floors=2,
        elevators=[Elevator(id=1, current_floor=2, capacity=1)],
        strategy=BoundaryStrategy(),
        passenger_source=PassengerSource(floors=2, arrival_probability=0.0, duration=0, seed=1),
    )

    snapshot = simulation.step()

    assert snapshot.elevators[0].current_floor == 2
    assert snapshot.elevators[0].direction == Direction.IDLE


def test_unknown_elevator_decision_raises_error() -> None:
    """Simulation rejects strategy decisions for missing elevators."""
    simulation = Simulation(
        floors=3,
        elevators=[Elevator(id=1, current_floor=1, capacity=1)],
        strategy=InvalidElevatorStrategy(),
        passenger_source=PassengerSource(floors=3, arrival_probability=1.0, duration=1, seed=1),
    )

    with pytest.raises(ValueError, match="unknown elevator ID"):
        simulation.step()


def _direction_toward(current_floor: int, target_floor: int) -> Direction:
    if target_floor > current_floor:
        return Direction.UP
    if target_floor < current_floor:
        return Direction.DOWN
    return Direction.IDLE
