"""Workload configuration and strategy comparison helpers."""

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from rich import box
from rich.table import Table

from elevator_sim.core.metrics import SimulationResult
from elevator_sim.core.models import Elevator
from elevator_sim.simulation import Simulation
from elevator_sim.strategies.base import ElevatorStrategy
from elevator_sim.workload.base import PassengerSource
from elevator_sim.workload.file_source import FileSource

ElevatorFactory = Callable[[], list[Elevator]]
StrategyFactory = Callable[[], ElevatorStrategy]


@dataclass(frozen=True)
class WorkloadConfig:
    """Configuration used to create identical file-backed passenger workloads."""

    floors: int
    input_file: Path


@dataclass(frozen=True)
class StrategyComparisonResult:
    """Result from running one strategy against a shared workload configuration."""

    strategy_name: str
    result: SimulationResult


def create_workload_source(workload_config: WorkloadConfig) -> PassengerSource:
    """Create a passenger source from workload settings."""
    return FileSource(workload_config.input_file)


def compare_strategies(
    workload_config: WorkloadConfig,
    elevator_factory: ElevatorFactory,
    strategies: dict[str, StrategyFactory],
    max_ticks: int = 100_000,
) -> list[StrategyComparisonResult]:
    """Run each strategy against fresh elevators and identical file-backed passenger sources."""
    results: list[StrategyComparisonResult] = []
    for name, strategy_factory in strategies.items():
        simulation = Simulation(
            floors=workload_config.floors,
            elevators=elevator_factory(),
            strategy=strategy_factory(),
            passenger_source=create_workload_source(workload_config),
        )
        results.append(
            StrategyComparisonResult(
                strategy_name=name,
                result=simulation.run(max_ticks=max_ticks),
            )
        )
    return results


def build_summary_statistics_table(workload_size: int, results: list[StrategyComparisonResult]) -> Table:
    """Build a passenger timing summary table."""
    table = Table(title="Summary Statistics", box=box.SQUARE_DOUBLE_HEAD)
    table.add_column("Strategy", no_wrap=True)
    table.add_column("Passengers", justify="right", no_wrap=True)
    table.add_column("Total Ticks", justify="right", no_wrap=True)
    table.add_column("Wait Time\nMin", justify="right", no_wrap=True)
    table.add_column("Wait Time\nMax", justify="right", no_wrap=True)
    table.add_column("Wait Time\nAvg", justify="right", no_wrap=True)
    table.add_column("Total Time\nMin", justify="right", no_wrap=True)
    table.add_column("Total Time\nMax", justify="right", no_wrap=True)
    table.add_column("Total Time\nAvg", justify="right", no_wrap=True)

    for comparison in results:
        metrics = comparison.result.metrics
        table.add_row(
            comparison.strategy_name,
            str(workload_size),
            str(comparison.result.performance.total_ticks),
            _format_int(metrics.minimum_wait_time),
            _format_int(metrics.maximum_wait_time),
            _format_float(metrics.average_wait_time),
            _format_int(metrics.minimum_total_time),
            _format_int(metrics.maximum_total_time),
            _format_float(metrics.average_total_time),
        )
    return table


def build_performance_analysis_table(results: list[StrategyComparisonResult]) -> Table:
    """Build a simulation performance analysis table."""
    table = Table(title="Performance Analysis", box=box.SQUARE_DOUBLE_HEAD)
    table.add_column("Strategy", no_wrap=True)
    table.add_column("Peak Queue", justify="right", no_wrap=True)
    table.add_column("Utilization %", justify="right", no_wrap=True)
    table.add_column("Wait Time Avg", justify="right", no_wrap=True)
    table.add_column("Wait Time P90", justify="right", no_wrap=True)

    for comparison in results:
        performance = comparison.result.performance
        metrics = comparison.result.metrics
        table.add_row(
            comparison.strategy_name,
            str(performance.peak_queue),
            f"{performance.utilization:.2f}%",
            _format_float(metrics.average_wait_time),
            _format_float(metrics.p90_wait_time),
        )
    return table


def _format_int(value: int | None) -> str:
    """Format optional integer metrics for table output."""
    if value is None:
        return "-"
    return str(value)


def _format_float(value: float | None) -> str:
    """Format optional floating point metrics for table output."""
    if value is None:
        return "-"
    return f"{value:.2f}"
