import type { LoadedSimulation, NormalizedOutputFile, StatSummary, Stats } from "./types";

/**
 * Precomputes the running maximum of simultaneously waiting passengers,
 * indexed by tick, so scrubbing the timeline never rescans earlier frames.
 */
export function buildPeakQueueByTick(sim: NormalizedOutputFile): number[] {
  const peaks: number[] = [];
  let peak = 0;

  for (const frame of sim.frames) {
    let waiting = 0;
    for (const passenger of frame.passengers) {
      if (passenger.status === "waiting") waiting += 1;
    }
    peak = Math.max(peak, waiting);
    peaks.push(peak);
  }

  return peaks;
}

/** Computes the live stats shown for a single tick of the timeline. */
export function getStats(sim: LoadedSimulation, tick: number): Stats {
  const frame = sim.frames[tick];
  if (!frame) {
    throw new Error(`No frame recorded for tick ${tick}.`);
  }

  let waiting = 0;
  let riding = 0;
  for (const passenger of frame.passengers) {
    if (passenger.status === "waiting") waiting += 1;
    else if (passenger.status === "riding") riding += 1;
  }

  // The strict `<` comparisons make events count only once they are visible
  // on screen: a board tick of N means the passenger first appears riding in
  // frame N+1, and a complete tick of N means frame N is the last one the
  // passenger appears in, so they count as transported from frame N+1 on.
  const boardedWaits: number[] = [];
  const completedTotals: number[] = [];
  for (const journey of Object.values(sim.journeys)) {
    if (journey.boardTime !== null && journey.boardTime < frame.time && journey.waitTime !== null) {
      boardedWaits.push(journey.waitTime);
    }
    if (journey.completeTime !== null && journey.completeTime < frame.time && journey.totalTime !== null) {
      completedTotals.push(journey.totalTime);
    }
  }

  return {
    tick: frame.time,
    transported: completedTotals.length,
    riding,
    waiting,
    peakQueue: sim.peakQueueByTick[tick] ?? 0,
    waitSummary: summarize(boardedWaits),
    totalSummary: summarize(completedTotals),
  };
}

function summarize(values: number[]): StatSummary | null {
  if (values.length === 0) return null;

  let min = Number.POSITIVE_INFINITY;
  let max = Number.NEGATIVE_INFINITY;
  let sum = 0;
  for (const value of values) {
    min = Math.min(min, value);
    max = Math.max(max, value);
    sum += value;
  }

  return { min, avg: sum / values.length, max };
}
