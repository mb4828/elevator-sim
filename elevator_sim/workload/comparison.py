"""Workload configuration and strategy comparison helpers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from elevator_sim.core.metrics import SimulationResult
from elevator_sim.core.models import Elevator
from elevator_sim.simulation import Simulation
from elevator_sim.strategies.base import ElevatorStrategy
from elevator_sim.workload.passenger_source import PassengerSource


ElevatorFactory = Callable[[], list[Elevator]]
StrategyFactory = Callable[[], ElevatorStrategy]


@dataclass(frozen=True)
class WorkloadConfig:
    """Configuration used to create identical seeded passenger workloads."""

    floors: int
    arrival_probability: float
    duration: int
    seed: int


@dataclass(frozen=True)
class StrategyComparisonResult:
    """Result from running one strategy against a shared workload configuration."""

    strategy_name: str
    result: SimulationResult


def create_passenger_source(workload_config: WorkloadConfig) -> PassengerSource:
    """Create a passenger source from workload settings."""
    return PassengerSource(
        floors=workload_config.floors,
        duration=workload_config.duration,
        arrival_probability=workload_config.arrival_probability,
        seed=workload_config.seed,
    )


def compare_strategies(
    workload_config: WorkloadConfig,
    elevator_factory: ElevatorFactory,
    strategies: dict[str, StrategyFactory],
    max_ticks: int = 100_000,
) -> list[StrategyComparisonResult]:
    """Run each strategy against fresh elevators and identical seeded passenger sources."""
    results: list[StrategyComparisonResult] = []
    for name, strategy_factory in strategies.items():
        simulation = Simulation(
            floors=workload_config.floors,
            elevators=elevator_factory(),
            strategy=strategy_factory(),
            passenger_source=create_passenger_source(workload_config),
        )
        results.append(
            StrategyComparisonResult(
                strategy_name=name,
                result=simulation.run(max_ticks=max_ticks),
            )
        )
    return results
