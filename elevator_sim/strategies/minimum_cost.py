"""Minimum cost elevator assignment strategy."""

from elevator_sim.core.models import Direction, ElevatorSnapshot, PassengerSnapshot, PassengerStatus, SimulationSnapshot
from elevator_sim.strategies.base import (
    ElevatorDecision,
    ElevatorStrategy,
    RouteSimulation,
    distance,
    is_ahead,
)


class MinimumCostStrategy(ElevatorStrategy):
    """Assign passengers to the elevator with the lowest estimated service cost.

    This is a lightweight destination-dispatch strategy. For each unassigned
    waiting passenger, it simulates assigning that passenger to each elevator,
    estimates the resulting pickup/dropoff cost, and keeps the assignment with
    the lowest score.
    """

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        """Assign waiting passengers and return each elevator's next stop queue."""
        passenger_by_id = {passenger.id: passenger for passenger in state.passengers}
        assignments = self._build_plan_assignments(state.elevators)

        for passenger in self._unassigned_waiting_passengers(state):
            best_elevator = min(
                state.elevators,
                key=lambda elevator: self._assignment_cost(
                    elevator=elevator,
                    passenger=passenger,
                    passengers=state.passengers,
                    passenger_by_id=passenger_by_id,
                    assigned_passenger_ids=assignments[elevator.id],
                ),
            )
            assignments[best_elevator.id].append(passenger.id)

        return [
            ElevatorDecision(
                elevator_id=elevator.id,
                stop_floors=self._build_stop_queue(
                    elevator=elevator,
                    passengers=state.passengers,
                    passenger_by_id=passenger_by_id,
                    assigned_passenger_ids=assignments[elevator.id],
                ),
                assigned_passenger_ids=tuple(assignments[elevator.id]),
            )
            for elevator in state.elevators
        ]

    def _assignment_cost(
        self,
        elevator: ElevatorSnapshot,
        passenger: PassengerSnapshot,
        passengers: tuple[PassengerSnapshot, ...],
        passenger_by_id: dict[int, PassengerSnapshot],
        assigned_passenger_ids: list[int],
    ) -> int:
        """Return the estimated cost of assigning a passenger to an elevator."""
        current_route = self._estimated_route(
            elevator=elevator,
            passengers=passengers,
            passenger_by_id=passenger_by_id,
            assigned_passenger_ids=assigned_passenger_ids,
        )
        candidate_route = self._estimated_route(
            elevator=elevator,
            passengers=passengers,
            passenger_by_id=passenger_by_id,
            assigned_passenger_ids=[*assigned_passenger_ids, passenger.id],
        )

        pickup_time = _time_to_floor(elevator.current_floor, candidate_route, passenger.start_floor)
        dropoff_time = _time_to_floor(elevator.current_floor, candidate_route, passenger.destination_floor)
        added_route_distance = _route_distance(elevator.current_floor, candidate_route) - _route_distance(
            elevator.current_floor,
            current_route,
        )
        direction_penalty = self._direction_penalty(elevator, passenger)
        capacity_penalty = self._capacity_penalty(elevator)

        return pickup_time + dropoff_time + added_route_distance + direction_penalty + capacity_penalty

    def _estimated_route(
        self,
        elevator: ElevatorSnapshot,
        passengers: tuple[PassengerSnapshot, ...],
        passenger_by_id: dict[int, PassengerSnapshot],
        assigned_passenger_ids: list[int],
    ) -> tuple[int, ...]:
        """Return the stops the elevator would make to serve its riders and assigned pickups."""
        rider_dropoff_floors = [
            passenger.destination_floor
            for passenger in passengers
            if passenger.status == PassengerStatus.RIDING and passenger.elevator_id == elevator.id
        ]
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

    def _direction_penalty(self, elevator: ElevatorSnapshot, passenger: PassengerSnapshot) -> int:
        """Penalize assigning against the elevator's current useful sweep."""
        elevator_direction = self._effective_direction(elevator)
        passenger_direction = self._passenger_direction(passenger)
        if elevator_direction == Direction.IDLE:
            return 0
        if elevator_direction != passenger_direction:
            return 5
        if not is_ahead(passenger.start_floor, elevator.current_floor, elevator_direction):
            return 5
        return 0

    def _capacity_penalty(self, elevator: ElevatorSnapshot) -> int:
        """Softly discourage assigning to elevators that are currently full."""
        if elevator.passenger_count < elevator.capacity:
            return 0
        return 10


def _time_to_floor(current_floor: int, route: tuple[int, ...], target_floor: int) -> int:
    """Return the estimated travel time to a target floor along a route."""
    elapsed_time = 0
    previous_floor = current_floor
    for floor in route:
        elapsed_time += distance(previous_floor, floor)
        if floor == target_floor:
            return elapsed_time
        previous_floor = floor
    return elapsed_time + distance(previous_floor, target_floor)


def _route_distance(current_floor: int, route: tuple[int, ...]) -> int:
    """Return the total floor distance traveled along a route."""
    elapsed_distance = 0
    previous_floor = current_floor
    for floor in route:
        elapsed_distance += distance(previous_floor, floor)
        previous_floor = floor
    return elapsed_distance
