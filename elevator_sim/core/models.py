"""Core domain models for the elevator simulation."""

from dataclasses import dataclass, field
from enum import Enum


class Direction(str, Enum):
    """Possible elevator and passenger travel directions."""

    UP = "up"
    DOWN = "down"
    IDLE = "idle"


class PassengerStatus(str, Enum):
    """Lifecycle states for a passenger request."""

    SCHEDULED = "scheduled"
    WAITING = "waiting"
    RIDING = "riding"
    COMPLETED = "completed"


class ElevatorServicePhase(str, Enum):
    """Per-tick service state for an elevator at a stop floor."""

    MOVING = "moving"
    STOPPING = "stopping"
    DROPPING_OFF = "dropping_off"
    PICKING_UP = "picking_up"


@dataclass
class Passenger:
    """A passenger request tracked through the simulation."""

    id: int
    request_time: int
    start_floor: int
    destination_floor: int
    status: PassengerStatus = PassengerStatus.SCHEDULED
    pickup_time: int | None = None
    dropoff_time: int | None = None
    elevator_id: int | None = None

    def __post_init__(self) -> None:
        """Validate static passenger invariants."""
        if self.id <= 0:
            raise ValueError("passenger id must be greater than 0")
        if self.request_time < 0:
            raise ValueError("request_time must be greater than or equal to 0")
        if self.start_floor < 0:
            raise ValueError("start_floor must be greater than or equal to 0")
        if self.destination_floor < 0:
            raise ValueError("destination_floor must be greater than or equal to 0")
        if self.start_floor == self.destination_floor:
            raise ValueError("start and destination floors must differ")

    @property
    def direction(self) -> Direction:
        """Return the passenger's requested travel direction."""
        if self.destination_floor > self.start_floor:
            return Direction.UP
        return Direction.DOWN

    @property
    def wait_time(self) -> int | None:
        """Return ticks between request and pickup, if picked up."""
        if self.pickup_time is None:
            return None
        return self.pickup_time - self.request_time

    @property
    def total_time(self) -> int | None:
        """Return ticks between request and drop-off, if completed."""
        if self.dropoff_time is None:
            return None
        return self.dropoff_time - self.request_time

    def validate_for_building(self, floors: int, current_time: int) -> None:
        """Validate this passenger against simulation-specific runtime constraints."""
        if self.start_floor >= floors:
            raise ValueError(f"passenger {self.id} start_floor is outside building bounds")
        if self.destination_floor >= floors:
            raise ValueError(f"passenger {self.id} destination_floor is outside building bounds")
        if self.request_time != current_time:
            raise ValueError(f"passenger {self.id} was released at the wrong time")


@dataclass
class Elevator:
    """Mutable elevator state owned by the simulation engine."""

    id: int
    current_floor: int
    capacity: int
    direction: Direction = Direction.IDLE
    service_phase: ElevatorServicePhase = ElevatorServicePhase.MOVING
    passengers: list[Passenger] = field(default_factory=list)
    assigned_passenger_ids: set[int] = field(default_factory=set)
    target_floors: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate static elevator invariants."""
        if self.id <= 0:
            raise ValueError("elevator id must be greater than 0")
        if self.current_floor < 0:
            raise ValueError("current_floor must be greater than or equal to 0")
        if self.capacity <= 0:
            raise ValueError("capacity must be greater than 0")

    @property
    def available_capacity(self) -> int:
        """Return the number of passengers that can still board."""
        return self.capacity - len(self.passengers)

    def validate_for_building(self, floors: int) -> None:
        """Validate this elevator against simulation-specific building constraints."""
        if self.current_floor >= floors:
            raise ValueError(f"elevator {self.id} current_floor is outside building bounds")
        for target_floor in self.target_floors:
            if target_floor < 0 or target_floor >= floors:
                raise ValueError(f"elevator {self.id} target_floor is outside building bounds")


@dataclass(frozen=True)
class ElevatorSnapshot:
    """Immutable elevator state for strategies and presentation adapters."""

    id: int
    current_floor: int
    direction: Direction
    service_phase: ElevatorServicePhase
    passenger_count: int
    capacity: int
    target_floors: tuple[int, ...]
    assigned_passenger_ids: tuple[int, ...]


@dataclass(frozen=True)
class PassengerSnapshot:
    """Immutable passenger state for strategies and presentation adapters."""

    id: int
    request_time: int
    start_floor: int
    destination_floor: int
    status: PassengerStatus
    elevator_id: int | None
    pickup_time: int | None
    dropoff_time: int | None


@dataclass(frozen=True)
class SimulationSnapshot:
    """Immutable state returned after each simulation tick."""

    time: int
    floors: int
    elevators: tuple[ElevatorSnapshot, ...]
    passengers: tuple[PassengerSnapshot, ...]
    complete: bool
