/**
 * Silk — a fill of slow, flowing ribbons for a background that is alive but never competes with the
 * subject (the fluid set's "silk"). Every ribbon edge is a sum of sines whose phases advance with the
 * frame, so the field is a pure function of the frame, smooth, and loops exactly every `loopFrames`.
 *
 *   silkY(x, ribbon, frame, opts)       y of one ribbon's centre line at x (0–1 of the height)
 *   silkPath(width, height, ribbon, frame, opts)   an SVG path for the ribbon (closed down to the bottom)
 *   <Silk>                              stacked translucent ribbons in the given colours
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";

export type SilkOpts = {
  /** the frame count after which the motion repeats exactly */
  loopFrames?: number;
  /** vertical swing as a fraction of the height */
  amplitude?: number;
  /** how many waves cross the width */
  waves?: number;
};

const TAU = Math.PI * 2;

/** 0–1 height of ribbon `k` (of `n`) at horizontal position x (0–1). */
export const silkY = (x: number, k: number, n: number, frame: number, opts: SilkOpts = {}): number => {
  const loop = opts.loopFrames ?? 240;
  const amp = opts.amplitude ?? 0.08;
  const waves = opts.waves ?? 1.6;
  const t = (frame / loop) * TAU; // one full turn per loop: integer multiples below keep it periodic
  const base = (k + 1) / (n + 1);
  const a = Math.sin(TAU * waves * x + t + k * 1.7);
  const b = 0.5 * Math.sin(TAU * waves * 2.1 * x - 2 * t + k * 0.9);
  const c = 0.25 * Math.sin(TAU * waves * 0.6 * x + 3 * t + k * 2.3);
  return base + (amp * (a + b + c)) / 1.75;
};

export const silkPath = (
  width: number,
  height: number,
  k: number,
  n: number,
  frame: number,
  opts: SilkOpts = {},
  steps = 48,
): string => {
  const pts = Array.from({ length: steps + 1 }, (_, i) => {
    const x = i / steps;
    return `${(x * width).toFixed(1)},${(silkY(x, k, n, frame, opts) * height).toFixed(1)}`;
  });
  return `M0,${height} L${pts.join(" L")} L${width},${height} Z`;
};

export const Silk: React.FC<{
  colors: string[];
  opacity?: number;
  opts?: SilkOpts;
}> = ({ colors, opacity = 0.35, opts }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  return (
    <svg width={width} height={height} style={{ position: "absolute", inset: 0 }}>
      {colors.map((c, k) => (
        <path key={k} d={silkPath(width, height, k, colors.length, frame, opts)} fill={c} opacity={opacity} />
      ))}
    </svg>
  );
};
