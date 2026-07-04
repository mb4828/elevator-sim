"""Discrete-time elevator simulation engine."""

from copy import deepcopy

from elevator_sim.core.metrics import SimulationResult, summarize_metrics
from elevator_sim.core.models import Elevator, Passenger, PassengerStatus, SimulationSnapshot
from elevator_sim.simulation.decisions import apply_decisions
from elevator_sim.simulation.events import drop_off_passengers, move_elevators, pick_up_passengers
from elevator_sim.simulation.snapshots import build_snapshot
from elevator_sim.strategies.base import ElevatorStrategy
from elevator_sim.workload.passenger_source import PassengerSource


class Simulation:
    """Authoritative state machine for one elevator simulation run."""

    def __init__(
        self,
        floors: int,
        elevators: list[Elevator],
        strategy: ElevatorStrategy,
        passenger_source: PassengerSource,
    ) -> None:
        self.floors = floors
        self.elevators = elevators
        self.strategy = strategy
        self.passenger_source = passenger_source
        self.time = 0
        self.passengers: dict[int, Passenger] = {}
        self.stopped = False
        self._validate_initial_state(self.floors, self.elevators)

    def step(self) -> SimulationSnapshot:
        """Advance the simulation by exactly one tick and return the new state."""
        if self.stopped:
            return self.snapshot()

        self._release_new_passengers(self.passenger_source, self.time, self.passengers, self.floors)
        decisions = self.strategy.plan(self.snapshot())
        apply_decisions(self.elevators, self.passengers, decisions, self.floors)

        # Keep these as global phases so every elevator moves before any drop-offs or pickups occur.
        move_elevators(self.elevators, self.floors)
        drop_off_passengers(self.elevators, self.time)
        pick_up_passengers(self.elevators, self.passengers, self.time)

        self.time += 1
        self.stopped = self._should_stop()
        return self.snapshot()

    def run(self, max_ticks: int = 100_000) -> SimulationResult:
        """Run until complete, guarding against defective strategies."""
        while not self.stopped:
            if self.time >= max_ticks:
                raise RuntimeError(f"Simulation exceeded {max_ticks} ticks")
            self.step()
        return self.result()

    def snapshot(self) -> SimulationSnapshot:
        """Return immutable state for strategies and clients."""
        return build_snapshot(self.time, self.floors, self.elevators, self.passengers, self.stopped)

    def result(self) -> SimulationResult:
        """Return final or current run metrics."""
        passengers = tuple(deepcopy(passenger) for passenger in self.passengers.values())
        return SimulationResult(
            ticks=self.time,
            metrics=summarize_metrics(list(passengers)),
            passengers=passengers,
        )

    def _should_stop(self) -> bool:
        """Determine if the simulation has completed all work."""
        source_done = self.passenger_source.is_exhausted(self.time)
        active_passengers = any(passenger.status != PassengerStatus.COMPLETED for passenger in self.passengers.values())
        assigned_work = any(elevator.assigned_passenger_ids or elevator.passengers for elevator in self.elevators)
        return source_done and not active_passengers and not assigned_work

    def _validate_initial_state(self, floors: int, elevators: list[Elevator]) -> None:
        """Validate static simulation configuration before the first tick."""
        if floors < 2:
            raise ValueError("floors must be at least 2")
        elevator_ids = [elevator.id for elevator in elevators]
        if len(elevator_ids) != len(set(elevator_ids)):
            raise ValueError("elevator IDs must be unique")
        for elevator in elevators:
            elevator.validate_for_building(floors)

    def _release_new_passengers(
        self,
        passenger_source: PassengerSource,
        time: int,
        passengers: dict[int, Passenger],
        floors: int,
    ) -> None:
        """Release passengers scheduled for the current tick."""
        for passenger in passenger_source.passengers_at(time):
            passenger.validate_for_building(floors, time)
            if passenger.id in passengers:
                raise ValueError(f"duplicate passenger ID: {passenger.id}")
            passenger.status = PassengerStatus.WAITING
            passengers[passenger.id] = passenger
