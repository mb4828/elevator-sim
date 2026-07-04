"""Command-line tools for running and comparing strategies."""

import argparse
import importlib
import logging
import re
from collections.abc import Sequence
from pathlib import Path

from rich.console import Console
from rich_argparse import RichHelpFormatter

from elevator_sim.core.models import Elevator
from elevator_sim.core.state_log import write_state_log
from elevator_sim.strategies.base import ElevatorStrategy
from elevator_sim.workload.comparison import (
    StrategyComparisonResult,
    WorkloadConfig,
    build_performance_analysis_table,
    build_summary_statistics_table,
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
        probability=args.probability,
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
    _write_state_logs(args.output_dir, results)

    _print_results(len(passenger_source.passengers), results)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="🛗 Elevator Simulator - Compare elevator scheduling strategies.",
        epilog="©️ Copyright 2026 Matt Brauner",
        formatter_class=RichHelpFormatter,
    )

    parser._optionals.title = "required"  # pylint: disable=W0212
    parser.add_argument("--floors", type=int, metavar="INT", required=True, help="Number of floors in the building.")
    parser.add_argument("--elevators", type=int, metavar="INT", required=True, help="Number of elevators.")
    parser.add_argument(
        "--capacity",
        type=int,
        metavar="INT",
        required=True,
        help="Maximum passenger capacity per elevator.",
    )

    optional_options = parser.add_argument_group("optional")
    optional_options.add_argument(
        "--strategy", metavar="PATH", action="append", default=[], help="Dotted strategy class path."
    )
    optional_options.add_argument(
        "--start-floor", type=int, metavar="INT", default=0, help="Starting floor for every elevator. [Default: 0]"
    )
    optional_options.add_argument(
        "--duration", type=int, metavar="INT", default=200, help="Random workload duration in ticks. [Default: 200]"
    )
    optional_options.add_argument(
        "--seed", type=int, metavar="INT", default=42, help="Random workload seed. [Default: 42]"
    )
    optional_options.add_argument(
        "--probability",
        type=float,
        metavar="FLOAT",
        default=0.25,
        help="Passenger generation probability per tick. [Default: 0.25]",
    )
    optional_options.add_argument(
        "--max-ticks", type=int, metavar="INT", default=100_000, help="Maximum ticks per simulation. [Default: 100,000]"
    )
    optional_options.add_argument(
        "--output-dir",
        type=Path,
        metavar="PATH",
        default=Path("."),
        help="Directory for per-strategy JSON state logs. [Default: .]",
    )
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
        Elevator(id=elevator_id, current_floor=start_floor, capacity=capacity) for elevator_id in range(1, count + 1)
    ]


def _print_no_strategy_result(workload_size: int) -> None:
    """Print workload information when no strategies are provided."""
    print(f"Generated passengers: {workload_size}")
    print("No strategies provided; pass --strategy to run a comparison.")


def _print_results(workload_size: int, results: list[StrategyComparisonResult]) -> None:
    """Print comparison metrics for completed strategy runs."""
    console = Console(width=160)
    console.print(f"Generated passengers: {workload_size}")
    console.print(build_summary_statistics_table(workload_size, results))
    console.print(build_performance_analysis_table(results))


def _write_state_logs(output_dir: Path, results: list[StrategyComparisonResult]) -> None:
    """Write one state log file for each completed strategy run."""
    for comparison in results:
        output_path = output_dir / f"{_safe_file_stem(comparison.strategy_name)}.state-log.json"
        write_state_log(comparison.result.state_log, output_path)


def _safe_file_stem(value: str) -> str:
    """Return a filesystem-safe log filename stem."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "strategy"


if __name__ == "__main__":
    raise SystemExit(main())
