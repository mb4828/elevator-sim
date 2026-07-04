"""Simulation result and metrics helpers."""

from __future__ import annotations

from dataclasses import dataclass

from elevator_sim.core.models import Passenger


@dataclass(frozen=True)
class MetricsSummary:
    """Aggregate passenger timing metrics."""

    completed_passengers: int
    average_wait_time: float | None
    minimum_wait_time: int | None
    maximum_wait_time: int | None
    average_total_time: float | None
    minimum_total_time: int | None
    maximum_total_time: int | None


@dataclass(frozen=True)
class SimulationResult:
    """Final simulation output."""

    ticks: int
    metrics: MetricsSummary
    passengers: tuple[Passenger, ...]


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
        average_total_time=_average(total_times),
        minimum_total_time=min(total_times) if total_times else None,
        maximum_total_time=max(total_times) if total_times else None,
    )


def _average(values: list[int]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)
