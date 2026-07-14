"""Tests for workload generation and strategy comparison helpers."""

from pathlib import Path

import pytest

from elevator_sim.core.metrics import MetricsSummary, PerformanceSummary, SimulationResult
from elevator_sim.core.models import Elevator, PassengerStatus, SimulationSnapshot
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy
from elevator_sim.workload.base import PassengerSource
from elevator_sim.workload.comparison import (
    StrategyComparisonResult,
    WorkloadConfig,
    build_summary_statistics_table,
    build_performance_analysis_table,
    build_service_quality_table,
    build_time_distribution_table,
    compare_strategies,
    create_workload_source,
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


def test_passenger_source_rejects_negative_duration() -> None:
    """Passenger source rejects a negative workload duration."""
    with pytest.raises(ValueError, match="duration must be non-negative"):
        PassengerSource(passengers=(), duration=-1)


def test_create_workload_source_loads_file_passengers(tmp_path: Path) -> None:
    """Workload source loads passengers from the configured CSV file."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,source,dest\n0,passenger1,1,2\n", encoding="utf-8")
    workload_config = WorkloadConfig(floors=5, input_file=input_file)

    source = create_workload_source(workload_config)

    assert len(source.passengers) == 1
    assert source.passengers[0].start_floor == 1
    assert source.passengers[0].destination_floor == 2


def test_create_workload_source_is_reproducible(tmp_path: Path) -> None:
    """File-backed passenger sources are reproducible for fair strategy comparisons."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,source,dest\n0,passenger1,1,2\n1,passenger2,2,3\n", encoding="utf-8")
    workload_config = WorkloadConfig(floors=5, input_file=input_file)
    first = create_workload_source(workload_config)
    second = create_workload_source(workload_config)

    assert first.passengers == second.passengers


def test_compare_strategies_runs_each_strategy_with_shared_workload(tmp_path: Path) -> None:
    """Comparison helper runs each strategy factory against identical file-backed passenger requests."""
    input_file = tmp_path / "workload.csv"
    input_file.write_text("time,id,source,dest\n0,passenger1,1,2\n1,passenger2,2,3\n", encoding="utf-8")
    workload_config = WorkloadConfig(floors=4, input_file=input_file)
    passenger_count = len(create_workload_source(workload_config).passengers)
    results = compare_strategies(
        workload_config=workload_config,
        elevator_factory=lambda: [Elevator(id=1, current_floor=1, capacity=4)],
        strategies={"complete": CompletingStrategy},
        max_ticks=40,
    )

    assert len(results) == 1
    assert results[0].strategy_name == "complete"
    assert results[0].result.metrics.completed_passengers == passenger_count


def test_build_summary_statistics_table_reports_passengers_and_total_ticks() -> None:
    """Summary table reports passenger count, total ticks, and passenger timing metrics."""
    table = build_summary_statistics_table(
        workload_size=2,
        results=[
            StrategyComparisonResult(
                strategy_name="strategy",
                result=SimulationResult(
                    ticks=12,
                    metrics=MetricsSummary(
                        completed_passengers=2,
                        average_wait_time=5.5,
                        minimum_wait_time=1,
                        maximum_wait_time=10,
                        p90_wait_time=9.0,
                        average_total_time=12.5,
                        minimum_total_time=8,
                        maximum_total_time=17,
                    ),
                    performance=PerformanceSummary(
                        total_ticks=12,
                        average_passengers_per_tick=0.0,
                        peak_queue=4,
                        total_riding_ticks=0,
                        total_capacity_ticks=1,
                        efficiency_score=0.0,
                        utilization=62.5,
                    ),
                    passengers=(),
                    state_log=(),
                ),
            )
        ],
    )

    assert [column.header for column in table.columns] == [
        "Strategy",
        "Passengers",
        "Total Ticks",
        "Wait Time\nMin",
        "Wait Time\nMax",
        "Wait Time\nAvg",
        "Total Time\nMin",
        "Total Time\nMax",
        "Total Time\nAvg",
    ]
    assert table.columns[1]._cells == ["2"]  # pylint: disable=protected-access
    assert table.columns[2]._cells == ["12"]  # pylint: disable=protected-access
    assert table.columns[8]._cells == ["12.50"]  # pylint: disable=protected-access


def test_build_time_distribution_table_reports_wait_and_total_time_percentiles() -> None:
    """Time distribution table reports p50 through p99 for wait and total times."""
    table = build_time_distribution_table(
        [
            StrategyComparisonResult(
                strategy_name="strategy",
                result=SimulationResult(
                    ticks=12,
                    metrics=MetricsSummary(
                        completed_passengers=10,
                        average_wait_time=5.5,
                        minimum_wait_time=1,
                        maximum_wait_time=10,
                        p50_wait_time=5.0,
                        p90_wait_time=9.0,
                        p95_wait_time=10.0,
                        p99_wait_time=10.0,
                        average_total_time=7.5,
                        minimum_total_time=3,
                        maximum_total_time=12,
                        p50_total_time=7.0,
                        p90_total_time=11.0,
                        p95_total_time=12.0,
                        p99_total_time=12.0,
                    ),
                    performance=PerformanceSummary(
                        total_ticks=12,
                        average_passengers_per_tick=0.0,
                        peak_queue=4,
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
        "Wait Time\nP50",
        "Wait Time\nP90",
        "Wait Time\nP95",
        "Wait Time\nP99",
        "Total Time\nP50",
        "Total Time\nP90",
        "Total Time\nP95",
        "Total Time\nP99",
    ]
    assert table.columns[1]._cells == ["5.00"]  # pylint: disable=protected-access
    assert table.columns[4]._cells == ["10.00"]  # pylint: disable=protected-access
    assert table.columns[8]._cells == ["12.00"]  # pylint: disable=protected-access


def test_build_service_quality_table_reports_fairness_overhead_and_worst_passenger() -> None:
    """Service quality table reports wait spread, overhead ratios, and the worst-served passenger."""
    table = build_service_quality_table(
        [
            StrategyComparisonResult(
                strategy_name="strategy",
                result=SimulationResult(
                    ticks=12,
                    metrics=MetricsSummary(
                        completed_passengers=10,
                        average_wait_time=5.5,
                        minimum_wait_time=1,
                        maximum_wait_time=10,
                        p90_wait_time=9.0,
                        wait_time_std_dev=2.87,
                        max_average_wait_ratio=1.82,
                        average_total_time=7.5,
                        minimum_total_time=3,
                        maximum_total_time=12,
                        average_overhead_ratio=1.5,
                        p95_overhead_ratio=2.0,
                        worst_passenger_id="passenger7",
                        worst_passenger_wait_time=10,
                        worst_passenger_total_time=12,
                    ),
                    performance=PerformanceSummary(
                        total_ticks=12,
                        average_passengers_per_tick=0.0,
                        peak_queue=4,
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
        "Wait Time\nStd Dev",
        "Wait Time\nMax/Avg",
        "Overhead\nAvg",
        "Overhead\nP95",
        "Worst Passenger\nID",
        "Worst Passenger\nWait",
        "Worst Passenger\nTotal",
    ]
    assert table.columns[1]._cells == ["2.87"]  # pylint: disable=protected-access
    assert table.columns[3]._cells == ["1.50"]  # pylint: disable=protected-access
    assert table.columns[5]._cells == ["passenger7"]  # pylint: disable=protected-access
    assert table.columns[7]._cells == ["12"]  # pylint: disable=protected-access


def test_build_performance_analysis_table_reports_utilization_and_wait_time() -> None:
    """Performance table reports peak queue and utilization alongside average and p90 wait time."""
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
                        peak_queue=7,
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
        "Peak Queue",
        "Utilization %",
        "Wait Time Avg",
        "Wait Time P90",
    ]
    assert table.columns[1]._cells == ["7"]  # pylint: disable=protected-access
    assert table.columns[2]._cells == ["62.50%"]  # pylint: disable=protected-access
    assert table.columns[3]._cells == ["5.50"]  # pylint: disable=protected-access
    assert table.columns[4]._cells == ["9.00"]  # pylint: disable=protected-access
