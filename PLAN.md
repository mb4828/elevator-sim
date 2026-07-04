# Elevator Simulation Framework Plan

## 1. Purpose

This project is a discrete-time elevator simulation harness for building and comparing elevator scheduling strategies.

The implemented scope is:

1. Configurable building size: floors, elevators, and maximum passengers per elevator.
2. Deterministic seeded passenger workloads.
3. Step-by-step simulation through one authoritative `step()` method.
4. Full-run execution through `run()`, which loops over `step()`.
5. Strategy comparison against identical workload configuration.
6. A CLI adapter for running and comparing strategy classes.

The following are intentionally not implemented:

- scheduling strategies;
- FastAPI endpoints;
- UI.

The central design principle is:

> The simulation owns time and advances exactly one discrete tick through `step()`.

---

## 2. Architecture

```text
main.py CLI
    |
    v
workload comparison
    |
    +------------------+
    |                  |
    v                  v
PassengerSource     Simulation
                       |
        +--------------+--------------+
        |              |              |
        v              v              v
    Strategy       Domain Models    Metrics
```

Major components:

- **Core models**: Pydantic mutable domain models, enums, immutable snapshots, and result metrics.
- **Simulation package**: authoritative state machine, event application, decisions, and snapshots.
- **Strategies**: interchangeable scheduling algorithms behind a shared interface.
- **Workload package**: seeded passenger generation and strategy comparison helpers.
- **CLI**: argument parsing and orchestration in `main.py`.

---

## 3. Project Structure

```text
elevator_sim/
├── __init__.py
├── api.py
├── core/
│   ├── __init__.py
│   ├── metrics.py
│   └── models.py
├── simulation/
│   ├── __init__.py
│   ├── decisions.py
│   ├── events.py
│   ├── simulation.py
│   └── snapshots.py
├── strategies/
│   ├── __init__.py
│   ├── base.py
│   ├── collective_control.py
│   └── nearest_car.py
└── workload/
    ├── __init__.py
    ├── comparison.py
    └── passenger_source.py

tests/
├── __init__.py
├── test_main.py
├── test_models.py
├── test_simulation.py
├── test_workload.py
└── test_workload_sources.py

main.py
pyproject.toml
README.md
```

---

## 4. Core Models

`Passenger` and `Elevator` are Pydantic models because they are mutable simulation state with intrinsic validation.
Snapshots and result summaries are frozen dataclasses because strategies and callers should not mutate them.

### Enums

```python
class Direction(str, Enum):
    UP = "up"
    DOWN = "down"
    IDLE = "idle"


class PassengerStatus(str, Enum):
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    RIDING = "riding"
    COMPLETED = "completed"
```

### Passenger

`Passenger` validates:

- positive passenger ID;
- non-negative request time;
- floor values greater than or equal to 1;
- origin and destination differ.

It stores:

- request time;
- origin and destination floors;
- lifecycle status;
- pickup/drop-off timestamps;
- current riding elevator ID.

It derives:

- direction;
- wait time;
- total time.

Building-specific validation lives on `Passenger.validate_for_building(floors, current_time)` because the passenger
model does not know the simulation's configured floor count at construction time.

### Elevator

`Elevator` validates:

- positive elevator ID;
- current floor greater than or equal to 1;
- positive capacity.

It stores:

- current floor;
- observed movement direction;
- service phase;
- onboard passengers;
- assigned waiting passenger IDs;
- ordered target floors.

Building-specific validation lives on `Elevator.validate_for_building(floors)`.

### Snapshots

Strategies receive immutable snapshots:

- `ElevatorSnapshot`
- `PassengerSnapshot`
- `SimulationSnapshot`

Snapshots prevent strategies from mutating the engine directly.

---

## 5. Simulation Tick Order

Each call to `Simulation.step()` advances exactly one tick.

Implemented order:

1. Return the current snapshot immediately if the simulation is stopped.
2. Release passengers scheduled for the current time.
3. Build a snapshot and ask the strategy for decisions.
4. Validate and apply strategy decisions.
5. Apply one movement or service event to each elevator.
6. Increment simulation time.
7. Evaluate completion.
8. Return a new snapshot.

An elevator moves one floor per movement tick, but it can pass intermediate floors if they are not in the ordered stop
queue. When an elevator reaches a stop floor, later ticks are consumed by stopping, dropping off, and picking up.

---

## 6. Simulation Package Responsibilities

### `simulation.py`

Contains the `Simulation` class and public simulation API:

```python
simulation.step()
simulation.run(max_ticks=100_000)
simulation.snapshot()
simulation.result()
```

It owns:

- current time;
- elevator state;
- released passenger state;
- completion state.

It validates:

- building has at least two floors;
- elevator IDs are unique;
- elevators are valid for the configured building;
- released passengers are valid for the configured building and tick;
- passenger IDs are unique.

### `decisions.py`

Validates and applies strategy decisions:

- duplicate elevator decisions are rejected;
- unknown elevator IDs are rejected;
- unknown passenger IDs are rejected;
- non-waiting passenger assignments are rejected;
- assigning one passenger to multiple elevators is rejected;
- stop floors outside building bounds are rejected;
- duplicate stop floors are collapsed while preserving order.

Assignment ownership is indexed once per decision application, then checked by passenger ID.

### `events.py`

Applies per-tick events:

- stop ticks;
- elevator movement toward the next stop;
- passenger drop-off;
- passenger pickup.

If a waiting assigned passenger cannot board because the elevator is full, the passenger remains waiting and is
unassigned so a future strategy decision can assign them again.

### `snapshots.py`

Builds immutable snapshots from mutable simulation state.

---

## 7. Strategy Interface

Strategies implement `ElevatorStrategy`:

```python
@dataclass(frozen=True)
class ElevatorDecision:
    elevator_id: int
    stop_floors: tuple[int, ...] = ()
    assigned_passenger_ids: tuple[int, ...] = ()


class ElevatorStrategy(ABC):
    @abstractmethod
    def plan(self, state: SimulationSnapshot) -> list[ElevatorDecision]:
        raise NotImplementedError
```

Strategies decide. The simulation validates and enforces.

The project contains placeholders only:

- `elevator_sim/strategies/nearest_car.py`
- `elevator_sim/strategies/collective_control.py`

---

## 8. Passenger Workload

The only implemented workload source is `PassengerSource`.

It uses seeded Bernoulli arrivals:

- each tick has an arrival probability;
- each arrival creates one passenger;
- origin and destination are random valid floors;
- origin and destination cannot match;
- the full passenger tuple is generated at initialization.

Public API:

```python
source.passengers_at(time)
source.is_exhausted(time)
source.passengers
```

Because generation is seeded and precomputed, the same workload configuration produces the same passenger requests.

---

## 9. Strategy Comparison

`WorkloadConfig` stores workload settings:

- floors;
- arrival probability;
- duration;
- seed.

`compare_strategies()` creates a fresh `PassengerSource` and fresh elevators for each strategy. This provides fair
comparison without sharing mutated passenger or elevator objects across runs.

---

## 10. Metrics

Metrics are derived from passenger timestamps rather than maintained redundantly.

Required passenger metrics:

- wait time: `pickup_time - request_time`;
- total time: `dropoff_time - request_time`.

`MetricsSummary` reports:

- completed passengers;
- average/minimum/maximum wait time;
- average/minimum/maximum total time.

Zero-passenger runs are handled without division-by-zero errors.

---

## 11. CLI

`main.py` is the CLI adapter.

Required options:

- `--floors`
- `--elevators`
- `--max-passengers` / `--capacity`

Optional options:

- `--strategy`
- `--start-floor`
- `--duration`
- `--seed`
- `--arrival-probability`
- `--max-ticks`

No strategy is required. If no strategy is provided, the CLI reports the generated passenger count and exits.

---

## 12. Final Design Principles

1. **One source of truth**  
   The simulation owns all mutable run state.

2. **One execution primitive**  
   Every mode advances through `step()`.

3. **Strategies decide, simulation enforces**  
   Strategy code proposes actions; the simulation protects invariants.

4. **Randomness is seeded**  
   Workloads are reproducible.

5. **Comparisons use identical configuration**  
   Each strategy receives fresh objects generated from the same workload settings.

6. **Snapshots cross boundaries**  
   Strategies and future adapters consume immutable snapshots.

7. **Metrics come from timestamps**  
   Derived values are calculated from passenger state.

8. **The web layer is optional**  
   The simulation remains runnable and testable without FastAPI or React.
