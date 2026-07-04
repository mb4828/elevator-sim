"""Base strategy contract for elevator scheduling algorithms."""

from abc import ABC, abstractmethod
from dataclasses import dataclass

from elevator_sim.core.models import Direction, SimulationSnapshot


@dataclass(frozen=True)
class ElevatorDecision:
    """A strategy's proposed work for one elevator during a tick."""

    elevator_id: int
    direction: Direction
    assigned_passenger_ids: tuple[int, ...] = ()


class ElevatorStrategy(ABC):
    """Interface implemented by all elevator scheduling strategies."""

    @abstractmethod
    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        """Return movement and assignment decisions for the current state."""
        raise NotImplementedError
