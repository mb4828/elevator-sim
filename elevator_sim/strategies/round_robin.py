"""Round-robin elevator assignment strategy."""

from elevator_sim.core.models import SimulationSnapshot
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy


class RoundRobinStrategy(ElevatorStrategy):
    """Assign waiting passengers to elevators in rotating elevator order."""

    def __init__(self) -> None:
        self._next_elevator_index = 0

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        """Return round-robin passenger assignments and basic stop queues."""
        passenger_by_id = {passenger.id: passenger for passenger in state.passengers}
        plan_assignments = self._build_plan_assignments(state.elevators)
        unassigned_waiting_passengers = self._unassigned_waiting_passengers(state)

        for passenger in unassigned_waiting_passengers:
            elevator = state.elevators[self._next_elevator_index % len(state.elevators)]
            plan_assignments[elevator.id].append(passenger.id)
            self._next_elevator_index += 1

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
