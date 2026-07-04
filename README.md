# Elevator Sim

Discrete-time elevator simulation harness for building and testing scheduling strategies.

&copy; 2026 Matt Brauner

## Setup

```bash
uv sync
```

## Run Tests

```bash
uv run pytest
```

The test command prints coverage and fails if total coverage drops below 80%.

## Run A Strategy

The required runtime configuration is:

- `--floors`
- `--elevators`
- `--max-passengers`

Run one strategy by passing its dotted class path:

```bash
uv run python main.py \
  --floors 10 \
  --elevators 2 \
  --max-passengers 6 \
  --strategy your_package.your_module.MyStrategy
```

Optional workload arguments include `--duration`, `--seed`, `--arrival-probability`, `--start-floor`, and
`--max-ticks`.

## Compare Strategies

Pass multiple `--strategy` values to compare strategies against the same seeded workload. Each strategy receives fresh
elevator and passenger objects.

```bash
uv run python main.py \
  --floors 10 \
  --elevators 2 \
  --max-passengers 6 \
  --strategy your_package.your_module.MyStrategy \
  --strategy another_package.other_module.OtherStrategy \
  --duration 200 \
  --seed 42 \
  --arrival-probability 0.25
```

## Implement A Strategy

Create a class that inherits from `ElevatorStrategy` and returns `ElevatorDecision` objects from `plan()`.
Strategies receive immutable snapshots; the simulation engine enforces capacity, floor bounds, one-floor-per-tick
movement, pickup timing, and drop-off timing.

```python
from elevator_sim.core.models import Direction, SimulationSnapshot
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy


class MyStrategy(ElevatorStrategy):
    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        return [
            ElevatorDecision(
                elevator_id=state.elevators[0].id,
                direction=Direction.IDLE,
                assigned_passenger_ids=(),
            )
        ]
```
