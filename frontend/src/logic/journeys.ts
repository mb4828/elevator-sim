import type { JourneyMap, LoadedFrame, NormalizedOutputFile, PassengerDefinition } from "./types";

/**
 * Reconstructs each passenger's journey (request → board → complete) from the
 * frame-by-frame history in three passes: seed a journey per passenger from
 * the roster, observe board and last-seen ticks in the frames, then derive
 * the wait and total durations.
 */
export function buildJourneys(sim: NormalizedOutputFile): JourneyMap {
  const journeys = initJourneys(sim.passengers);
  const lastSeenTick = recordBoardAndLastSeenTicks(sim.frames, journeys);
  deriveDurations(journeys, lastSeenTick);
  return journeys;
}

function initJourneys(passengers: PassengerDefinition[]): JourneyMap {
  return Object.fromEntries(
    passengers.map((passenger) => [
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
}

/**
 * Scans the frames once, setting each journey's boardTime and returning the
 * last tick each passenger was observed in.
 */
function recordBoardAndLastSeenTicks(frames: LoadedFrame[], journeys: JourneyMap): Record<number, number> {
  const lastSeenTick: Record<number, number> = {};

  for (const frame of frames) {
    for (const passenger of frame.passengers) {
      const journey = journeys[passenger.id];
      if (!journey) continue;

      lastSeenTick[passenger.id] = frame.time;
      if (passenger.status === "riding" && journey.boardTime === null) {
        // A passenger is first reported as "riding" in the frame *after* the
        // boarding happened, so the actual board tick is the previous frame.
        journey.boardTime = frame.time - 1;
      }
    }
  }

  return lastSeenTick;
}

function deriveDurations(journeys: JourneyMap, lastSeenTick: Record<number, number>): void {
  for (const journey of Object.values(journeys)) {
    const lastTick = lastSeenTick[journey.id];
    if (lastTick !== undefined) {
      // Passengers disappear from the frames once delivered, so the last
      // frame a passenger appears in is the tick their journey completed.
      journey.completeTime = lastTick;
    }
    if (journey.boardTime !== null) {
      journey.waitTime = journey.boardTime - journey.requestTime;
    }
    if (journey.completeTime !== null) {
      journey.totalTime = journey.completeTime - journey.requestTime;
    }
  }
}
