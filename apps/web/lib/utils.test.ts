import { describe, expect, it } from "vitest";

import { cn, formatDate, scoreTone, titleCase } from "./utils";

describe("cn", () => {
  it("merges conflicting tailwind classes (last wins)", () => {
    expect(cn("p-2", "p-4")).toBe("p-4");
  });

  it("handles conditional classes", () => {
    expect(cn("a", false && "b", "c")).toBe("a c");
  });
});

describe("scoreTone", () => {
  it("maps score ranges to tones", () => {
    expect(scoreTone(90)).toBe("good");
    expect(scoreTone(75)).toBe("good");
    expect(scoreTone(60)).toBe("medium");
    expect(scoreTone(49)).toBe("poor");
    expect(scoreTone(0)).toBe("poor");
  });
});

describe("titleCase", () => {
  it("converts snake_case to Title Case", () => {
    expect(titleCase("nice_to_have")).toBe("Nice To Have");
    expect(titleCase("system_design")).toBe("System Design");
  });
});

describe("formatDate", () => {
  it("returns an em dash for missing or invalid dates", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate("not-a-date")).toBe("—");
  });

  it("formats ISO dates", () => {
    expect(formatDate("2025-06-15T12:00:00Z")).toMatch(/2025/);
  });
});
