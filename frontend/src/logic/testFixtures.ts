import type { NormalizedOutputFile } from "./types";

/**
 * A small but complete simulation: passenger 1 boards at tick 1 and completes
 * at tick 2; passenger 2 boards at tick 2 and completes at tick 3.
 */
export function sampleOutputFile(): NormalizedOutputFile {
  return {
    floors: 4,
    elevators: [{ id: 1, capacity: 4 }],
    passengers: [
      { id: 1, full_id: "passenger1", request_time: 0, start_floor: 0, destination_floor: 3 },
      { id: 2, full_id: "passenger2", request_time: 1, start_floor: 1, destination_floor: 0 },
    ],
    frames: [
      { time: 0, complete: false, elevators: [], passengers: [{ id: 1, status: "waiting", elevator_id: null }] },
      {
        time: 1,
        complete: false,
        elevators: [],
        passengers: [
          { id: 1, status: "waiting", elevator_id: null },
          { id: 2, status: "waiting", elevator_id: null },
        ],
      },
      {
        time: 2,
        complete: false,
        elevators: [],
        passengers: [
          { id: 1, status: "riding", elevator_id: 1 },
          { id: 2, status: "waiting", elevator_id: null },
        ],
      },
      { time: 3, complete: false, elevators: [], passengers: [{ id: 2, status: "riding", elevator_id: 1 }] },
      { time: 4, complete: true, elevators: [], passengers: [] },
    ],
  };
}
