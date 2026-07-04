# Elevator Sim

Discrete-time elevator simulation harness for building and testing scheduling strategies.

Estimated project time: <!-- project-time:start -->4h 57m<!-- project-time:end -->

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

Run one strategy by passing its module name under `elevator_sim.strategies`:

```bash
uv run python main.py \
  --floors 10 \
  --elevators 2 \
  --capacity 6 \
  --strategy nearest_car
```

Optional workload arguments include `--duration`, `--seed`, `--passengers`, `--start-floor`, and
`--max-ticks`.

Floors are zero-based. For example, `--floors 10` creates floors `0` through `9`, and `--start-floor` defaults to `0`.

Completed strategy runs also write compact JSON visualization logs to the current directory by default. Each log stores
static elevator and passenger metadata once, plus per-tick animation frames. Use `--output-dir` to choose a different
output directory.

## Compare Strategies

Pass multiple `--strategy` values to compare strategies against the same seeded workload. Each strategy receives fresh
elevator and passenger objects.

```bash
uv run python main.py \
  --floors 10 \
  --elevators 2 \
  --capacity 6 \
  --strategy nearest_car \
  --strategy another_strategy \
```

## Implement A Strategy

Create a class that inherits from `ElevatorStrategy` and returns `ElevatorDecision` objects from `plan()`.
Place each strategy in its own module under `elevator_sim/strategies`; the CLI discovers the strategy class from that
module name.
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
