# Elevator Simulator

Discrete-time elevator simulation harness for building and testing scheduling strategies.

**See [`frontend/`](frontend/) for the React app used to visualize the JSON output produced by the Python simulation
script.**

Estimated project time: <!-- project-time:start -->15h 14m<!-- project-time:end -->

&copy; Copyright 2026 Matt Brauner

![screenshot.png](screenshot.png)

### Assumptions / Simplifiactions / Tradeoffs

- Simulation is tick based; elevators move at most 1 floor per tick; stopping, loading, and unloading require 1 tick each
- Passengers come from an input file that is arbitrary and doesn't simulate real building traffic patterns
- Passenger patience is infinite and passengers never leave the queue once they join
- Electricity usage and other supply-side factors aren't taken into account besides utilization %

### What Could Be Improved

- The simulation currently assigns every passenger to an elevator on the tick they enter (per [`INSTRUCTIONS.md`](INSTRUCTIONS.md)); allowing assignments to be deferred and revised over multiple ticks, rather than committed immediately, could yield further efficiency gains
- Make simulation time based and simulate elevator speed, acceleration, and deceleration; simulate passenger loading and unloading times more realistically
- Better passenger generation including simulations for start of day, lunch, end of day, and randomized traffic
- Add passenger attrition for longer wait times
- Incorporate supply-side factors to the performance analysis like electricity usage
- Allow for simultaneous testing of different elevator configurations, number of elevators, capacity, etc.
- Allow for simultaneous testing of multiple passenger input files
- Continue to refine the cost function for the minimum_cost strategy


### Fairness vs. Efficiency

Comparing strategies across a mixed-traffic workload ([`sample_input.csv`](sample_data/sample_input.csv)) and a
morning up-peak where everyone boards at the lobby ([`sample_rush_hour.csv`](sample_data/sample_rush_hour.csv))
surfaced a few takeaways:

- **No single strategy wins everywhere.** `minimum_cost` gives the lowest average wait on mixed traffic, while the
  naive `round_robin` stays competitive across patterns because it distributes load structurally rather than reacting
  to it.
- **Traffic shape matters as much as the algorithm.** A pure up-peak is actually *easier* for most strategies (waits
  drop ~30% vs. mixed traffic) because demand is predictable and batchable — provided the strategy keeps both cars busy
  instead of stacking the crowd onto one.
- **`minimum_cost` balances fairness against efficiency explicitly.** Its cost function scores each candidate car by
  travel time plus a capacity penalty that scales with the passengers already assigned to it, so overflow spills to an
  emptier car rather than piling onto the cheapest route.
- **Average wait can hide unfairness.** The mean alone can look healthy while one car does most of the work — peak
  queue, utilization, and worst-passenger wait are the metrics that expose an imbalanced load.


## Setup

```bash
uv sync
git config core.hooksPath .githooks  # for black formatting and project time pre-commit hooks
```

## Run Tests

```bash
uv run pytest
```

The test command prints coverage and fails if total coverage drops below 80%.

## Run A Strategy

Run one strategy by passing its module name under `elevator_sim.strategies`:

```bash
uv run python main.py \
  --floors 10 \
  --elevators 2 \
  --capacity 6 \
  --input-file ./sample_data/sample_input.csv \
  --strategy nearest_car_same_direction
```
The simulator reads passengers from a CSV file with this exact header:
`time,id,source,dest`. The simulation assigns each passenger a zero-based numeric ID for internal scheduling and writes
the original CSV `id` value as `full_id` in the output passenger metadata for display.

Completed strategy runs also write JSON logs to the current directory by default. Each log stores
static elevator and passenger metadata once, plus per-tick animation frames. Use `--output-dir` to choose a different
output directory.

## Compare Strategies

Pass multiple `--strategy` values to compare strategies against the same input workload:

```bash
uv run python main.py \
  --floors 10 \
  --elevators 2 \
  --capacity 6 \
  --input-file ./sample_data/sample_input.csv \
  --strategy round_robin \
  --strategy nearest_car \
  --strategy nearest_car_same_direction \
  --strategy minimum_cost
```

Each strategy produces a `log.json` file with results.

## Implement A Strategy

Create a class that inherits from `ElevatorStrategy` and returns `ElevatorDecision` objects from `plan()`.
Place each strategy in its own module under `elevator_sim/strategies`; the CLI discovers the strategy class from that
module name.
Strategies receive immutable snapshots; the simulation engine enforces capacity, floor bounds, one-floor-per-tick
movement, stop timing, loading timing, and unloading timing.

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
