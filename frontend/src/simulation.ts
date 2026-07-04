import type { JourneyMap, LoadedSimulation, OutputFile, Stats } from "./types";

export function parseSimulation(value: unknown): LoadedSimulation {
  if (!isSimulationFile(value)) {
    throw new Error("Expected top-level frames and passengers arrays.");
  }

  return {
    ...value,
    journeys: buildJourneys(value),
  };
}

export function buildJourneys(sim: OutputFile): JourneyMap {
  const journeys: JourneyMap = Object.fromEntries(
    sim.passengers.map((passenger) => [
      passenger.id,
      {
        id: passenger.id,
        requestTime: passenger.request_time,
        boardTime: null,
        completeTime: null,
        waitTime: null,
        rideTime: null,
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
        journey.boardTime = frame.time;
      }
    }
  }

  for (const journey of Object.values(journeys)) {
    if (lastSeen[journey.id] !== undefined) {
      journey.completeTime = lastSeen[journey.id] + 1;
    }
    if (journey.boardTime !== null) {
      journey.waitTime = journey.boardTime - journey.requestTime;
    }
    if (journey.completeTime !== null) {
      journey.rideTime = journey.completeTime - journey.requestTime;
    }
  }

  return journeys;
}

export function getStats(sim: LoadedSimulation, tick: number): Stats {
  const frame = sim.frames[tick];
  const activePassengers = frame.passengers ?? [];
  const waiting = activePassengers.filter((passenger) => passenger.status === "waiting").length;
  const riding = activePassengers.filter((passenger) => passenger.status === "riding").length;
  const peakQueue = sim.frames
    .slice(0, tick + 1)
    .reduce(
      (peak, currentFrame) =>
        Math.max(peak, (currentFrame.passengers ?? []).filter((passenger) => passenger.status === "waiting").length),
      0,
    );
  const journeys = Object.values(sim.journeys);
  const boardedWaits = journeys
    .filter((journey) => journey.boardTime !== null && journey.boardTime <= frame.time)
    .map((journey) => journey.waitTime)
    .filter((value): value is number => value !== null);
  const completedRides = journeys
    .filter((journey) => journey.completeTime !== null && journey.completeTime <= frame.time)
    .map((journey) => journey.rideTime)
    .filter((value): value is number => value !== null);

  return {
    tick: frame.time,
    transported: completedRides.length,
    riding,
    waiting,
    peakQueue,
    waitSummary: summarize(boardedWaits),
    rideSummary: summarize(completedRides),
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
    Array.isArray(candidate.frames)
  );
}
