"""Seeded passenger workload generation."""

from __future__ import annotations

from collections import defaultdict
import random

from elevator_sim.core.models import Passenger


class PassengerSource:
    """Generate and replay reproducible Bernoulli passenger arrivals."""

    def __init__(self, floors: int, arrival_probability: float, duration: int, seed: int | None = None) -> None:
        if floors < 2:
            raise ValueError("floors must be at least 2")
        if not 0.0 <= arrival_probability <= 1.0:
            raise ValueError("arrival_probability must be between 0.0 and 1.0")
        if duration < 0:
            raise ValueError("duration must be non-negative")

        self.floors = floors
        self.arrival_probability = arrival_probability
        self.duration = duration
        self._random = random.Random(seed)
        self._passengers = self._generate_passengers()
        self._by_time = self._group_passengers_by_time()

    @property
    def passengers(self) -> tuple[Passenger, ...]:
        """Return the generated passenger workload."""
        return self._passengers

    def passengers_at(self, time: int) -> list[Passenger]:
        """Return passengers scheduled for a specific tick."""
        return list(self._by_time.get(time, []))

    def is_exhausted(self, time: int) -> bool:
        """Return whether passenger generation has passed its configured duration."""
        return time >= self.duration

    def _generate_passengers(self) -> tuple[Passenger, ...]:
        """Generate the full passenger workload up front."""
        passengers: list[Passenger] = []
        next_passenger_id = 1
        for time in range(self.duration):
            if self._random.random() >= self.arrival_probability:
                continue
            passengers.append(self._create_passenger(next_passenger_id, time))
            next_passenger_id += 1
        return tuple(passengers)

    def _create_passenger(self, passenger_id: int, request_time: int) -> Passenger:
        """Create one passenger with distinct random origin and destination floors."""
        start_floor = self._random.randint(1, self.floors)
        destination_floor = self._random.randint(1, self.floors)
        while destination_floor == start_floor:
            destination_floor = self._random.randint(1, self.floors)

        return Passenger(
            id=passenger_id,
            request_time=request_time,
            start_floor=start_floor,
            destination_floor=destination_floor,
        )

    def _group_passengers_by_time(self) -> dict[int, list[Passenger]]:
        """Index generated passengers by request time."""
        by_time: dict[int, list[Passenger]] = defaultdict(list)
        for passenger in self._passengers:
            by_time[passenger.request_time].append(passenger)
        return by_time
