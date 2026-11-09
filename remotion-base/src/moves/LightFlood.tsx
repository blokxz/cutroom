/**
 * LightFlood — the ground itself is the punctuation. A field of warm light rises from below the
 * frame and floods it, then drains in rings that open the next scene: the flood stays outside the
 * leading ring, bands between rings alternate two tints, and the next scene shows inside the last.
 *
 *   floodAt(frame, fps, spec)        { level, drain, phase } — rise, hold, drain
 *   ringRadii(drain, n, rMax, gap)   radii of n rings leaving one point (index 0 = leading, largest)
 *   <LightFlood>                     draws the field while it rises and the rings while it drains
 *
 * Timing is in seconds; the caller passes the frame the flood starts on. Draw the previous scene
 * under it and give the next scene as `children`.
 */
import React from "react";
import { interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { CLAMP, EASE } from "../lib/motion";
import { Track } from "../components/Track";

export type FloodSpec = {
  /** frame the flood starts rising */
  at: number;
  /** seconds to flood the frame (keep it short) */
  riseS?: number;
  /** seconds fully flooded before the rings leave */
  holdS?: number;
  /** seconds for the rings to drain off the frame */
  drainS?: number;
};

export type FloodState = {
  level: number;
  drain: number;
  phase: "idle" | "rise" | "hold" | "drain" | "done";
};

export const floodAt = (
  frame: number,
  fps: number,
  spec: FloodSpec,
): FloodState => {
  const rise = (spec.riseS ?? 0.4) * fps;
  const hold = (spec.holdS ?? 0.15) * fps;
  const drain = (spec.drainS ?? 1) * fps;
  const t = frame - spec.at;
  if (t < 0) return { level: 0, drain: 0, phase: "idle" };
  if (t < rise)
    return { level: EASE.snap(t / rise), drain: 0, phase: "rise" };
  if (t < rise + hold) return { level: 1, drain: 0, phase: "hold" };
  if (t < rise + hold + drain)
    return {
      level: 1,
      drain: EASE.glide((t - rise - hold) / drain),
      phase: "drain",
    };
  return { level: 1, drain: 1, phase: "done" };
};

/** Radii of `n` rings that leave one point `gap` (0–0.5 of the drain) apart. Ring 0 leaves first
 *  and ends up largest; `rMax` is where the leading ring ends (≥ the frame's far corner). */
export const ringRadii = (drain: number, n: number, rMax: number, gap = 0.12) => {
  const span = Math.max(0.2, 1 - (n - 1) * gap);
  return Array.from({ length: n }, (_, i) => {
    const p = interpolate((drain - i * gap) / span, [0, 1], [0, 1], CLAMP);
    return rMax * EASE.out(p);
  });
};

const maskOutside = (cx: number, cy: number, r: number) => {
  const m = `radial-gradient(circle at ${cx}px ${cy}px, transparent ${r}px, #000 ${r + 1}px)`;
  return { WebkitMaskImage: m, maskImage: m } as React.CSSProperties;
};

export const LightFlood: React.FC<{
  spec: FloodSpec;
  /** where the rings leave from (composition pixels) */
  center: { x: number; y: number };
  glow?: string;
  /** the second tint of the alternating bands */
  tint?: string;
  rings?: number;
  /** the next scene, shown inside the last ring */
  children?: React.ReactNode;
  trackId?: string;
}> = ({
  spec,
  center,
  glow = "#F2B160",
  tint = "#F7DFA4",
  rings = 3,
  children,
  trackId,
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const s = floodAt(frame, fps, spec);
  if (s.phase === "idle") return null;
  const far = Math.hypot(
    Math.max(center.x, width - center.x),
    Math.max(center.y, height - center.y),
  );
  const field =
    s.drain === 0 ? (
      <div
        style={{
          position: "absolute",
          inset: 0,
          opacity: Math.min(1, s.level * 1.4),
          background: `radial-gradient(ellipse ${60 + 90 * s.level}% ${40 + 80 * s.level}% at 50% ${112 - 30 * s.level}%, ${glow} ${45 + 40 * s.level}%, transparent 100%)`,
        }}
      />
    ) : (
      <>
        <div style={{ position: "absolute", inset: 0 }}>{children}</div>
        {ringRadii(s.drain, rings, far * 1.02)
          .map((r, i) => (
            <div
              key={i}
              style={{
                position: "absolute",
                inset: 0,
                background: i % 2 ? tint : glow,
                ...maskOutside(center.x, center.y, r),
              }}
            />
          ))
          .reverse()}
      </>
    );
  return trackId ? (
    <Track id={trackId} kind="shape">
      {field}
    </Track>
  ) : (
    field
  );
};
