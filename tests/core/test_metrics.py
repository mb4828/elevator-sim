"""Tests for simulation metrics summaries."""

import pytest

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
    assert summary.p50_wait_time is None
    assert summary.p90_wait_time is None
    assert summary.p95_wait_time is None
    assert summary.p99_wait_time is None
    assert summary.wait_time_std_dev is None
    assert summary.max_average_wait_ratio is None
    assert summary.average_total_time is None
    assert summary.minimum_total_time is None
    assert summary.maximum_total_time is None
    assert summary.p50_total_time is None
    assert summary.p90_total_time is None
    assert summary.p95_total_time is None
    assert summary.p99_total_time is None
    assert summary.average_overhead_ratio is None
    assert summary.p95_overhead_ratio is None
    assert summary.worst_passenger_id is None
    assert summary.worst_passenger_wait_time is None
    assert summary.worst_passenger_total_time is None


def test_summarize_metrics_reports_wait_and_total_time_statistics() -> None:
    """Metrics report min, max, average, and nearest-rank percentiles across completed passengers."""
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
    assert summary.p50_wait_time == 5.0
    assert summary.p90_wait_time == 9.0
    assert summary.p95_wait_time == 10.0
    assert summary.p99_wait_time == 10.0
    assert summary.average_total_time == 7.5
    assert summary.p50_total_time == 7.0
    assert summary.p90_total_time == 11.0
    assert summary.p95_total_time == 12.0
    assert summary.p99_total_time == 12.0


def test_summarize_metrics_reports_wait_time_fairness_statistics() -> None:
    """Metrics report wait time spread as a standard deviation and max-to-average ratio."""
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

    assert summary.wait_time_std_dev == pytest.approx(2.8722813)
    assert summary.max_average_wait_ratio == pytest.approx(10 / 5.5)


def test_summarize_metrics_reports_overhead_versus_best_possible_time() -> None:
    """Overhead compares each trip against floor distance plus the minimum service ticks."""
    perfectly_served = Passenger(
        id=1,
        request_time=0,
        start_floor=5,
        destination_floor=1,
        pickup_time=0,
        dropoff_time=6,
    )
    delayed = Passenger(
        id=2,
        request_time=0,
        start_floor=0,
        destination_floor=4,
        pickup_time=2,
        dropoff_time=12,
    )

    summary = summarize_metrics([perfectly_served, delayed])

    assert summary.average_overhead_ratio == pytest.approx(1.5)
    assert summary.p95_overhead_ratio == pytest.approx(2.0)


def test_summarize_metrics_reports_worst_served_passenger() -> None:
    """Metrics identify the completed passenger with the longest total time."""
    quick_trip = Passenger(
        id=1,
        full_id="alice",
        request_time=0,
        start_floor=0,
        destination_floor=3,
        pickup_time=1,
        dropoff_time=7,
    )
    slow_trip = Passenger(
        id=2,
        full_id="bob",
        request_time=0,
        start_floor=0,
        destination_floor=3,
        pickup_time=4,
        dropoff_time=20,
    )

    summary = summarize_metrics([quick_trip, slow_trip])

    assert summary.worst_passenger_id == "bob"
    assert summary.worst_passenger_wait_time == 4
    assert summary.worst_passenger_total_time == 20


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
