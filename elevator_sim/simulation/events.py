"""Elevator movement and passenger lifecycle event helpers."""

from elevator_sim.core.models import Direction, Elevator, ElevatorServicePhase, Passenger, PassengerStatus


def apply_elevator_events(elevators: list[Elevator], passengers: dict[int, Passenger], time: int) -> None:
    """Apply one movement or service event to every elevator."""
    for elevator in elevators:
        apply_elevator_event(elevator, passengers, time)


def apply_elevator_event(elevator: Elevator, passengers: dict[int, Passenger], time: int) -> None:
    """Apply one movement or service event to an elevator."""
    if elevator.service_phase == ElevatorServicePhase.STOPPING:
        elevator.direction = Direction.IDLE
        advance_service_phase(elevator, passengers)
    elif elevator.service_phase == ElevatorServicePhase.DROPPING_OFF:
        drop_off_passengers(elevator, time)
        if has_pickup_passengers(elevator, passengers):
            elevator.service_phase = ElevatorServicePhase.PICKING_UP
        else:
            remove_current_stop(elevator)
            elevator.service_phase = ElevatorServicePhase.MOVING
    elif elevator.service_phase == ElevatorServicePhase.PICKING_UP:
        pick_up_passengers(elevator, passengers, time)
        remove_current_stop(elevator)
        elevator.service_phase = ElevatorServicePhase.MOVING
    else:
        move_toward_next_stop(elevator)


def advance_service_phase(elevator: Elevator, passengers: dict[int, Passenger]) -> None:
    """Move from stopping into the next service phase that has work."""
    if has_dropoff_passengers(elevator):
        elevator.service_phase = ElevatorServicePhase.DROPPING_OFF
    elif has_pickup_passengers(elevator, passengers):
        elevator.service_phase = ElevatorServicePhase.PICKING_UP
    else:
        remove_current_stop(elevator)
        elevator.service_phase = ElevatorServicePhase.MOVING


def move_toward_next_stop(elevator: Elevator) -> None:
    """Move one floor toward the next stop or prepare to stop at the current floor."""
    if not elevator.target_floors:
        elevator.direction = Direction.IDLE
        return

    next_stop = elevator.target_floors[0]
    if next_stop == elevator.current_floor:
        elevator.direction = Direction.IDLE
        elevator.service_phase = ElevatorServicePhase.STOPPING
    elif next_stop > elevator.current_floor:
        elevator.current_floor += 1
        elevator.direction = Direction.UP
        start_stop_if_arrived(elevator, next_stop)
    else:
        elevator.current_floor -= 1
        elevator.direction = Direction.DOWN
        start_stop_if_arrived(elevator, next_stop)


def start_stop_if_arrived(elevator: Elevator, next_stop: int) -> None:
    """Prepare to consume a stop tick on the next simulation tick if the elevator arrived."""
    if elevator.current_floor == next_stop:
        elevator.service_phase = ElevatorServicePhase.STOPPING


def has_dropoff_passengers(elevator: Elevator) -> bool:
    """Return whether onboard passengers need to exit at the current floor."""
    return any(passenger.destination_floor == elevator.current_floor for passenger in elevator.passengers)


def has_pickup_passengers(elevator: Elevator, passengers: dict[int, Passenger]) -> bool:
    """Return whether assigned waiting passengers are available at the current floor."""
    return any(
        passenger.status == PassengerStatus.WAITING and passenger.start_floor == elevator.current_floor
        for passenger_id in elevator.assigned_passenger_ids
        if (passenger := passengers.get(passenger_id)) is not None
    )


def drop_off_passengers(elevator: Elevator, time: int) -> None:
    """Drop off onboard passengers at the elevator's current floor."""
    remaining_passengers = []
    for passenger in elevator.passengers:
        if passenger.destination_floor == elevator.current_floor:
            passenger.status = PassengerStatus.COMPLETED
            passenger.dropoff_time = time
            passenger.elevator_id = None
        else:
            remaining_passengers.append(passenger)
    elevator.passengers = remaining_passengers


def pick_up_passengers(elevator: Elevator, passengers: dict[int, Passenger], time: int) -> None:
    """Pick up assigned waiting passengers at the elevator's current floor.

    If the elevator is full, passengers waiting at this floor remain waiting
    and are unassigned so a future strategy decision can send another elevator.
    """
    for passenger_id in sorted(elevator.assigned_passenger_ids.copy()):
        passenger = passengers[passenger_id]
        if passenger.status != PassengerStatus.WAITING or passenger.start_floor != elevator.current_floor:
            continue
        if elevator.available_capacity <= 0:
            elevator.assigned_passenger_ids.remove(passenger_id)
            continue
        passenger.status = PassengerStatus.RIDING
        passenger.pickup_time = time
        passenger.elevator_id = elevator.id
        elevator.passengers.append(passenger)
        elevator.assigned_passenger_ids.remove(passenger_id)


def remove_current_stop(elevator: Elevator) -> None:
    """Remove the current floor from the front of the stop queue after service completes."""
    if elevator.target_floors and elevator.target_floors[0] == elevator.current_floor:
        elevator.target_floors.pop(0)
