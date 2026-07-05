"""Tests for simulation metrics summaries."""

from elevator_sim.core.metrics import summarize_metrics, summarize_performance
from elevator_sim.core.models import Passenger


def test_summarize_metrics_returns_none_values_when_no_passenger_completed() -> None:
    """Metrics stay unset instead of failing when no passenger finished a trip."""
    incomplete_passenger = Passenger(id=1, request_time=0, start_floor=0, destination_floor=1)

    summary = summarize_metrics([incomplete_passenger])

    assert summary.completed_passengers == 0
    assert summary.average_wait_time is None
    assert summary.minimum_wait_time is None
    assert summary.maximum_wait_time is None
    assert summary.p90_wait_time is None
    assert summary.average_total_time is None
    assert summary.minimum_total_time is None
    assert summary.maximum_total_time is None


def test_summarize_metrics_reports_wait_and_total_time_statistics() -> None:
    """Metrics report min, max, average, and nearest-rank p90 across completed passengers."""
    passengers = [
        Passenger(
            id=passenger_id,
            request_time=0,
            start_floor=0,
            destination_floor=1,
            pickup_time=wait_time,
            dropoff_time=wait_time + 2,
        )
        for passenger_id, wait_time in enumerate(range(1, 11), start=1)
    ]

    summary = summarize_metrics(passengers)

    assert summary.completed_passengers == 10
    assert summary.minimum_wait_time == 1
    assert summary.maximum_wait_time == 10
    assert summary.average_wait_time == 5.5
    assert summary.p90_wait_time == 9.0
    assert summary.average_total_time == 7.5


def test_summarize_performance_handles_zero_tick_runs() -> None:
    """Performance ratios fall back to zero instead of dividing by zero."""
    summary = summarize_performance(
        total_ticks=0,
        total_riding_ticks=0,
        total_capacity_ticks=0,
        peak_queue=0,
        total_active_elevator_ticks=0,
        total_elevator_ticks=0,
    )

    assert summary.average_passengers_per_tick == 0.0
    assert summary.efficiency_score == 0.0
    assert summary.utilization == 0.0
