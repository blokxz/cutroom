/**
 * Motion blur for everything that moves fast.
 *
 * Two engines from @remotion/motion-blur:
 * - "camera" (default): <CameraMotionBlur>, layered copies. Works in every Chromium.
 * - "canvas": <HtmlInCanvasMotionBlur> captures the children at fractional frames and averages the
 *   snapshots — a real shutter, without the colour/opacity shifts layered blending can cause.
 *   Needs Chromium 149+ with HTML-in-canvas (Remotion's own headless shell; an older or
 *   repackaged Chromium fails with "No cached paint record"). Compare both on your machine with
 *   `node scripts/blur-ab.mjs <CompositionId> <frame>...` before switching.
 *
 * The render script picks the engine and the sample count through input props
 * (`blurEngine`, `blurSamples`): drafts use few samples, finals many. A composition only says
 * which children are blurred and, optionally, a shutter angle.
 */
import React from "react";
import {
  CameraMotionBlur,
  HtmlInCanvasMotionBlur,
} from "@remotion/motion-blur";
import {
  AbsoluteFill,
  getInputProps,
  getRemotionEnvironment,
  useVideoConfig,
} from "remotion";

export type BlurEngine = "canvas" | "camera";

type BlurProps = {
  blurEngine?: BlurEngine;
  blurSamples?: number;
  /** set by render.mjs when it averages whole-frame passes (tools/shutter.py): no in-DOM blur on top */
  shutterPasses?: number;
};

const inputs = (): BlurProps => {
  try {
    return getInputProps() as BlurProps;
  } catch {
    return {};
  }
};

/** The engine and samples the current render asked for (exported for tests and the demo). */
export const blurSettings = (
  env: { isRendering: boolean },
  props: BlurProps,
  fallbackSamples: number,
): { engine: BlurEngine; samples: number } => {
  const engine: BlurEngine =
    props.blurEngine === "canvas" && env.isRendering ? "canvas" : "camera";
  const requested = props.blurSamples ?? fallbackSamples;
  const samples = Math.max(1, Math.min(64, Math.round(requested)));
  return { engine, samples };
};

/** Samples that keep copies at most `gapPx` apart for something travelling `travelPx` per frame.
 *  0 means the move is too small to blur (the children render untouched). */
export const samplesFor = (travelPx: number, gapPx = 24, minSamples = 2) => {
  if (!(travelPx > 1)) return 0;
  return Math.max(minSamples, Math.ceil(travelPx / Math.max(1, gapPx)) + 1);
};

/** The sample count to use: the render's request, lowered (never raised) by the declared travel. */
export const samplesWithTravel = (
  requested: number,
  travelPx?: number,
  gapPx = 24,
): number => {
  if (travelPx === undefined) return requested;
  const need = samplesFor(travelPx, gapPx);
  return need === 0 ? 0 : Math.min(requested, need);
};

export const MotionBlur: React.FC<{
  children: React.ReactNode;
  /** exposure: 180 = half a frame (film look); 0 disables the blur */
  shutterAngle?: number;
  /** samples when the render doesn't specify them */
  samples?: number;
  /** the farthest anything inside travels per frame, in px (camera included). When given, slow
   *  stretches get fewer samples and a move under 1 px renders without blur. */
  travel?: number;
  /** max distance between blur copies, px (with `travel`) */
  gap?: number;
}> = ({ children, shutterAngle = 180, samples = 6, travel, gap = 24 }) => {
  const { width, height } = useVideoConfig();
  const { engine, samples: requested } = blurSettings(
    getRemotionEnvironment(),
    inputs(),
    samples,
  );
  const n = samplesWithTravel(requested, travel, gap);
  if (n === 0 || (inputs().shutterPasses ?? 1) > 1) return <>{children}</>;
  if (engine === "canvas") {
    return (
      <HtmlInCanvasMotionBlur
        width={width}
        height={height}
        shutterAngle={shutterAngle}
        samples={n}
      >
        <AbsoluteFill>{children}</AbsoluteFill>
      </HtmlInCanvasMotionBlur>
    );
  }
  return (
    <CameraMotionBlur shutterAngle={shutterAngle} samples={n}>
      {children}
    </CameraMotionBlur>
  );
};
