"""Command-line tools for running and comparing strategies."""

import argparse
import importlib
import inspect
import logging
import re
from collections.abc import Sequence
from pathlib import Path
from time import perf_counter

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
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the elevator simulation comparison CLI."""
    parser = _build_parser()
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.WARNING)

    workload_config = WorkloadConfig(
        floors=args.floors,
        input_file=args.input_file,
    )
    strategies = {name: _load_strategy_factory(name) for name in args.strategy}
    simulation_start = perf_counter()
    results = compare_strategies(
        workload_config=workload_config,
        elevator_factory=lambda: _create_elevators(args.elevators, args.capacity, args.start_floor),
        strategies=strategies,
        max_ticks=args.max_ticks,
    )
    simulation_runtime_seconds = perf_counter() - simulation_start
    _write_state_logs(args.output_dir, results)

    _print_results(len(results[0].result.passengers), results, simulation_runtime_seconds)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="Elevator Simulator - Compare elevator scheduling strategies.",
        epilog="(c) Copyright 2026 Matt Brauner",
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
    parser.add_argument(
        "--strategy",
        metavar="NAME",
        action="append",
        required=True,
        help="Strategy module name under elevator_sim.strategies.",
    )
    parser.add_argument(
        "--input-file",
        type=Path,
        metavar="PATH",
        required=True,
        help="CSV workload file with header: time,id,source,dest.",
    )

    optional_options = parser.add_argument_group("optional")
    optional_options.add_argument(
        "--start-floor", type=int, metavar="INT", default=0, help="Starting floor for every elevator. [Default: 0]"
    )
    optional_options.add_argument(
        "--max-ticks", type=int, metavar="INT", default=1_000, help="Maximum ticks per simulation. [Default: 1,000]"
    )
    optional_options.add_argument(
        "--output-dir",
        type=Path,
        metavar="PATH",
        default=Path("."),
        help="Directory for per-strategy JSON state logs. [Default: .]",
    )
    return parser


def _load_strategy_factory(name: str) -> type[ElevatorStrategy]:
    """Load the strategy class from an elevator_sim.strategies submodule."""
    module_name = f"elevator_sim.strategies.{name}"
    strategy_classes = [
        strategy_class
        for _, strategy_class in inspect.getmembers(importlib.import_module(module_name), inspect.isclass)
        if issubclass(strategy_class, ElevatorStrategy)
        and strategy_class is not ElevatorStrategy
        and strategy_class.__module__ == module_name
    ]
    if len(strategy_classes) != 1:
        raise ValueError(f"strategy module must define exactly one ElevatorStrategy subclass: {module_name}")
    return strategy_classes[0]


def _create_elevators(count: int, capacity: int, start_floor: int) -> list[Elevator]:
    """Create configured elevator instances for one simulation run."""
    if count <= 0:
        raise ValueError("elevators must be positive")
    return [
        Elevator(id=elevator_id, current_floor=start_floor, capacity=capacity) for elevator_id in range(1, count + 1)
    ]


def _print_results(
    workload_size: int,
    results: list[StrategyComparisonResult],
    simulation_runtime_seconds: float,
) -> None:
    """Print comparison metrics for completed strategy runs."""
    console = Console(width=160)
    console.print(f"Simulation runtime: {simulation_runtime_seconds:.6f} seconds")
    console.print(build_summary_statistics_table(workload_size, results))
    console.print(build_performance_analysis_table(results))


def _write_state_logs(output_dir: Path, results: list[StrategyComparisonResult]) -> None:
    """Write one state log file for each completed strategy run."""
    for comparison in results:
        output_path = output_dir / f"{_safe_file_stem(comparison.strategy_name)}_log.json"
        write_state_log(comparison.result.state_log, output_path)


def _safe_file_stem(value: str) -> str:
    """Return a filesystem-safe log filename stem."""
    return re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip("-") or "strategy"


if __name__ == "__main__":
    raise SystemExit(main())
