"""Simulation result and metrics helpers."""

import math
from dataclasses import dataclass

from elevator_sim.core.models import Passenger, SimulationSnapshot


@dataclass(frozen=True)
class MetricsSummary:
    """Aggregate passenger timing metrics."""

    completed_passengers: int
    average_wait_time: float | None
    minimum_wait_time: int | None
    maximum_wait_time: int | None
    p90_wait_time: float | None
    average_total_time: float | None
    minimum_total_time: int | None
    maximum_total_time: int | None


@dataclass(frozen=True)
class PerformanceSummary:
    """Aggregate simulation performance metrics."""

    total_ticks: int
    average_passengers_per_tick: float
    peak_queue: int
    total_riding_ticks: int
    total_capacity_ticks: int
    efficiency_score: float
    utilization: float


@dataclass(frozen=True)
class SimulationResult:
    """Final simulation output."""

    ticks: int
    metrics: MetricsSummary
    performance: PerformanceSummary
    passengers: tuple[Passenger, ...]
    state_log: tuple[SimulationSnapshot, ...]


def summarize_metrics(passengers: list[Passenger]) -> MetricsSummary:
    """Build summary metrics from passenger timestamps."""
    completed = [passenger for passenger in passengers if passenger.dropoff_time is not None]
    wait_times = [passenger.wait_time for passenger in completed if passenger.wait_time is not None]
    total_times = [passenger.total_time for passenger in completed if passenger.total_time is not None]

    return MetricsSummary(
        completed_passengers=len(completed),
        average_wait_time=_average(wait_times),
        minimum_wait_time=min(wait_times) if wait_times else None,
        maximum_wait_time=max(wait_times) if wait_times else None,
        p90_wait_time=_percentile(sorted(wait_times), 90),
        average_total_time=_average(total_times),
        minimum_total_time=min(total_times) if total_times else None,
        maximum_total_time=max(total_times) if total_times else None,
    )


def summarize_performance(
    total_ticks: int,
    total_riding_ticks: int,
    total_capacity_ticks: int,
    peak_queue: int,
    total_active_elevator_ticks: int,
    total_elevator_ticks: int,
) -> PerformanceSummary:
    """Build performance metrics from simulation run counters."""
    average_passengers_per_tick = total_riding_ticks / total_ticks if total_ticks else 0.0
    efficiency_score = (total_riding_ticks / total_capacity_ticks) * 100 if total_capacity_ticks else 0.0
    utilization = (total_active_elevator_ticks / total_elevator_ticks) * 100 if total_elevator_ticks else 0.0
    return PerformanceSummary(
        total_ticks=total_ticks,
        average_passengers_per_tick=average_passengers_per_tick,
        peak_queue=peak_queue,
        total_riding_ticks=total_riding_ticks,
        total_capacity_ticks=total_capacity_ticks,
        efficiency_score=efficiency_score,
        utilization=utilization,
    )


def _average(values: list[int]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _percentile(sorted_values: list[int], percentile: float) -> float | None:
    """Return the given percentile from already-sorted values using the nearest-rank method."""
    if not sorted_values:
        return None
    rank = math.ceil(percentile / 100 * len(sorted_values))
    index = max(rank - 1, 0)
    return float(sorted_values[index])
