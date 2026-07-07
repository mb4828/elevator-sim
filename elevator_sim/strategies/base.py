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
        """Return the full route the elevator would follow to serve its riders and assigned pickups."""
        rider_dropoff_floors = [
            passenger.destination_floor
            for passenger in passengers
            if passenger.status == PassengerStatus.RIDING and passenger.elevator_id == elevator.id
        ]
        waiting_pickups: list[PassengerSnapshot] = []
        if elevator.passenger_count < elevator.capacity:
            waiting_pickups = [
                passenger_by_id[passenger_id]
                for passenger_id in assigned_passenger_ids
                if passenger_by_id[passenger_id].status == PassengerStatus.WAITING
            ]

        simulation = RouteSimulation(
            current_floor=elevator.current_floor,
            direction=self._effective_direction(elevator),
            dropoff_floors=rider_dropoff_floors,
            waiting_pickups=waiting_pickups,
        )
        return simulation.route()

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


@dataclass
class RouteSimulation:
    """Simulates the full sequence of stops one elevator would make to serve its work.

    Movement follows a LOOK sweep: keep travelling in one direction while any
    stop lies ahead, then reverse. At each floor the elevator drops off arriving
    riders and boards waiting passengers travelling its way; reaching a pickup
    floor adds that passenger's destination as a new dropoff. Opposite-direction
    passengers board only once the elevator turns around, so it never stops for
    them mid-sweep. Capacity is ignored; this produces a plan, not an exact schedule.
    """

    current_floor: int
    direction: Direction
    dropoff_floors: list[int]
    waiting_pickups: list[PassengerSnapshot]

    def route(self) -> tuple[int, ...]:
        """Return every floor the elevator would stop at, in visit order."""
        stops: list[int] = []
        while True:
            if self._serve_current_floor():
                stops.append(self.current_floor)
            if not self._pending_stop_floors():
                return tuple(stops)
            self.current_floor = self._next_stop_floor()

    def _serve_current_floor(self) -> bool:
        """Drop off and board at the current floor, reporting whether the elevator stopped."""
        stopped = self.current_floor in self.dropoff_floors
        self.dropoff_floors = [floor for floor in self.dropoff_floors if floor != self.current_floor]
        stopped = self._board(self._boardable_pickups_here()) or stopped
        if not self._stops_ahead():
            # Nothing remains ahead, so the elevator turns around here: board anyone
            # still waiting rather than stranding opposite-direction passengers.
            stopped = self._board(self._pickups_here()) or stopped
        return stopped

    def _board(self, passengers: list[PassengerSnapshot]) -> bool:
        """Board the given passengers, adding each destination as a new dropoff."""
        for passenger in passengers:
            self.waiting_pickups.remove(passenger)
            self.dropoff_floors.append(passenger.destination_floor)
        return bool(passengers)

    def _pickups_here(self) -> list[PassengerSnapshot]:
        """Return every waiting pickup at the current floor."""
        return [passenger for passenger in self.waiting_pickups if passenger.start_floor == self.current_floor]

    def _boardable_pickups_here(self) -> list[PassengerSnapshot]:
        """Return current-floor pickups travelling the elevator's current direction."""
        if self.direction == Direction.IDLE:
            return self._pickups_here()
        return [passenger for passenger in self._pickups_here() if _passenger_direction(passenger) == self.direction]

    def _next_stop_floor(self) -> int:
        """Return the nearest pending stop, finishing the current sweep before reversing."""
        if self.direction == Direction.IDLE:
            nearest_stop = self._nearest_of(self._pending_stop_floors())
            self.direction = Direction.UP if nearest_stop > self.current_floor else Direction.DOWN
            return nearest_stop
        if not self._stops_ahead():
            self.direction = Direction.DOWN if self.direction == Direction.UP else Direction.UP
        return self._nearest_of(self._stops_ahead())

    def _stops_ahead(self) -> list[int]:
        """Return pending stop floors strictly ahead in the current direction."""
        return [floor for floor in self._pending_stop_floors() if is_ahead(floor, self.current_floor, self.direction)]

    def _pending_stop_floors(self) -> list[int]:
        """Return every floor that still needs a stop: dropoffs plus waiting pickups."""
        return [*self.dropoff_floors, *(passenger.start_floor for passenger in self.waiting_pickups)]

    def _nearest_of(self, floors: list[int]) -> int:
        """Return the floor closest to the elevator's current position."""
        return min(floors, key=lambda floor: distance(self.current_floor, floor))


def _passenger_direction(passenger: PassengerSnapshot) -> Direction:
    """Return a passenger's requested travel direction."""
    if passenger.destination_floor > passenger.start_floor:
        return Direction.UP
    return Direction.DOWN


def is_ahead(floor: int, current_floor: int, direction: Direction) -> bool:
    """Return whether a floor is strictly ahead in a direction."""
    if direction == Direction.UP:
        return floor > current_floor
    return floor < current_floor


def distance(first_floor: int, second_floor: int) -> int:
    """Return absolute floor distance."""
    return abs(first_floor - second_floor)
