"""Tests for workload generation and strategy comparison helpers."""

from elevator_sim.core.models import Direction, Elevator, PassengerStatus, SimulationSnapshot
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy
from elevator_sim.workload.comparison import WorkloadConfig, compare_strategies, create_passenger_source


class CompletingStrategy(ElevatorStrategy):
    """Test strategy that can finish generated one-passenger-at-a-time workloads."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        elevator = state.elevators[0]
        active = [passenger for passenger in state.passengers if passenger.status != PassengerStatus.COMPLETED]
        if not active:
            return [ElevatorDecision(elevator.id, Direction.IDLE)]

        passenger = active[0]
        assigned = () if passenger.status == PassengerStatus.RIDING else (passenger.id,)
        target = passenger.destination_floor if passenger.status == PassengerStatus.RIDING else passenger.start_floor
        return [ElevatorDecision(elevator.id, _direction_toward(elevator.current_floor, target), assigned)]


def test_create_passenger_source_is_reproducible() -> None:
    """Generated passenger sources are reproducible for fair strategy comparisons."""
    workload_config = WorkloadConfig(floors=5, duration=20, seed=7, arrival_probability=0.4)
    first = create_passenger_source(workload_config)
    second = create_passenger_source(workload_config)

    assert first.passengers == second.passengers


def test_compare_strategies_runs_each_strategy_with_shared_workload() -> None:
    """Comparison helper runs each strategy factory against identical seeded passenger requests."""
    workload_config = WorkloadConfig(floors=4, duration=3, seed=1, arrival_probability=1.0)
    passenger_count = len(create_passenger_source(workload_config).passengers)
    results = compare_strategies(
        workload_config=workload_config,
        elevator_factory=lambda: [Elevator(id=1, current_floor=1, capacity=4)],
        strategies={"complete": CompletingStrategy},
        max_ticks=40,
    )

    assert len(results) == 1
    assert results[0].strategy_name == "complete"
    assert results[0].result.metrics.completed_passengers == passenger_count


def _direction_toward(current_floor: int, target_floor: int) -> Direction:
    if target_floor > current_floor:
        return Direction.UP
    if target_floor < current_floor:
        return Direction.DOWN
    return Direction.IDLE
