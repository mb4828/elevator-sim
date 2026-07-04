export type Direction = "idle" | "up" | "down";
export type ElevatorPhase = "moving" | "stopping" | "picking_up" | "dropping_off" | string;
export type PassengerStatus = "waiting" | "riding";

export interface PassengerDefinition {
  id: number;
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
  version?: string;
  floors: number;
  elevators: ElevatorDefinition[];
  passengers: PassengerDefinition[];
  frames: Frame[];
}

export interface Journey {
  id: number;
  requestTime: number;
  boardTime: number | null;
  completeTime: number | null;
  waitTime: number | null;
  rideTime: number | null;
  start: number;
  dest: number;
}

export type JourneyMap = Record<number, Journey>;

export interface LoadedSimulation extends OutputFile {
  journeys: JourneyMap;
}

export interface Stats {
  tick: number;
  transported: number;
  riding: number;
  waiting: number;
  peakQueue: number;
  waitSummary: string;
  rideSummary: string;
}
