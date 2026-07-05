"""Tests for workload generation and strategy comparison helpers."""

from elevator_sim.core.metrics import MetricsSummary, PerformanceSummary, SimulationResult
from elevator_sim.core.models import Elevator, PassengerStatus, SimulationSnapshot
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy
from elevator_sim.workload.comparison import (
    StrategyComparisonResult,
    WorkloadConfig,
    build_performance_analysis_table,
    compare_strategies,
    create_passenger_source,
)


class CompletingStrategy(ElevatorStrategy):
    """Test strategy that can finish generated one-passenger-at-a-time workloads."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        elevator = state.elevators[0]
        active = [passenger for passenger in state.passengers if passenger.status != PassengerStatus.COMPLETED]
        if not active:
            return [ElevatorDecision(elevator.id)]

        passenger = active[0]
        assigned = () if passenger.status == PassengerStatus.RIDING else (passenger.id,)
        target = passenger.destination_floor if passenger.status == PassengerStatus.RIDING else passenger.start_floor
        return [ElevatorDecision(elevator.id, stop_floors=(target,), assigned_passenger_ids=assigned)]


def test_create_passenger_source_is_reproducible() -> None:
    """Generated passenger sources are reproducible for fair strategy comparisons."""
    workload_config = WorkloadConfig(floors=5, duration=20, seed=7, passengers=8)
    first = create_passenger_source(workload_config)
    second = create_passenger_source(workload_config)

    assert first.passengers == second.passengers


def test_compare_strategies_runs_each_strategy_with_shared_workload() -> None:
    """Comparison helper runs each strategy factory against identical seeded passenger requests."""
    workload_config = WorkloadConfig(floors=4, duration=3, seed=1, passengers=3)
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


def test_build_performance_analysis_table_reports_utilization_and_wait_time() -> None:
    """Performance table reports elevator utilization alongside average and p90 wait time."""
    table = build_performance_analysis_table(
        [
            StrategyComparisonResult(
                strategy_name="strategy",
                result=SimulationResult(
                    ticks=1,
                    metrics=MetricsSummary(
                        completed_passengers=2,
                        average_wait_time=5.5,
                        minimum_wait_time=1,
                        maximum_wait_time=10,
                        p90_wait_time=9.0,
                        average_total_time=None,
                        minimum_total_time=None,
                        maximum_total_time=None,
                    ),
                    performance=PerformanceSummary(
                        total_ticks=1,
                        average_passengers_per_tick=0.0,
                        peak_queue=0,
                        total_riding_ticks=0,
                        total_capacity_ticks=1,
                        efficiency_score=0.0,
                        utilization=62.5,
                    ),
                    passengers=(),
                    state_log=(),
                ),
            )
        ]
    )

    assert [column.header for column in table.columns] == [
        "Strategy",
        "Total Ticks",
        "Avg Passengers/Tick",
        "Utilization %",
        "Wait Time Avg",
        "Wait Time P90",
    ]
    assert table.columns[3]._cells == ["62.50%"]  # pylint: disable=protected-access
    assert table.columns[4]._cells == ["5.50"]  # pylint: disable=protected-access
    assert table.columns[5]._cells == ["9.00"]  # pylint: disable=protected-access
