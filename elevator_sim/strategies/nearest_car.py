"""Nearest-car elevator scheduling strategy.

Rules:
- Assign every unassigned waiting passenger during each planning pass.
- Prefer the nearest elevator already moving toward the pickup floor.
- Fall back to the nearest elevator when all cars would need to reverse first.
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
    ) -> ElevatorSnapshot:
        """Return the nearest elevator, preferring cars already moving toward the passenger."""
        eligible_elevators = [
            elevator for elevator in elevators if self._is_moving_toward_passenger(elevator, passenger)
        ]
        if not eligible_elevators:
            eligible_elevators = list(elevators)
        return min(
            eligible_elevators,
            key=lambda elevator: (abs(elevator.current_floor - passenger.start_floor), elevator.id),
        )

    def _is_moving_toward_passenger(self, elevator: ElevatorSnapshot, passenger: PassengerSnapshot) -> bool:
        """Return whether an elevator can serve a passenger without reversing first."""
        direction = self._effective_direction(elevator)
        if direction == Direction.IDLE:
            return True
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
        pickup_stops: list[int] = []
        newly_assigned_passengers: list[PassengerSnapshot] = []
        for passenger_id in assigned_passenger_ids:
            passenger = passenger_by_id[passenger_id]
            newly_assigned_passengers.append(passenger)
            pickup_stops.append(passenger.start_floor)

        first_leg_stops = [*rider_destination_stops, *pickup_stops]
        direction = self._route_direction(elevator, first_leg_stops)
        ordered_first_leg_stops = self._order_stops(elevator.current_floor, direction, first_leg_stops)
        ordered_pickup_floors = self._order_stops(elevator.current_floor, direction, pickup_stops)

        destination_stops = [
            passenger.destination_floor
            for pickup_floor in ordered_pickup_floors
            for passenger in newly_assigned_passengers
            if passenger.start_floor == pickup_floor
        ]
        return self._dedupe_stops((*ordered_first_leg_stops, *destination_stops))

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
