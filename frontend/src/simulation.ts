import type { JourneyMap, LoadedSimulation, OutputFile, Stats } from "./types";

export function parseSimulation(value: unknown): LoadedSimulation {
  if (!isSimulationFile(value)) {
    throw new Error("Expected a simulation file with valid passengers and frames arrays.");
  }

  return {
    ...value,
    journeys: buildJourneys(value),
    peakQueueByTick: buildPeakQueueByTick(value),
  };
}

export function buildJourneys(sim: OutputFile): JourneyMap {
  const journeys: JourneyMap = Object.fromEntries(
    sim.passengers.map((passenger) => [
      passenger.id,
      {
        id: passenger.id,
        fullId: passenger.full_id,
        requestTime: passenger.request_time,
        boardTime: null,
        completeTime: null,
        waitTime: null,
        totalTime: null,
        start: passenger.start_floor,
        dest: passenger.destination_floor,
      },
    ]),
  );
  const lastSeen: Record<number, number> = {};

  for (const frame of sim.frames) {
    for (const passenger of frame.passengers ?? []) {
      const journey = journeys[passenger.id];
      if (!journey) continue;

      lastSeen[passenger.id] = frame.time;
      if (passenger.status === "riding" && journey.boardTime === null) {
        journey.boardTime = frame.time - 1;
      }
    }
  }

  for (const journey of Object.values(journeys)) {
    const lastSeenTime = lastSeen[journey.id];
    if (lastSeenTime !== undefined) {
      journey.completeTime = lastSeenTime;
    }
    if (journey.boardTime !== null) {
      journey.waitTime = journey.boardTime - journey.requestTime;
    }
    if (journey.completeTime !== null) {
      journey.totalTime = journey.completeTime - journey.requestTime;
    }
  }

  return journeys;
}

export function buildPeakQueueByTick(sim: OutputFile): number[] {
  const peaks: number[] = [];
  let peak = 0;

  for (const frame of sim.frames) {
    const waiting = (frame.passengers ?? []).filter((passenger) => passenger.status === "waiting").length;
    peak = Math.max(peak, waiting);
    peaks.push(peak);
  }

  return peaks;
}

export function getStats(sim: LoadedSimulation, tick: number): Stats {
  const frame = sim.frames[tick];
  if (!frame) {
    throw new Error(`No frame recorded for tick ${tick}.`);
  }
  const activePassengers = frame.passengers ?? [];
  const waiting = activePassengers.filter((passenger) => passenger.status === "waiting").length;
  const riding = activePassengers.filter((passenger) => passenger.status === "riding").length;
  const peakQueue = sim.peakQueueByTick[tick] ?? 0;
  const journeys = Object.values(sim.journeys);
  const boardedWaits = journeys
    .filter((journey) => journey.boardTime !== null && journey.boardTime < frame.time)
    .map((journey) => journey.waitTime)
    .filter((value): value is number => value !== null);
  const completedTotals = journeys
    .filter((journey) => journey.completeTime !== null && journey.completeTime < frame.time)
    .map((journey) => journey.totalTime)
    .filter((value): value is number => value !== null);

  return {
    tick: frame.time,
    transported: completedTotals.length,
    riding,
    waiting,
    peakQueue,
    waitSummary: summarize(boardedWaits),
    totalSummary: summarize(completedTotals),
  };
}

function summarize(values: number[]): string {
  if (values.length === 0) return "n/a";
  const min = Math.min(...values);
  const max = Math.max(...values);
  const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
  return `${formatStat(min)}/${formatStat(avg)}/${formatStat(max)}`;
}

function formatStat(value: number): string {
  return value.toFixed(2);
}

function isSimulationFile(value: unknown): value is OutputFile {
  if (!value || typeof value !== "object") return false;
  const candidate = value as Partial<OutputFile>;

  return (
    typeof candidate.floors === "number" &&
    Array.isArray(candidate.elevators) &&
    Array.isArray(candidate.passengers) &&
    candidate.passengers.every(isPassengerDefinition) &&
    Array.isArray(candidate.frames)
  );
}

function isPassengerDefinition(value: unknown): value is OutputFile["passengers"][number] {
  if (!value || typeof value !== "object") return false;
  const passenger = value as Partial<OutputFile["passengers"][number]>;

  return (
    typeof passenger.id === "number" &&
    typeof passenger.full_id === "string" &&
    passenger.full_id.length > 0 &&
    typeof passenger.request_time === "number" &&
    typeof passenger.start_floor === "number" &&
    typeof passenger.destination_floor === "number"
  );
}
