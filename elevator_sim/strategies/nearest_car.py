"""Nearest-car elevator scheduling strategy.

Rules:
- Assign every unassigned waiting passenger during each planning pass.
- Prefer the nearest elevator already moving toward the pickup floor in the passenger's requested direction.
- Leave a passenger waiting (retry next tick) when every car would need to reverse first.
- Keep current rider destinations and assigned pickup floors on the next directional sweep, then append newly assigned
  passenger destinations after their pickup floors.
"""

from elevator_sim.core.models import Direction, ElevatorSnapshot, PassengerSnapshot, PassengerStatus, SimulationSnapshot
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy


class NearestCarStrategy(ElevatorStrategy):
    """Assign waiting passengers to the nearest elevator."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        """Return assignment and stop decisions for every elevator."""
        passenger_by_id = {passenger.id: passenger for passenger in state.passengers}
        plan_assignments = self._build_plan_assignments(state.elevators)
        already_assigned_passenger_ids = {
            passenger_id for elevator in state.elevators for passenger_id in elevator.assigned_passenger_ids
        }

        waiting_passengers = sorted(
            (
                passenger
                for passenger in state.passengers
                if passenger.status == PassengerStatus.WAITING and passenger.id not in already_assigned_passenger_ids
            ),
            key=lambda passenger: (passenger.request_time, passenger.id),
        )
        for passenger in waiting_passengers:
            elevator = self._nearest_elevator(state.elevators, passenger)
            if elevator is not None:
                plan_assignments[elevator.id].append(passenger.id)

        return [
            ElevatorDecision(
                elevator_id=elevator.id,
                stop_floors=self._build_stop_queue(
                    elevator,
                    state.passengers,
                    passenger_by_id,
                    plan_assignments[elevator.id],
                ),
                assigned_passenger_ids=tuple(plan_assignments[elevator.id]),
            )
            for elevator in state.elevators
        ]

    def _build_plan_assignments(self, elevators: tuple[ElevatorSnapshot, ...]) -> dict[int, list[int]]:
        """Return mutable assignment lists keyed by elevator ID."""
        return {elevator.id: list(elevator.assigned_passenger_ids) for elevator in elevators}

    def _nearest_elevator(
        self,
        elevators: tuple[ElevatorSnapshot, ...],
        passenger: PassengerSnapshot,
    ) -> ElevatorSnapshot | None:
        """Return the nearest elevator moving toward the passenger, or None if all cars must reverse first."""
        eligible_elevators = [
            elevator for elevator in elevators if self._is_moving_toward_passenger(elevator, passenger)
        ]
        if not eligible_elevators:
            return None
        return min(
            eligible_elevators,
            key=lambda elevator: (abs(elevator.current_floor - passenger.start_floor), elevator.id),
        )

    def _is_moving_toward_passenger(self, elevator: ElevatorSnapshot, passenger: PassengerSnapshot) -> bool:
        """Return whether an elevator can serve a passenger without reversing first."""
        direction = self._effective_direction(elevator)
        if direction == Direction.IDLE:
            return True
        if self._passenger_direction(passenger) != direction:
            return False
        if direction == Direction.UP:
            return passenger.start_floor >= elevator.current_floor
        return passenger.start_floor <= elevator.current_floor

    def _effective_direction(self, elevator: ElevatorSnapshot) -> Direction:
        """Return the elevator's active travel direction, including queued post-stop work."""
        if elevator.direction != Direction.IDLE or not elevator.target_floors:
            return elevator.direction

        future_stops = [floor for floor in elevator.target_floors if floor != elevator.current_floor]
        if not future_stops:
            return Direction.IDLE
        if future_stops[0] > elevator.current_floor:
            return Direction.UP
        return Direction.DOWN

    def _build_stop_queue(
        self,
        elevator: ElevatorSnapshot,
        passengers: tuple[PassengerSnapshot, ...],
        passenger_by_id: dict[int, PassengerSnapshot],
        assigned_passenger_ids: list[int],
    ) -> tuple[int, ...]:
        """Build an ordered stop queue for rider destinations and assigned pickups."""
        rider_destination_stops = [
            passenger.destination_floor
            for passenger in passengers
            if passenger.status == PassengerStatus.RIDING and passenger.elevator_id == elevator.id
        ]
        sweep_direction = self._route_direction(elevator, rider_destination_stops)
        if sweep_direction != Direction.IDLE:
            return self._build_moving_stop_queue(
                elevator, passenger_by_id, assigned_passenger_ids, rider_destination_stops, sweep_direction
            )

        current_sweep_pickup_stops: list[int] = []
        reverse_sweep_pickup_stops: list[int] = []
        following_sweep_pickup_stops: list[int] = []
        newly_assigned_passengers: list[PassengerSnapshot] = []
        direction = sweep_direction
        for passenger_id in assigned_passenger_ids:
            passenger = passenger_by_id[passenger_id]
            newly_assigned_passengers.append(passenger)
            if self._is_current_sweep_pickup(elevator, passenger, direction):
                current_sweep_pickup_stops.append(passenger.start_floor)
            elif self._passenger_direction(passenger) == self._reverse_direction(direction):
                reverse_sweep_pickup_stops.append(passenger.start_floor)
            else:
                following_sweep_pickup_stops.append(passenger.start_floor)

        first_leg_stops = [*rider_destination_stops, *current_sweep_pickup_stops]
        direction = self._route_direction(elevator, first_leg_stops)
        ordered_first_leg_stops = self._order_stops(elevator.current_floor, direction, first_leg_stops)
        ordered_pickup_floors = self._order_stops(elevator.current_floor, direction, current_sweep_pickup_stops)
        reverse_direction = self._reverse_direction(direction)
        ordered_reverse_pickup_floors = self._order_future_sweep_pickups(reverse_direction, reverse_sweep_pickup_stops)
        ordered_following_pickup_floors = self._order_future_sweep_pickups(direction, following_sweep_pickup_stops)
        pickup_floors = (*ordered_pickup_floors, *ordered_reverse_pickup_floors, *ordered_following_pickup_floors)

        destination_stops = [
            passenger.destination_floor
            for pickup_floor in pickup_floors
            for passenger in newly_assigned_passengers
            if passenger.start_floor == pickup_floor
        ]
        return self._dedupe_stops(
            (
                *ordered_first_leg_stops,
                *ordered_reverse_pickup_floors,
                *ordered_following_pickup_floors,
                *destination_stops,
            )
        )

    def _build_moving_stop_queue(
        self,
        elevator: ElevatorSnapshot,
        passenger_by_id: dict[int, PassengerSnapshot],
        assigned_passenger_ids: list[int],
        rider_destination_stops: list[int],
        direction: Direction,
    ) -> tuple[int, ...]:
        """Build a stop queue for a travelling elevator, keeping each passenger's pickup and
        destination in the same directional sweep so the car finishes its current direction first.
        """
        reverse_direction = self._reverse_direction(direction)
        current_sweep_stops: list[int] = list(rider_destination_stops)
        reverse_sweep_stops: list[int] = []
        following_sweep_stops: list[int] = []
        for passenger_id in assigned_passenger_ids:
            passenger = passenger_by_id[passenger_id]
            trip_stops = (passenger.start_floor, passenger.destination_floor)
            if self._is_current_sweep_pickup(elevator, passenger, direction):
                current_sweep_stops.extend(trip_stops)
            elif self._passenger_direction(passenger) == reverse_direction:
                reverse_sweep_stops.extend(trip_stops)
            else:
                following_sweep_stops.extend(trip_stops)

        ordered_current_sweep = self._order_stops(elevator.current_floor, direction, current_sweep_stops)
        ordered_reverse_sweep = self._order_future_sweep_pickups(reverse_direction, reverse_sweep_stops)
        ordered_following_sweep = self._order_future_sweep_pickups(direction, following_sweep_stops)
        return self._dedupe_stops((*ordered_current_sweep, *ordered_reverse_sweep, *ordered_following_sweep))

    def _is_current_sweep_pickup(
        self,
        elevator: ElevatorSnapshot,
        passenger: PassengerSnapshot,
        direction: Direction,
    ) -> bool:
        """Return whether a passenger can board on the elevator's current sweep."""
        if direction == Direction.IDLE:
            return True
        if self._passenger_direction(passenger) != direction:
            return False
        if direction == Direction.UP:
            return passenger.start_floor >= elevator.current_floor
        return passenger.start_floor <= elevator.current_floor

    def _reverse_direction(self, direction: Direction) -> Direction:
        """Return the opposite movement direction, preserving idle."""
        if direction == Direction.UP:
            return Direction.DOWN
        if direction == Direction.DOWN:
            return Direction.UP
        return Direction.IDLE

    def _order_future_sweep_pickups(self, direction: Direction, pickup_stops: list[int]) -> tuple[int, ...]:
        """Order future pickups after the elevator has already reached its turn point."""
        unique_stops = set(pickup_stops)
        if direction == Direction.UP:
            return tuple(sorted(unique_stops))
        if direction == Direction.DOWN:
            return tuple(sorted(unique_stops, reverse=True))
        return tuple(sorted(unique_stops))

    def _passenger_direction(self, passenger: PassengerSnapshot) -> Direction:
        """Return the passenger's requested travel direction."""
        if passenger.destination_floor > passenger.start_floor:
            return Direction.UP
        return Direction.DOWN

    def _route_direction(self, elevator: ElevatorSnapshot, stops: list[int]) -> Direction:
        """Choose the direction used to order an elevator's next stop queue."""
        effective_direction = self._effective_direction(elevator)
        if effective_direction != Direction.IDLE or not stops:
            return effective_direction

        nearest_stop = min(stops, key=lambda floor: (abs(floor - elevator.current_floor), floor))
        if nearest_stop > elevator.current_floor:
            return Direction.UP
        if nearest_stop < elevator.current_floor:
            return Direction.DOWN
        return Direction.IDLE

    def _order_stops(self, current_floor: int, direction: Direction, stops: list[int]) -> tuple[int, ...]:
        """Order stops by current travel sweep, preserving one visit per floor."""
        unique_stops = set(stops)
        if direction == Direction.UP:
            ordered_stops = sorted(floor for floor in unique_stops if floor >= current_floor)
            ordered_stops.extend(sorted((floor for floor in unique_stops if floor < current_floor), reverse=True))
            return tuple(ordered_stops)
        if direction == Direction.DOWN:
            ordered_stops = sorted((floor for floor in unique_stops if floor <= current_floor), reverse=True)
            ordered_stops.extend(sorted(floor for floor in unique_stops if floor > current_floor))
            return tuple(ordered_stops)
        return tuple(sorted(unique_stops, key=lambda floor: (abs(floor - current_floor), floor)))

    def _dedupe_stops(self, stops: tuple[int, ...]) -> tuple[int, ...]:
        """Remove duplicate stops from a route while preserving route order."""
        ordered_stops: list[int] = []
        seen_stops: set[int] = set()
        for stop in stops:
            if stop in seen_stops:
                continue
            ordered_stops.append(stop)
            seen_stops.add(stop)
        return tuple(ordered_stops)
