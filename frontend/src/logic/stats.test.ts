import { describe, expect, it } from "vitest";
import { parseSimulation } from "./parse";
import { buildPeakQueueByTick, getStats } from "./stats";
import { sampleOutputFile } from "./testFixtures";

describe("buildPeakQueueByTick", () => {
  it("tracks the running maximum of waiting passengers", () => {
    expect(buildPeakQueueByTick(sampleOutputFile())).toEqual([1, 2, 2, 2, 2]);
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
    expect(stats.waitSummary).toEqual({ min: 1, avg: 1, max: 1 });
    expect(stats.totalSummary).toBeNull();
  });

  it("reports final counts once every passenger has completed", () => {
    const sim = parseSimulation(sampleOutputFile());

    const stats = getStats(sim, 4);

    expect(stats.transported).toBe(2);
    expect(stats.riding).toBe(0);
    expect(stats.waiting).toBe(0);
    expect(stats.waitSummary).toEqual({ min: 1, avg: 1, max: 1 });
    expect(stats.totalSummary).toEqual({ min: 2, avg: 2, max: 2 });
  });

  it("throws for a tick with no recorded frame", () => {
    const sim = parseSimulation(sampleOutputFile());

    expect(() => getStats(sim, 99)).toThrow("No frame recorded for tick 99.");
  });
});
