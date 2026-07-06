import { describe, expect, it } from "vitest";
import { buildJourneys } from "./journeys";
import { sampleOutputFile } from "./testFixtures";

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
