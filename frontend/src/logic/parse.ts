import type {
  Direction,
  ElevatorDefinition,
  ElevatorPhase,
  Frame,
  FrameElevator,
  FramePassenger,
  LoadedSimulation,
  NormalizedOutputFile,
  OutputFile,
  PassengerDefinition,
  PassengerStatus,
} from "./types";
import { buildJourneys } from "./journeys";
import { buildPeakQueueByTick } from "./stats";

/**
 * Validates an unknown value (typically freshly parsed JSON) as a simulation
 * output file, normalizes it, and attaches the derived journey and queue data
 * the UI needs. This is the single entry point for loading a simulation.
 */
export function parseSimulation(value: unknown): LoadedSimulation {
  if (!isSimulationFile(value)) {
    throw new Error("Expected a simulation file with valid passengers and frames arrays.");
  }

  const sim = normalize(value);

  return {
    ...sim,
    journeys: buildJourneys(sim),
    peakQueueByTick: buildPeakQueueByTick(sim),
  };
}

/**
 * Guarantees every frame carries a passengers array so downstream code never
 * has to re-check the optional field.
 */
function normalize(file: OutputFile): NormalizedOutputFile {
  return {
    ...file,
    frames: file.frames.map((frame) => ({ ...frame, passengers: frame.passengers ?? [] })),
  };
}

// ---------------------------------------------------------------------------
// Validation guards
// ---------------------------------------------------------------------------

const DIRECTIONS: readonly Direction[] = ["idle", "up", "down"];
const ELEVATOR_PHASES: readonly ElevatorPhase[] = ["idle", "moving", "stopping", "loading", "unloading"];
const PASSENGER_STATUSES: readonly PassengerStatus[] = ["waiting", "riding"];

function isSimulationFile(value: unknown): value is OutputFile {
  if (!isRecord(value)) return false;
  const candidate = value as Partial<OutputFile>;

  return (
    typeof candidate.floors === "number" &&
    Array.isArray(candidate.elevators) &&
    candidate.elevators.every(isElevatorDefinition) &&
    Array.isArray(candidate.passengers) &&
    candidate.passengers.every(isPassengerDefinition) &&
    Array.isArray(candidate.frames) &&
    candidate.frames.every(isFrame)
  );
}

function isPassengerDefinition(value: unknown): value is PassengerDefinition {
  if (!isRecord(value)) return false;
  const passenger = value as Partial<PassengerDefinition>;

  return (
    typeof passenger.id === "number" &&
    typeof passenger.full_id === "string" &&
    passenger.full_id.length > 0 &&
    typeof passenger.request_time === "number" &&
    typeof passenger.start_floor === "number" &&
    typeof passenger.destination_floor === "number"
  );
}

function isElevatorDefinition(value: unknown): value is ElevatorDefinition {
  if (!isRecord(value)) return false;
  const elevator = value as Partial<ElevatorDefinition>;

  return typeof elevator.id === "number" && typeof elevator.capacity === "number";
}

function isFrame(value: unknown): value is Frame {
  if (!isRecord(value)) return false;
  const frame = value as Partial<Frame>;

  return (
    typeof frame.time === "number" &&
    typeof frame.complete === "boolean" &&
    Array.isArray(frame.elevators) &&
    frame.elevators.every(isFrameElevator) &&
    (frame.passengers === undefined ||
      (Array.isArray(frame.passengers) && frame.passengers.every(isFramePassenger)))
  );
}

function isFrameElevator(value: unknown): value is FrameElevator {
  if (!isRecord(value)) return false;
  const elevator = value as Partial<FrameElevator>;

  return (
    typeof elevator.id === "number" &&
    typeof elevator.floor === "number" &&
    DIRECTIONS.includes(elevator.direction as Direction) &&
    ELEVATOR_PHASES.includes(elevator.phase as ElevatorPhase) &&
    typeof elevator.passenger_count === "number" &&
    (elevator.target_floor === null || typeof elevator.target_floor === "number")
  );
}

function isFramePassenger(value: unknown): value is FramePassenger {
  if (!isRecord(value)) return false;
  const passenger = value as Partial<FramePassenger>;

  return (
    typeof passenger.id === "number" &&
    PASSENGER_STATUSES.includes(passenger.status as PassengerStatus) &&
    (passenger.elevator_id === undefined ||
      passenger.elevator_id === null ||
      typeof passenger.elevator_id === "number")
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object";
}
