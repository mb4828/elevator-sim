"""Nearest-car same-direction elevator assignment strategy."""

from elevator_sim.core.models import Direction, ElevatorSnapshot, PassengerSnapshot, SimulationSnapshot
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy


class NearestCarSameDirectionStrategy(ElevatorStrategy):
    """Assign waiting passengers to the nearest elevator already serving their direction."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        """Return assignment and stop decisions for every elevator."""
        passenger_by_id = {passenger.id: passenger for passenger in state.passengers}
        plan_assignments = self._build_plan_assignments(state.elevators)

        for passenger in self._unassigned_waiting_passengers(state):
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

    def _nearest_elevator(
        self,
        elevators: tuple[ElevatorSnapshot, ...],
        passenger: PassengerSnapshot,
    ) -> ElevatorSnapshot:
        """Return the nearest eligible elevator, falling back to nearest overall."""
        eligible_elevators = [
            elevator for elevator in elevators if self._is_moving_toward_passenger(elevator, passenger)
        ]
        return min(
            eligible_elevators or list(elevators),
            key=lambda elevator: (abs(elevator.current_floor - passenger.start_floor), elevator.id),
        )

    def _is_moving_toward_passenger(self, elevator: ElevatorSnapshot, passenger: PassengerSnapshot) -> bool:
        """Return whether an elevator can serve a passenger before reversing."""
        direction = self._effective_direction(elevator)
        if direction == Direction.IDLE:
            return True
        if self._passenger_direction(passenger) != direction:
            return False
        if direction == Direction.UP:
            return passenger.start_floor >= elevator.current_floor
        return passenger.start_floor <= elevator.current_floor
