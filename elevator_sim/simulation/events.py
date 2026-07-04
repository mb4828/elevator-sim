"""Passenger lifecycle event helpers."""

from elevator_sim.core.models import Direction, Elevator, Passenger, PassengerStatus


def apply_direction(elevator: Elevator, direction: Direction, floors: int) -> None:
    """Apply a strategy direction while enforcing building boundaries."""
    if direction == Direction.DOWN and elevator.current_floor <= 1:
        elevator.direction = Direction.IDLE
    elif direction == Direction.UP and elevator.current_floor >= floors:
        elevator.direction = Direction.IDLE
    else:
        elevator.direction = direction


def move_elevators(elevators: list[Elevator], floors: int) -> None:
    """Move every elevator by at most one floor."""
    for elevator in elevators:
        if elevator.direction == Direction.UP and elevator.current_floor < floors:
            elevator.current_floor += 1
        elif elevator.direction == Direction.DOWN and elevator.current_floor > 1:
            elevator.current_floor -= 1


def drop_off_passengers(elevators: list[Elevator], time: int) -> None:
    """Drop off onboard passengers at their destination floor."""
    for elevator in elevators:
        remaining_passengers = []
        for passenger in elevator.passengers:
            if passenger.destination_floor == elevator.current_floor:
                passenger.status = PassengerStatus.COMPLETED
                passenger.dropoff_time = time
                passenger.elevator_id = None
            else:
                remaining_passengers.append(passenger)
        elevator.passengers = remaining_passengers


def pick_up_passengers(elevators: list[Elevator], passengers: dict[int, Passenger], time: int) -> None:
    """Pick up assigned waiting passengers at each elevator's current floor."""
    for elevator in elevators:
        for passenger_id in sorted(elevator.assigned_passenger_ids):
            if elevator.available_capacity <= 0:
                break
            passenger = passengers[passenger_id]
            if passenger.status == PassengerStatus.WAITING and passenger.start_floor == elevator.current_floor:
                passenger.status = PassengerStatus.RIDING
                passenger.pickup_time = time
                passenger.elevator_id = elevator.id
                elevator.passengers.append(passenger)
                elevator.assigned_passenger_ids.remove(passenger_id)
