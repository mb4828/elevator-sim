import { describe, expect, it } from "vitest";
import { parseSimulation } from "./parse";
import { sampleOutputFile } from "./testFixtures";

describe("parseSimulation", () => {
  it("parses a valid output file and attaches derived journeys", () => {
    const parsed = parseSimulation(sampleOutputFile());

    expect(parsed.floors).toBe(4);
    expect(Object.keys(parsed.journeys)).toHaveLength(2);
  });

  it("normalizes frames so every frame has a passengers array", () => {
    const raw = sampleOutputFile();
    delete (raw.frames[4] as { passengers?: unknown }).passengers;

    const parsed = parseSimulation(raw);

    expect(parsed.frames[4]?.passengers).toEqual([]);
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

  it("rejects frames with malformed passenger entries", () => {
    expect(() => parseSimulation({
      ...sampleOutputFile(),
      frames: [{ time: 0, complete: false, elevators: [], passengers: [{ id: 1, status: "flying" }] }],
    })).toThrow("Expected a simulation file with valid passengers and frames arrays.");
  });

  it("rejects non-object values", () => {
    expect(() => parseSimulation(null)).toThrow();
    expect(() => parseSimulation("not a simulation")).toThrow();
  });
});
