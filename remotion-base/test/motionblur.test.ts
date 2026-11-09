import { describe, expect, it } from "vitest";
import {
  blurSettings,
  samplesFor,
  samplesWithTravel,
} from "../src/components/MotionBlur";

describe("blurSettings", () => {
  it("defaults to the camera engine and the composition's samples", () => {
    expect(blurSettings({ isRendering: true }, {}, 6)).toEqual({
      engine: "camera",
      samples: 6,
    });
  });
  it("uses the canvas engine only when asked and only while rendering", () => {
    expect(
      blurSettings({ isRendering: true }, { blurEngine: "canvas" }, 6).engine,
    ).toBe("canvas");
    expect(
      blurSettings({ isRendering: false }, { blurEngine: "canvas" }, 6).engine,
    ).toBe("camera");
  });
  it("takes the render's sample count and clamps it to 1-64", () => {
    expect(
      blurSettings({ isRendering: true }, { blurSamples: 12 }, 6).samples,
    ).toBe(12);
    expect(
      blurSettings({ isRendering: true }, { blurSamples: 500 }, 6).samples,
    ).toBe(64);
    expect(
      blurSettings({ isRendering: true }, { blurSamples: 0 }, 6).samples,
    ).toBe(1);
  });
});

describe("samples sized by travel", () => {
  it("is zero for a move under 1 px and grows with the travel", () => {
    expect(samplesFor(0)).toBe(0);
    expect(samplesFor(0.5)).toBe(0);
    expect(samplesFor(30)).toBeGreaterThan(samplesFor(10));
    expect(samplesFor(5)).toBe(2); // the minimum
  });
  it("keeps copies at most `gap` px apart", () => {
    for (const travel of [24, 60, 200, 935]) {
      const n = samplesFor(travel, 24);
      expect(travel / (n - 1)).toBeLessThanOrEqual(24);
    }
  });
  it("never exceeds what the render asked for, and ignores travel when unset", () => {
    expect(samplesWithTravel(12, undefined)).toBe(12);
    expect(samplesWithTravel(12, 935)).toBe(12);
    expect(samplesWithTravel(3, 935)).toBe(3);
    expect(samplesWithTravel(12, 40)).toBeLessThan(12);
    expect(samplesWithTravel(12, 0)).toBe(0);
  });
});
