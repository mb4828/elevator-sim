"""Seeded passenger workload generation."""

from collections import defaultdict
import random

from elevator_sim.core.models import Passenger


class PassengerSource:
    """Generate and replay reproducible random passenger workloads."""

    def __init__(self, floors: int, passengers: int, duration: int, seed: int | None = None) -> None:
        if floors < 2:
            raise ValueError("floors must be at least 2")
        if passengers < 0:
            raise ValueError("passengers must be non-negative")
        if duration < 0:
            raise ValueError("duration must be non-negative")
        if passengers > 0 and duration == 0:
            raise ValueError("duration must be positive when passengers are requested")

        self.floors = floors
        self.passenger_count = passengers
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
        request_times = sorted(self._random.randrange(self.duration) for _ in range(self.passenger_count))
        return tuple(
            self._create_passenger(passenger_id, request_time)
            for passenger_id, request_time in enumerate(request_times, start=1)
        )

    def _create_passenger(self, passenger_id: int, request_time: int) -> Passenger:
        """Create one passenger with distinct random origin and destination floors."""
        start_floor = self._random.randint(0, self.floors - 1)
        destination_floor = self._random.randint(0, self.floors - 1)
        while destination_floor == start_floor:
            destination_floor = self._random.randint(0, self.floors - 1)

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
