"""Base strategy contract for elevator scheduling algorithms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from elevator_sim.core.models import (
    Direction,
    ElevatorSnapshot,
    PassengerSnapshot,
    PassengerStatus,
    SimulationSnapshot,
)


@dataclass(frozen=True)
class ElevatorDecision:
    """A strategy's proposed work for one elevator during a tick."""

    # The ID of the elevator for which this decision applies.
    elevator_id: int

    # List of floors the elevator should stop at, in order.
    stop_floors: tuple[int, ...] = ()

    # List of passenger IDs that should be assigned to this elevator.
    assigned_passenger_ids: tuple[int, ...] = ()


class ElevatorStrategy(ABC):
    """Interface implemented by all elevator scheduling strategies."""

    @abstractmethod
    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        """Return stop queue and assignment decisions for the current state."""
        raise NotImplementedError

    def _build_plan_assignments(self, elevators: tuple[ElevatorSnapshot, ...]) -> dict[int, list[int]]:
        """Return mutable assignment lists keyed by elevator ID."""
        return {elevator.id: list(elevator.assigned_passenger_ids) for elevator in elevators}

    def _unassigned_waiting_passengers(self, state: SimulationSnapshot) -> list[PassengerSnapshot]:
        """Return waiting passengers that do not already belong to an elevator."""
        already_assigned_passenger_ids = {
            passenger_id for elevator in state.elevators for passenger_id in elevator.assigned_passenger_ids
        }
        return sorted(
            (
                passenger
                for passenger in state.passengers
                if passenger.status == PassengerStatus.WAITING and passenger.id not in already_assigned_passenger_ids
            ),
            key=lambda passenger: (passenger.request_time, passenger.id),
        )

    def _build_stop_queue(
        self,
        elevator: ElevatorSnapshot,
        passengers: tuple[PassengerSnapshot, ...],
        passenger_by_id: dict[int, PassengerSnapshot],
        assigned_passenger_ids: list[int],
    ) -> tuple[int, ...]:
        """Build the next actionable stop for current riders and assigned waiting passengers."""
        rider_stops = tuple(
            passenger.destination_floor
            for passenger in passengers
            if passenger.status == PassengerStatus.RIDING and passenger.elevator_id == elevator.id
        )
        pickups: tuple[PassengerSnapshot, ...] = ()
        if elevator.passenger_count < elevator.capacity:
            pickups = tuple(
                passenger_by_id[passenger_id]
                for passenger_id in assigned_passenger_ids
                if passenger_by_id[passenger_id].status == PassengerStatus.WAITING
            )

        planner = _StopPlanner(current_floor=elevator.current_floor, rider_stops=rider_stops, pickups=pickups)
        direction = self._effective_direction(elevator)
        if direction == Direction.IDLE:
            return planner.idle_queue()
        return planner.directional_queue(direction)

    def _effective_direction(self, elevator: ElevatorSnapshot) -> Direction:
        """Return current direction, falling back to the direction of the next queued stop."""
        if elevator.direction != Direction.IDLE:
            return elevator.direction
        future_stops = [floor for floor in elevator.target_floors if floor != elevator.current_floor]
        if not future_stops:
            return Direction.IDLE
        if future_stops[0] > elevator.current_floor:
            return Direction.UP
        return Direction.DOWN

    def _passenger_direction(self, passenger: PassengerSnapshot) -> Direction:
        """Return a passenger's requested travel direction."""
        return _passenger_direction(passenger)


@dataclass(frozen=True)
class _StopPlanner:
    """Chooses the next actionable stops for one elevator.

    Works from the elevator's current floor, the destination floors of its
    current riders, and the assigned waiting passengers it still has room for.
    """

    current_floor: int
    rider_stops: tuple[int, ...]
    pickups: tuple[PassengerSnapshot, ...]

    def directional_queue(self, direction: Direction) -> tuple[int, ...]:
        """Return the next stop while preserving the current sweep direction."""
        pickups_here = self._pickups_at_current_floor(direction)
        if pickups_here:
            return _pickup_stops(self.current_floor, pickups_here, direction, self.rider_stops)
        if self.current_floor in self.rider_stops:
            return (self.current_floor,)
        return self._sweep_queue(direction) or self._reverse_queue(_opposite_direction(direction))

    def idle_queue(self) -> tuple[int, ...]:
        """Return the next stop when the elevator has no current sweep direction."""
        if self.current_floor in self.rider_stops:
            return (self.current_floor,)
        nearest_rider_stop = _nearest_floor(self.current_floor, self.rider_stops)
        if nearest_rider_stop is not None:
            return (nearest_rider_stop,)
        pickups_here = self._pickups_at_current_floor()
        if pickups_here:
            return _pickup_stops(self.current_floor, pickups_here, _passenger_direction(pickups_here[0]))
        return _stops_for_pickup(self._nearest_pickup())

    def _sweep_queue(self, direction: Direction) -> tuple[int, ...]:
        """Return the next actionable stop ahead in a direction, or () when nothing is ahead."""
        next_rider_stop = _next_floor_in_direction(self.current_floor, self.rider_stops, direction)
        next_pickup = self._next_pickup_ahead(direction)
        if next_rider_stop is None:
            return _stops_for_pickup(next_pickup)
        if next_pickup is None:
            return (next_rider_stop,)
        if _is_before_or_same(next_rider_stop, next_pickup.start_floor, direction):
            return (next_rider_stop,)
        return _stops_for_pickup(next_pickup, self.rider_stops)

    def _reverse_queue(self, direction: Direction) -> tuple[int, ...]:
        """Return the next stop after the original sweep direction is exhausted."""
        next_rider_stop = _next_floor_in_direction(self.current_floor, self.rider_stops, direction)
        next_pickup = self._nearest_pickup_traveling(direction)
        if next_rider_stop is None:
            return _stops_for_pickup(next_pickup)
        if next_pickup is None:
            return (next_rider_stop,)
        if distance(self.current_floor, next_rider_stop) <= distance(self.current_floor, next_pickup.start_floor):
            return (next_rider_stop,)
        return _stops_for_pickup(next_pickup, self.rider_stops)

    def _pickups_at_current_floor(self, direction: Direction | None = None) -> tuple[PassengerSnapshot, ...]:
        """Return pickups waiting at the current floor, optionally filtered by travel direction."""
        return tuple(
            passenger
            for passenger in self.pickups
            if passenger.start_floor == self.current_floor
            and (direction is None or _passenger_direction(passenger) == direction)
        )

    def _next_pickup_ahead(self, direction: Direction) -> PassengerSnapshot | None:
        """Return the closest pickup ahead of the elevator and traveling in a direction."""
        candidates = [
            passenger
            for passenger in self.pickups
            if _passenger_direction(passenger) == direction
            and is_ahead(passenger.start_floor, self.current_floor, direction)
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda passenger: distance(self.current_floor, passenger.start_floor))

    def _nearest_pickup_traveling(self, direction: Direction) -> PassengerSnapshot | None:
        """Return the closest pickup traveling in a direction, anywhere in the building."""
        candidates = [passenger for passenger in self.pickups if _passenger_direction(passenger) == direction]
        return _nearest_passenger(self.current_floor, candidates)

    def _nearest_pickup(self) -> PassengerSnapshot | None:
        """Return the closest pickup in any travel direction."""
        return _nearest_passenger(self.current_floor, list(self.pickups))


def _pickup_stops(
    pickup_floor: int,
    passengers: tuple[PassengerSnapshot, ...],
    direction: Direction,
    rider_stops: tuple[int, ...] = (),
) -> tuple[int, ...]:
    """Return a pickup stop plus one onward stop to preserve the boarding direction."""
    onward_floors = (*rider_stops, *(passenger.destination_floor for passenger in passengers))
    onward_stop = _next_floor_in_direction(pickup_floor, onward_floors, direction)
    if onward_stop is None:
        return (pickup_floor,)
    return (pickup_floor, onward_stop)


def _stops_for_pickup(passenger: PassengerSnapshot | None, rider_stops: tuple[int, ...] = ()) -> tuple[int, ...]:
    """Return pickup stops for a single passenger, or () when there is no passenger."""
    if passenger is None:
        return ()
    return _pickup_stops(passenger.start_floor, (passenger,), _passenger_direction(passenger), rider_stops)


def _nearest_passenger(current_floor: int, passengers: list[PassengerSnapshot]) -> PassengerSnapshot | None:
    """Return the passenger closest to a floor, breaking ties by passenger ID."""
    if not passengers:
        return None
    return min(passengers, key=lambda passenger: (distance(current_floor, passenger.start_floor), passenger.id))


def _next_floor_in_direction(current_floor: int, floors: tuple[int, ...], direction: Direction) -> int | None:
    """Return the closest floor strictly ahead in a direction."""
    candidates = [floor for floor in floors if is_ahead(floor, current_floor, direction)]
    if not candidates:
        return None
    return min(candidates, key=lambda floor: distance(current_floor, floor))


def _nearest_floor(current_floor: int, floors: tuple[int, ...]) -> int | None:
    """Return the nearest floor from a list of floors."""
    if not floors:
        return None
    return min(floors, key=lambda floor: distance(current_floor, floor))


def _passenger_direction(passenger: PassengerSnapshot) -> Direction:
    """Return a passenger's requested travel direction."""
    if passenger.destination_floor > passenger.start_floor:
        return Direction.UP
    return Direction.DOWN


def _opposite_direction(direction: Direction) -> Direction:
    """Return the opposite travel direction."""
    if direction == Direction.UP:
        return Direction.DOWN
    return Direction.UP


def is_ahead(floor: int, current_floor: int, direction: Direction) -> bool:
    """Return whether a floor is strictly ahead in a direction."""
    if direction == Direction.UP:
        return floor > current_floor
    return floor < current_floor


def _is_before_or_same(first_floor: int, second_floor: int, direction: Direction) -> bool:
    """Return whether the first floor comes before the second in a sweep direction."""
    if direction == Direction.UP:
        return first_floor <= second_floor
    return first_floor >= second_floor


def distance(first_floor: int, second_floor: int) -> int:
    """Return absolute floor distance."""
    return abs(first_floor - second_floor)
