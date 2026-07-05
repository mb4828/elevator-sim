"""Tests for the discrete-time simulation engine."""

import pytest

from elevator_sim.core.models import (
    Direction,
    Elevator,
    ElevatorServicePhase,
    Passenger,
    PassengerStatus,
    SimulationSnapshot,
)
from elevator_sim.simulation import Simulation
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy
from elevator_sim.workload.passenger_source import PassengerSource


class StaticPassengerSource:
    """Test passenger source with explicit passenger requests."""

    def __init__(self, passengers: tuple[Passenger, ...]) -> None:
        self.passengers = passengers

    def passengers_at(self, time: int) -> tuple[Passenger, ...]:
        """Return passengers scheduled for the requested tick."""
        return tuple(passenger for passenger in self.passengers if passenger.request_time == time)

    def is_exhausted(self, time: int) -> bool:
        """Return whether all configured passengers have been released."""
        return all(passenger.request_time < time for passenger in self.passengers)


class DirectPassengerStrategy(ElevatorStrategy):
    """Test strategy that assigns one passenger and follows pickup/drop-off floors."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        elevator = state.elevators[0]
        passenger = next(
            (passenger for passenger in state.passengers if passenger.status != PassengerStatus.COMPLETED),
            None,
        )
        if passenger is None:
            return [ElevatorDecision(elevator.id)]
        assigned_ids = () if passenger.status == PassengerStatus.RIDING else (passenger.id,)
        target_floor = (
            passenger.destination_floor if passenger.status == PassengerStatus.RIDING else passenger.start_floor
        )
        return [ElevatorDecision(elevator.id, stop_floors=(target_floor,), assigned_passenger_ids=assigned_ids)]


class InvalidElevatorStrategy(ElevatorStrategy):
    """Test strategy that references a missing elevator."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        return [ElevatorDecision(elevator_id=999)]


class BoundaryStrategy(ElevatorStrategy):
    """Test strategy that stops at the current boundary floor."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        return [ElevatorDecision(elevator_id=1, stop_floors=(1,))]


class StopQueueStrategy(ElevatorStrategy):
    """Test strategy that returns a fixed stop queue."""

    def __init__(self, stop_floors: tuple[int, ...], assigned_passenger_ids: tuple[int, ...] = ()) -> None:
        self.stop_floors = stop_floors
        self.assigned_passenger_ids = assigned_passenger_ids

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        waiting_passenger_ids = {
            passenger.id for passenger in state.passengers if passenger.status == PassengerStatus.WAITING
        }
        return [
            ElevatorDecision(
                elevator_id=state.elevators[0].id,
                stop_floors=self.stop_floors,
                assigned_passenger_ids=tuple(
                    passenger_id
                    for passenger_id in self.assigned_passenger_ids
                    if passenger_id in waiting_passenger_ids
                ),
            )
        ]


class DwellStrategy(ElevatorStrategy):
    """Test strategy that updates stops as passengers finish service phases."""

    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        elevator = state.elevators[0]
        waiting_passengers = [
            passenger for passenger in state.passengers if passenger.status == PassengerStatus.WAITING
        ]
        riding_passengers = [passenger for passenger in state.passengers if passenger.status == PassengerStatus.RIDING]
        stop_floors = tuple(
            dict.fromkeys(
                [passenger.start_floor for passenger in waiting_passengers]
                + [passenger.destination_floor for passenger in riding_passengers]
            )
        )
        return [
            ElevatorDecision(
                elevator_id=elevator.id,
                stop_floors=stop_floors,
                assigned_passenger_ids=tuple(passenger.id for passenger in waiting_passengers),
            )
        ]


def test_run_completes_single_passenger_trip() -> None:
    """Simulation releases, picks up, moves, drops off, and records metrics."""
    passenger_source = PassengerSource(floors=5, passengers=1, duration=1, seed=7)
    simulation = Simulation(
        floors=5,
        elevators=[Elevator(id=1, current_floor=1, capacity=4)],
        strategy=DirectPassengerStrategy(),
        passenger_source=passenger_source,
    )

    result = simulation.run(max_ticks=10)

    assert result.metrics.completed_passengers == 1
    assert result.passengers[0].status == PassengerStatus.COMPLETED


def test_elevator_without_assigned_work_reports_idle_phase() -> None:
    """An elevator with no destination reports an idle service phase, not moving."""
    simulation = Simulation(
        floors=4,
        elevators=[Elevator(id=1, current_floor=2, capacity=4)],
        strategy=DirectPassengerStrategy(),
        passenger_source=StaticPassengerSource(()),
    )

    initial_snapshot = simulation.state_log[0]
    snapshot = simulation.step()

    assert initial_snapshot.elevators[0].service_phase == ElevatorServicePhase.IDLE
    assert snapshot.elevators[0].current_floor == 2
    assert snapshot.elevators[0].service_phase == ElevatorServicePhase.IDLE


def test_run_records_performance_summary() -> None:
    """Simulation records queue depth and utilization across completed ticks."""
    passenger = Passenger(id=1, request_time=0, start_floor=1, destination_floor=2)
    simulation = Simulation(
        floors=3,
        elevators=[Elevator(id=1, current_floor=1, capacity=2)],
        strategy=DirectPassengerStrategy(),
        passenger_source=StaticPassengerSource((passenger,)),
    )

    result = simulation.run(max_ticks=10)

    assert result.performance.total_ticks == 6
    assert result.performance.average_passengers_per_tick == 0.5
    assert result.performance.peak_queue == 1
    assert result.performance.total_riding_ticks == 3
    assert result.performance.total_capacity_ticks == 12
    assert result.performance.efficiency_score == 25.0
    assert result.performance.utilization == pytest.approx(83.333, abs=1e-3)


def test_run_records_complete_state_log() -> None:
    """Simulation result includes the initial state and every completed tick."""
    passenger = Passenger(id=1, request_time=0, start_floor=1, destination_floor=2)
    simulation = Simulation(
        floors=3,
        elevators=[Elevator(id=1, current_floor=1, capacity=2)],
        strategy=DirectPassengerStrategy(),
        passenger_source=StaticPassengerSource((passenger,)),
    )

    result = simulation.run(max_ticks=10)

    assert len(result.state_log) == result.ticks + 1
    assert result.state_log[0].time == 0
    assert result.state_log[0].elevators[0].current_floor == 1
    assert result.state_log[-1].complete is True
    assert result.state_log[-1].passengers[0].status == PassengerStatus.COMPLETED


def test_step_keeps_elevator_idle_at_current_boundary_stop() -> None:
    """Simulation keeps an elevator idle when its next stop is the current boundary floor."""
    simulation = Simulation(
        floors=2,
        elevators=[Elevator(id=1, current_floor=1, capacity=1)],
        strategy=BoundaryStrategy(),
        passenger_source=PassengerSource(floors=2, passengers=0, duration=0, seed=1),
    )

    snapshot = simulation.step()

    assert snapshot.elevators[0].current_floor == 1
    assert snapshot.elevators[0].direction == Direction.IDLE


def test_unknown_elevator_decision_raises_error() -> None:
    """Simulation rejects strategy decisions for missing elevators."""
    simulation = Simulation(
        floors=3,
        elevators=[Elevator(id=1, current_floor=1, capacity=1)],
        strategy=InvalidElevatorStrategy(),
        passenger_source=PassengerSource(floors=3, passengers=1, duration=1, seed=1),
    )

    with pytest.raises(ValueError, match="unknown elevator ID"):
        simulation.step()


def test_elevator_skips_intermediate_floor_without_stopping() -> None:
    """Elevator passes intermediate floors unless they are first in the stop queue."""
    simulation = Simulation(
        floors=5,
        elevators=[Elevator(id=1, current_floor=1, capacity=1)],
        strategy=StopQueueStrategy(stop_floors=(4,)),
        passenger_source=StaticPassengerSource(()),
    )

    first_snapshot = simulation.step()
    second_snapshot = simulation.step()

    assert first_snapshot.elevators[0].current_floor == 2
    assert first_snapshot.elevators[0].service_phase == ElevatorServicePhase.MOVING
    assert second_snapshot.elevators[0].current_floor == 3
    assert second_snapshot.elevators[0].service_phase == ElevatorServicePhase.MOVING


def test_stop_queue_uses_separate_stop_dropoff_and_pickup_ticks() -> None:
    """Elevator service consumes stop, drop-off, and pickup ticks after arrival."""
    onboard_passenger = Passenger(
        id=1,
        request_time=0,
        start_floor=1,
        destination_floor=2,
        status=PassengerStatus.RIDING,
        pickup_time=0,
        elevator_id=1,
    )
    waiting_passenger = Passenger(id=2, request_time=0, start_floor=2, destination_floor=3)
    elevator = Elevator(id=1, current_floor=1, capacity=2, passengers=[onboard_passenger])
    simulation = Simulation(
        floors=4,
        elevators=[elevator],
        strategy=DwellStrategy(),
        passenger_source=StaticPassengerSource((waiting_passenger,)),
    )

    arrived = simulation.step()
    stopped = simulation.step()
    dropped_off = simulation.step()
    picked_up = simulation.step()
    moved_again = simulation.step()

    assert arrived.elevators[0].current_floor == 2
    assert arrived.elevators[0].service_phase == ElevatorServicePhase.STOPPING
    assert stopped.elevators[0].passenger_count == 1
    assert stopped.passengers[0].status == PassengerStatus.WAITING
    assert stopped.elevators[0].service_phase == ElevatorServicePhase.DROPPING_OFF
    assert dropped_off.elevators[0].passenger_count == 0
    assert dropped_off.passengers[0].status == PassengerStatus.WAITING
    assert dropped_off.elevators[0].service_phase == ElevatorServicePhase.PICKING_UP
    assert picked_up.passengers[0].status == PassengerStatus.RIDING
    assert picked_up.elevators[0].current_floor == 2
    assert moved_again.elevators[0].current_floor == 3


def test_dropoff_stop_skips_pickup_when_no_passengers_are_waiting() -> None:
    """Elevator goes idle after drop-off when no assigned passenger can board and no stop is queued."""
    onboard_passenger = Passenger(
        id=1,
        request_time=0,
        start_floor=1,
        destination_floor=2,
        status=PassengerStatus.RIDING,
        pickup_time=0,
        elevator_id=1,
    )
    elevator = Elevator(id=1, current_floor=1, capacity=1, passengers=[onboard_passenger])
    simulation = Simulation(
        floors=3,
        elevators=[elevator],
        strategy=StopQueueStrategy(stop_floors=(2,)),
        passenger_source=StaticPassengerSource(()),
    )

    arrived = simulation.step()
    stopped = simulation.step()
    dropped_off = simulation.step()

    assert arrived.elevators[0].service_phase == ElevatorServicePhase.STOPPING
    assert stopped.elevators[0].service_phase == ElevatorServicePhase.DROPPING_OFF
    assert dropped_off.elevators[0].passenger_count == 0
    assert dropped_off.elevators[0].service_phase == ElevatorServicePhase.IDLE


def test_current_floor_stop_waits_before_pickup() -> None:
    """Stop at the current floor starts service timing instead of picking up immediately."""
    passenger = Passenger(id=1, request_time=0, start_floor=1, destination_floor=2)
    simulation = Simulation(
        floors=3,
        elevators=[Elevator(id=1, current_floor=1, capacity=1)],
        strategy=StopQueueStrategy(stop_floors=(1,), assigned_passenger_ids=(1,)),
        passenger_source=StaticPassengerSource((passenger,)),
    )

    first_snapshot = simulation.step()
    second_snapshot = simulation.step()
    third_snapshot = simulation.step()

    assert first_snapshot.passengers[0].status == PassengerStatus.WAITING
    assert first_snapshot.elevators[0].service_phase == ElevatorServicePhase.STOPPING
    assert second_snapshot.passengers[0].status == PassengerStatus.WAITING
    assert second_snapshot.elevators[0].service_phase == ElevatorServicePhase.PICKING_UP
    assert third_snapshot.passengers[0].status == PassengerStatus.RIDING
    assert third_snapshot.elevators[0].service_phase == ElevatorServicePhase.IDLE


def test_passenger_who_cannot_fit_is_unassigned_and_stays_waiting() -> None:
    """Passenger remains waiting and becomes unassigned if the elevator is full at pickup."""
    onboard_passenger = Passenger(
        id=1,
        request_time=0,
        start_floor=1,
        destination_floor=3,
        status=PassengerStatus.RIDING,
        pickup_time=0,
        elevator_id=1,
    )
    waiting_passenger = Passenger(id=2, request_time=0, start_floor=1, destination_floor=2)
    elevator = Elevator(id=1, current_floor=1, capacity=1, passengers=[onboard_passenger])
    simulation = Simulation(
        floors=4,
        elevators=[elevator],
        strategy=StopQueueStrategy(stop_floors=(1,), assigned_passenger_ids=(2,)),
        passenger_source=StaticPassengerSource((waiting_passenger,)),
    )

    simulation.step()
    simulation.step()
    snapshot = simulation.step()

    assert snapshot.passengers[0].status == PassengerStatus.WAITING
    assert snapshot.passengers[0].elevator_id is None
    assert snapshot.elevators[0].assigned_passenger_ids == ()


def test_invalid_stop_floor_raises_error() -> None:
    """Simulation rejects strategy stop floors outside building bounds."""
    simulation = Simulation(
        floors=3,
        elevators=[Elevator(id=1, current_floor=1, capacity=1)],
        strategy=StopQueueStrategy(stop_floors=(3,)),
        passenger_source=StaticPassengerSource(()),
    )

    with pytest.raises(ValueError, match="stop floor"):
        simulation.step()


def test_duplicate_stop_floors_are_collapsed() -> None:
    """Simulation removes duplicate stop floors while preserving order."""
    simulation = Simulation(
        floors=5,
        elevators=[Elevator(id=1, current_floor=1, capacity=1)],
        strategy=StopQueueStrategy(stop_floors=(3, 3, 2, 3)),
        passenger_source=StaticPassengerSource(()),
    )

    snapshot = simulation.step()

    assert snapshot.elevators[0].target_floors == (3, 2)


def test_pickup_boards_only_passengers_travelling_in_onward_direction() -> None:
    """An up-bound stop boards only up-bound passengers; opposite-direction ones stay waiting."""
    up_passenger = Passenger(id=1, request_time=0, start_floor=5, destination_floor=6)
    down_passenger = Passenger(id=2, request_time=0, start_floor=5, destination_floor=0)
    simulation = Simulation(
        floors=8,
        elevators=[Elevator(id=1, current_floor=4, capacity=4)],
        # Queue continues up (to 6) before reversing (to 0), so the stop at 5 is an up-bound stop.
        strategy=StopQueueStrategy(stop_floors=(5, 6, 0), assigned_passenger_ids=(1, 2)),
        passenger_source=StaticPassengerSource((up_passenger, down_passenger)),
    )

    simulation.step()  # move 4 -> 5 (arrive, stopping)
    simulation.step()  # stopping -> picking_up
    snapshot = simulation.step()  # picking_up boards only the up-bound passenger

    boarded = {passenger.id: passenger.status for passenger in snapshot.passengers}
    assert boarded[1] == PassengerStatus.RIDING
    assert boarded[2] == PassengerStatus.WAITING
    assert snapshot.elevators[0].passenger_count == 1
    assert 2 in snapshot.elevators[0].assigned_passenger_ids
