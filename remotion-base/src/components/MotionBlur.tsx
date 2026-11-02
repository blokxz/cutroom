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

type BlurProps = { blurEngine?: BlurEngine; blurSamples?: number };

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

export const MotionBlur: React.FC<{
  children: React.ReactNode;
  /** exposure: 180 = half a frame (film look); 0 disables the blur */
  shutterAngle?: number;
  /** samples when the render doesn't specify them */
  samples?: number;
}> = ({ children, shutterAngle = 180, samples = 6 }) => {
  const { width, height } = useVideoConfig();
  const { engine, samples: n } = blurSettings(
    getRemotionEnvironment(),
    inputs(),
    samples,
  );
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
