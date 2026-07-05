import { describe, expect, it } from "vitest";
import { theme } from "./theme";

describe("theme", () => {
  it("builds a MUI theme with the project typography and shape", () => {
    expect(theme.typography.h6.fontWeight).toBe(700);
    expect(theme.shape.borderRadius).toBe(8);
  });
});
