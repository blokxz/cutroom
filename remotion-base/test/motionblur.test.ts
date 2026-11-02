import { describe, expect, it } from "vitest";
import { blurSettings } from "../src/components/MotionBlur";

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
