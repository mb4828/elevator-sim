"""Shared workload source behavior."""

from collections import defaultdict

from elevator_sim.core.models import Passenger


class PassengerSource:
    """Base workload source for scheduled passenger requests."""

    def __init__(self, passengers: tuple[Passenger, ...], duration: int) -> None:
        if duration < 0:
            raise ValueError("duration must be non-negative")
        self.duration = duration
        self._passengers = passengers
        self._by_time = self._group_passengers_by_time(passengers)

    @property
    def passengers(self) -> tuple[Passenger, ...]:
        """Return the configured passenger workload."""
        return self._passengers

    def passengers_at(self, time: int) -> list[Passenger]:
        """Return passengers scheduled for a specific tick."""
        return list(self._by_time.get(time, []))

    def is_exhausted(self, time: int) -> bool:
        """Return whether passenger generation has passed its configured duration."""
        return time >= self.duration

    def _group_passengers_by_time(self, passengers: tuple[Passenger, ...]) -> dict[int, list[Passenger]]:
        """Index passengers by request time."""
        by_time: dict[int, list[Passenger]] = defaultdict(list)
        for passenger in passengers:
            by_time[passenger.request_time].append(passenger)
        return by_time
