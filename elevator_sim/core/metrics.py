"""Simulation result and metrics helpers."""

import math
import statistics
from dataclasses import dataclass

from elevator_sim.core.models import Passenger, SimulationSnapshot

# Guaranteed per-trip service overhead: one stopping tick plus one unloading tick
# at the destination. Pickup dwell ticks can be shared with other passengers'
# service, so they are not part of the per-passenger lower bound.
MINIMUM_SERVICE_TICKS = 2


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
    p50_wait_time: float | None = None
    p95_wait_time: float | None = None
    p99_wait_time: float | None = None
    wait_time_std_dev: float | None = None
    max_average_wait_ratio: float | None = None
    p50_total_time: float | None = None
    p90_total_time: float | None = None
    p95_total_time: float | None = None
    p99_total_time: float | None = None
    average_overhead_ratio: float | None = None
    p95_overhead_ratio: float | None = None
    worst_passenger_id: str | None = None
    worst_passenger_wait_time: int | None = None
    worst_passenger_total_time: int | None = None


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
    wait_times = sorted(passenger.wait_time for passenger in completed if passenger.wait_time is not None)
    total_times = sorted(passenger.total_time for passenger in completed if passenger.total_time is not None)
    overhead_ratios = sorted(_overhead_ratio(passenger) for passenger in completed if passenger.total_time is not None)
    average_wait_time = _average(wait_times)
    maximum_wait_time = max(wait_times) if wait_times else None
    worst_passenger = _worst_passenger(completed)

    return MetricsSummary(
        completed_passengers=len(completed),
        average_wait_time=average_wait_time,
        minimum_wait_time=min(wait_times) if wait_times else None,
        maximum_wait_time=maximum_wait_time,
        p50_wait_time=_percentile(wait_times, 50),
        p90_wait_time=_percentile(wait_times, 90),
        p95_wait_time=_percentile(wait_times, 95),
        p99_wait_time=_percentile(wait_times, 99),
        wait_time_std_dev=statistics.pstdev(wait_times) if wait_times else None,
        max_average_wait_ratio=_ratio(maximum_wait_time, average_wait_time),
        average_total_time=_average(total_times),
        minimum_total_time=min(total_times) if total_times else None,
        maximum_total_time=max(total_times) if total_times else None,
        p50_total_time=_percentile(total_times, 50),
        p90_total_time=_percentile(total_times, 90),
        p95_total_time=_percentile(total_times, 95),
        p99_total_time=_percentile(total_times, 99),
        average_overhead_ratio=_average(overhead_ratios),
        p95_overhead_ratio=_percentile(overhead_ratios, 95),
        worst_passenger_id=worst_passenger.full_id if worst_passenger else None,
        worst_passenger_wait_time=worst_passenger.wait_time if worst_passenger else None,
        worst_passenger_total_time=worst_passenger.total_time if worst_passenger else None,
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


def _overhead_ratio(passenger: Passenger) -> float:
    """Return actual total time relative to the passenger's best possible total time."""
    floor_distance = abs(passenger.destination_floor - passenger.start_floor)
    ideal_total_time = floor_distance + MINIMUM_SERVICE_TICKS
    return (passenger.total_time or 0) / ideal_total_time


def _worst_passenger(completed: list[Passenger]) -> Passenger | None:
    """Return the completed passenger with the longest total time."""
    return max(completed, key=lambda passenger: passenger.total_time or 0, default=None)


def _ratio(numerator: float | None, denominator: float | None) -> float | None:
    """Return numerator over denominator when both are present and the denominator is nonzero."""
    if numerator is None or not denominator:
        return None
    return numerator / denominator


def _average(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def _percentile(sorted_values: list[float], percentile: float) -> float | None:
    """Return the given percentile from already-sorted values using the nearest-rank method."""
    if not sorted_values:
        return None
    rank = math.ceil(percentile / 100 * len(sorted_values))
    index = max(rank - 1, 0)
    return float(sorted_values[index])
