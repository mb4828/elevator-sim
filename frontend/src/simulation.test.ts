import { describe, expect, it } from "vitest";
import { buildJourneys, getStats, parseSimulation } from "./simulation";
import type { OutputFile } from "./types";

function sampleOutputFile(): OutputFile {
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

describe("parseSimulation", () => {
  it("parses a valid output file and attaches derived journeys", () => {
    const parsed = parseSimulation(sampleOutputFile());

    expect(parsed.floors).toBe(4);
    expect(Object.keys(parsed.journeys)).toHaveLength(2);
  });

  it("rejects passenger metadata without a full display ID", () => {
    expect(() => parseSimulation({
      ...sampleOutputFile(),
      passengers: [{ id: 0, request_time: 0, start_floor: 0, destination_floor: 3 }],
      frames: [{ time: 0, complete: false, elevators: [], passengers: [{ id: 0, status: "waiting" }] }],
    })).toThrow("Expected a simulation file with valid passengers and frames arrays.");
  });

  it("rejects values missing the required top-level arrays", () => {
    expect(() => parseSimulation({ floors: 4 })).toThrow(
      "Expected a simulation file with valid passengers and frames arrays.",
    );
  });

  it("rejects non-object values", () => {
    expect(() => parseSimulation(null)).toThrow();
    expect(() => parseSimulation("not a simulation")).toThrow();
  });
});

describe("buildJourneys", () => {
  it("derives board/complete/wait/ride times from frame history", () => {
    const journeys = buildJourneys(sampleOutputFile());

    expect(journeys[1]).toMatchObject({
      requestTime: 0,
      fullId: "passenger1",
      boardTime: 1,
      completeTime: 2,
      waitTime: 1,
      totalTime: 2,
      start: 0,
      dest: 3,
    });
    expect(journeys[2]).toMatchObject({
      requestTime: 1,
      fullId: "passenger2",
      boardTime: 2,
      completeTime: 3,
      waitTime: 1,
      totalTime: 2,
      start: 1,
      dest: 0,
    });
  });

  it("leaves a passenger who never boards with null board/ride times", () => {
    const sim = sampleOutputFile();
    sim.passengers.push({ id: 3, full_id: "passenger3", request_time: 4, start_floor: 2, destination_floor: 1 });

    const journeys = buildJourneys(sim);

    expect(journeys[3]).toMatchObject({
      boardTime: null,
      completeTime: null,
      waitTime: null,
      totalTime: null,
    });
  });
});

describe("getStats", () => {
  it("reports mid-simulation counts and only-completed summaries", () => {
    const sim = parseSimulation(sampleOutputFile());

    const stats = getStats(sim, 2);

    expect(stats.tick).toBe(2);
    expect(stats.riding).toBe(1);
    expect(stats.waiting).toBe(1);
    expect(stats.transported).toBe(0);
    expect(stats.peakQueue).toBe(2);
    expect(stats.waitSummary).toBe("1.00/1.00/1.00");
    expect(stats.totalSummary).toBe("n/a");
  });

  it("reports final counts once every passenger has completed", () => {
    const sim = parseSimulation(sampleOutputFile());

    const stats = getStats(sim, 4);

    expect(stats.transported).toBe(2);
    expect(stats.riding).toBe(0);
    expect(stats.waiting).toBe(0);
    expect(stats.waitSummary).toBe("1.00/1.00/1.00");
    expect(stats.totalSummary).toBe("2.00/2.00/2.00");
  });
});
