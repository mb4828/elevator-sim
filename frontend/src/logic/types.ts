// ---------------------------------------------------------------------------
// Raw simulation file format
//
// These types mirror the JSON emitted by the backend simulator. Field names
// are snake_case to match the file on disk.
// ---------------------------------------------------------------------------

export type Direction = "idle" | "up" | "down";
export type ElevatorPhase = "idle" | "moving" | "stopping" | "loading" | "unloading";
export type PassengerStatus = "waiting" | "riding";

export interface PassengerDefinition {
  id: number;
  full_id: string;
  request_time: number;
  start_floor: number;
  destination_floor: number;
}

export interface ElevatorDefinition {
  id: number;
  capacity: number;
}

export interface FrameElevator {
  id: number;
  floor: number;
  direction: Direction;
  phase: ElevatorPhase;
  passenger_count: number;
  target_floor: number | null;
}

export interface FramePassenger {
  id: number;
  status: PassengerStatus;
  elevator_id?: number | null;
}

export interface Frame {
  time: number;
  complete: boolean;
  elevators: FrameElevator[];
  passengers?: FramePassenger[];
}

export interface OutputFile {
  version?: number;
  floors: number;
  elevators: ElevatorDefinition[];
  passengers: PassengerDefinition[];
  frames: Frame[];
}

// ---------------------------------------------------------------------------
// Normalized and derived shapes
//
// parseSimulation normalizes the raw file (every frame is guaranteed a
// passengers array) and attaches data derived from the frame history.
// ---------------------------------------------------------------------------

/** A frame whose optional fields have been filled in during parsing. */
export interface LoadedFrame extends Frame {
  passengers: FramePassenger[];
}

/** An OutputFile whose frames have all been normalized to LoadedFrame. */
export interface NormalizedOutputFile extends OutputFile {
  frames: LoadedFrame[];
}

export interface Journey {
  id: number;
  fullId: string;
  requestTime: number;
  boardTime: number | null;
  completeTime: number | null;
  waitTime: number | null;
  totalTime: number | null;
  start: number;
  dest: number;
}

export type JourneyMap = Record<number, Journey>;

export interface LoadedSimulation extends NormalizedOutputFile {
  journeys: JourneyMap;
  /** Running maximum of waiting passengers, indexed by tick. */
  peakQueueByTick: number[];
}

/** Min/average/max of a set of durations, in ticks. Formatting is up to the UI. */
export interface StatSummary {
  min: number;
  avg: number;
  max: number;
}

export interface Stats {
  tick: number;
  transported: number;
  riding: number;
  waiting: number;
  peakQueue: number;
  /** Wait durations of passengers who have visibly boarded, or null if none yet. */
  waitSummary: StatSummary | null;
  /** Total journey durations of delivered passengers, or null if none yet. */
  totalSummary: StatSummary | null;
}
