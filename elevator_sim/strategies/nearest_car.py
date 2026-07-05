"""Nearest-car elevator assignment strategy."""

from elevator_sim.core.models import ElevatorSnapshot, PassengerSnapshot, SimulationSnapshot
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy


class NearestCarStrategy(ElevatorStrategy):
    """Assign waiting passengers to the nearest elevator, regardless of direction."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        """Return nearest-car passenger assignments and basic stop queues."""
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
        """Return the nearest elevator by current floor, ignoring travel direction."""
        return min(elevators, key=lambda elevator: (abs(elevator.current_floor - passenger.start_floor), elevator.id))
