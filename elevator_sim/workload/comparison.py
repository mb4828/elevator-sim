"""Workload configuration and strategy comparison helpers."""

from collections.abc import Callable
from dataclasses import dataclass

from rich import box
from rich.table import Table

from elevator_sim.core.metrics import SimulationResult
from elevator_sim.core.models import Elevator
from elevator_sim.simulation import Simulation
from elevator_sim.strategies.base import ElevatorStrategy
from elevator_sim.workload.passenger_source import PassengerSource

ElevatorFactory = Callable[[], list[Elevator]]
StrategyFactory = Callable[[], ElevatorStrategy]


@dataclass(frozen=True)
class WorkloadConfig:
    """Configuration used to create identical seeded passenger workloads."""

    floors: int
    passengers: int
    duration: int
    seed: int


@dataclass(frozen=True)
class StrategyComparisonResult:
    """Result from running one strategy against a shared workload configuration."""

    strategy_name: str
    result: SimulationResult


def create_passenger_source(workload_config: WorkloadConfig) -> PassengerSource:
    """Create a passenger source from workload settings."""
    return PassengerSource(
        floors=workload_config.floors,
        duration=workload_config.duration,
        passengers=workload_config.passengers,
        seed=workload_config.seed,
    )


def compare_strategies(
    workload_config: WorkloadConfig,
    elevator_factory: ElevatorFactory,
    strategies: dict[str, StrategyFactory],
    max_ticks: int = 100_000,
) -> list[StrategyComparisonResult]:
    """Run each strategy against fresh elevators and identical seeded passenger sources."""
    results: list[StrategyComparisonResult] = []
    for name, strategy_factory in strategies.items():
        simulation = Simulation(
            floors=workload_config.floors,
            elevators=elevator_factory(),
            strategy=strategy_factory(),
            passenger_source=create_passenger_source(workload_config),
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
    table.add_column("Total Ticks", justify="right", no_wrap=True)
    table.add_column("Avg Passengers/Tick", justify="right", no_wrap=True)
    table.add_column("Peak Queue", justify="right", no_wrap=True)
    table.add_column("Efficiency Score", justify="right", no_wrap=True)

    for comparison in results:
        performance = comparison.result.performance
        table.add_row(
            comparison.strategy_name,
            str(performance.total_ticks),
            _format_float(performance.average_passengers_per_tick),
            str(performance.peak_queue),
            _format_efficiency_score(performance.efficiency_score),
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


def _format_efficiency_score(value: float) -> str:
    """Format efficiency score with Rich markup for threshold-based coloring."""
    if value < 50:
        color = "red"
    elif value < 80:
        color = "yellow"
    else:
        color = "green"
    return f"[{color}]{value:.2f}%[/{color}]"
