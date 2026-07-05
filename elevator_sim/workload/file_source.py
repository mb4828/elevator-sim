"""CSV-backed passenger workload source."""

import csv
import re
from pathlib import Path

from elevator_sim.core.models import Passenger
from elevator_sim.workload.base import PassengerSource

REQUIRED_COLUMNS = ("time", "id", "source", "dest")


class FileSource(PassengerSource):
    """Load scheduled passenger requests from a CSV file."""

    def __init__(self, input_file: Path) -> None:
        passengers = self._load_passengers(input_file)
        duration = self._calculate_duration(passengers)
        super().__init__(passengers, duration)

    def _load_passengers(self, input_file: Path) -> tuple[Passenger, ...]:
        """Parse passenger requests from a CSV file."""
        with input_file.open(newline="", encoding="utf-8") as file_obj:
            reader = csv.DictReader(file_obj)
            self._validate_header(reader.fieldnames, input_file)
            return tuple(self._passenger_from_row(row, row_number) for row_number, row in enumerate(reader, start=2))

    def _validate_header(self, fieldnames: list[str] | None, input_file: Path) -> None:
        """Validate the CSV header contains the expected schema."""
        if fieldnames is None:
            raise ValueError(f"{input_file} is empty")
        if tuple(fieldnames) != REQUIRED_COLUMNS:
            expected = ",".join(REQUIRED_COLUMNS)
            actual = ",".join(fieldnames)
            raise ValueError(f"{input_file} must use header {expected}; got {actual}")

    def _passenger_from_row(self, row: dict[str, str], row_number: int) -> Passenger:
        """Convert one CSV row into a Passenger."""
        try:
            return Passenger(
                id=self._parse_passenger_id(row["id"]),
                request_time=self._parse_int(row["time"], "time", row_number),
                start_floor=self._parse_int(row["source"], "source", row_number),
                destination_floor=self._parse_int(row["dest"], "dest", row_number),
            )
        except ValueError as error:
            raise ValueError(f"invalid passenger row {row_number}: {error}") from error

    def _parse_passenger_id(self, value: str) -> int:
        """Parse a positive integer passenger ID, including labels with trailing digits."""
        stripped = value.strip()
        if stripped.isdigit():
            return int(stripped)
        match = re.search(r"(\d+)$", stripped)
        if match:
            return int(match.group(1))
        raise ValueError("id must be a positive integer or end with digits")

    def _parse_int(self, value: str, field: str, row_number: int) -> int:
        """Parse one integer CSV field."""
        try:
            return int(value.strip())
        except ValueError as error:
            raise ValueError(f"{field} must be an integer on row {row_number}") from error

    def _calculate_duration(self, passengers: tuple[Passenger, ...]) -> int:
        """Return the first tick after the final scheduled request."""
        if not passengers:
            return 0
        return max(passenger.request_time for passenger in passengers) + 1
