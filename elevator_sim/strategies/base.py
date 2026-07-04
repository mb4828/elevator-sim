"""Base strategy contract for elevator scheduling algorithms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from elevator_sim.core.models import SimulationSnapshot


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
