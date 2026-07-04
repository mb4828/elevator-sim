"""Command-line tools for running and comparing strategies."""

from __future__ import annotations

import argparse
import importlib
import logging
from collections.abc import Sequence

from elevator_sim.core.models import Elevator
from elevator_sim.strategies.base import ElevatorStrategy
from elevator_sim.workload.comparison import (
    StrategyComparisonResult,
    WorkloadConfig,
    compare_strategies,
    create_passenger_source,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the elevator simulation comparison CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)

    workload_config = WorkloadConfig(
        floors=args.floors,
        arrival_probability=args.arrival_probability,
        duration=args.duration,
        seed=args.seed,
    )
    passenger_source = create_passenger_source(workload_config)

    strategies = {path: _load_strategy_factory(path) for path in args.strategy}
    if not strategies:
        _print_no_strategy_result(len(passenger_source.passengers))
        return 0

    results = compare_strategies(
        workload_config=workload_config,
        elevator_factory=lambda: _create_elevators(args.elevators, args.capacity, args.start_floor),
        strategies=strategies,
        max_ticks=args.max_ticks,
    )

    _print_results(len(passenger_source.passengers), results)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Elevator Simulator - Compare elevator scheduling strategies.",
        epilog="(c) 2026 Matt Brauner",
    )

    parser._optionals.title = "required"  # pylint: disable=W0212
    parser.add_argument("--floors", type=int, required=True, help="Number of floors in the building.")
    parser.add_argument("--elevators", type=int, required=True, help="Number of elevators.")
    parser.add_argument(
        "--max-passengers",
        "--capacity",
        dest="capacity",
        type=int,
        required=True,
        help="Maximum passenger capacity per elevator.",
    )

    optional_options = parser.add_argument_group("optional")
    optional_options.add_argument("--strategy", action="append", default=[], help="Dotted strategy class path.")
    optional_options.add_argument("--start-floor", type=int, default=1, help="Starting floor for every elevator.")
    optional_options.add_argument("--duration", type=int, default=200, help="Random workload duration in ticks.")
    optional_options.add_argument("--seed", type=int, default=42, help="Random workload seed.")
    optional_options.add_argument(
        "--arrival-probability",
        type=float,
        default=0.25,
        help="Passenger arrival probability per tick.",
    )
    optional_options.add_argument("--max-ticks", type=int, default=100_000, help="Maximum ticks per simulation.")
    return parser


def _load_strategy_factory(path: str) -> type[ElevatorStrategy]:
    """Load and validate an elevator strategy class from a dotted import path."""
    module_name, separator, class_name = path.rpartition(".")
    if not separator:
        raise ValueError(f"strategy must be a dotted class path: {path}")
    strategy_class = getattr(importlib.import_module(module_name), class_name)
    if not issubclass(strategy_class, ElevatorStrategy):
        raise TypeError(f"{path} is not an ElevatorStrategy")
    return strategy_class


def _create_elevators(count: int, capacity: int, start_floor: int) -> list[Elevator]:
    """Create configured elevator instances for one simulation run."""
    if count <= 0:
        raise ValueError("elevators must be positive")
    return [
        Elevator(id=elevator_id, current_floor=start_floor, capacity=capacity)
        for elevator_id in range(1, count + 1)
    ]


def _print_no_strategy_result(workload_size: int) -> None:
    """Print workload information when no strategies are provided."""
    print(f"Generated passengers: {workload_size}")
    print("No strategies provided; pass --strategy to run a comparison.")


def _print_results(workload_size: int, results: list[StrategyComparisonResult]) -> None:
    """Print comparison metrics for completed strategy runs."""
    print(f"Generated passengers: {workload_size}")
    for comparison in results:
        metrics = comparison.result.metrics
        print(
            f"{comparison.strategy_name}: "
            f"ticks={comparison.result.ticks}, "
            f"completed={metrics.completed_passengers}, "
            f"avg_wait={metrics.average_wait_time}, "
            f"max_wait={metrics.maximum_wait_time}, "
            f"avg_total={metrics.average_total_time}"
        )


if __name__ == "__main__":
    raise SystemExit(main())
