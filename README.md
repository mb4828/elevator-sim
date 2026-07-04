# Elevator Sim

Discrete-time elevator simulation harness for building and testing scheduling strategies.

Estimated project time: <!-- project-time:start -->3h 38m<!-- project-time:end -->

&copy; 2026 Matt Brauner

## Setup

```bash
uv sync
git config core.hooksPath .githooks
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
- `--capacity`

Run one strategy by passing its dotted class path:

```bash
uv run python main.py \
  --floors 10 \
  --elevators 2 \
  --capacity 6 \
  --strategy your_package.your_module.MyStrategy
```

Optional workload arguments include `--duration`, `--seed`, `--probability`, `--start-floor`, and
`--max-ticks`.

Floors are zero-based. For example, `--floors 10` creates floors `0` through `9`, and `--start-floor` defaults to `0`.

Completed strategy runs also write per-tick JSON state logs to the current directory by default. Each entry includes the
elevator positions plus the full elevator and passenger state for visualization. Use `--output-dir` to choose a
different output directory.

## Compare Strategies

Pass multiple `--strategy` values to compare strategies against the same seeded workload. Each strategy receives fresh
elevator and passenger objects.

```bash
uv run python main.py \
  --floors 10 \
  --elevators 2 \
  --capacity 6 \
  --strategy your_package.your_module.MyStrategy \
  --strategy another_package.other_module.OtherStrategy \
```

## Implement A Strategy

Create a class that inherits from `ElevatorStrategy` and returns `ElevatorDecision` objects from `plan()`.
Strategies receive immutable snapshots; the simulation engine enforces capacity, floor bounds, one-floor-per-tick
movement, stop timing, pickup timing, and drop-off timing.

```python
from elevator_sim.core.models import SimulationSnapshot
from elevator_sim.strategies.base import ElevatorDecision, ElevatorStrategy


class MyStrategy(ElevatorStrategy):
    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        return [
            ElevatorDecision(
                elevator_id=state.elevators[0].id,
                stop_floors=(),
                assigned_passenger_ids=(),
            )
        ]
```
