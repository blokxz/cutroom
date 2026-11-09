/**
 * Belt — places on one continuous belt that starts smoothly, runs at a constant speed and slows
 * to settle exactly on an item. Nothing cuts; the belt is the survivor.
 *
 *   beltPose(frame, fps, spec)   { x, speed, tau } — distance travelled, px/frame, 0–1 clock
 *   <Belt>                       lays the items along the belt and moves them with the pose
 *
 * The speed profile is a trapezoid (ramp up, cruise, brake), so the position is exact at the end:
 * set `distance` to `index * spacing` to land on item `index`. `tau` is a clock that slows with the
 * belt — drive an item's own loop (a flicker, a pulse) from it so the item settles with the belt.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { Track } from "../components/Track";

export type BeltSpec = {
  /** frame the belt starts */
  at: number;
  /** total seconds from start to full stop */
  durS: number;
  /** px travelled by the end */
  distance: number;
  /** seconds to reach cruise speed */
  rampS?: number;
  /** seconds to brake from cruise to stop */
  brakeS?: number;
};

export type BeltPose = { x: number; speed: number; tau: number };

export const beltPose = (
  frame: number,
  fps: number,
  spec: BeltSpec,
): BeltPose => {
  const T = spec.durS;
  const D = spec.distance;
  const a = Math.max(1e-6, spec.rampS ?? 0.6);
  const b = Math.max(1e-6, spec.brakeS ?? 0.9);
  if (T <= (a + b) / 2 || a + b > T) {
    throw new Error("beltPose: durS must exceed (rampS + brakeS) and be ≥ their sum");
  }
  const v = D / (T - (a + b) / 2); // px per second at cruise
  const t = Math.min(Math.max((frame - spec.at) / fps, 0), T);
  let x: number;
  let sp: number;
  if (t < a) {
    x = (v * t * t) / (2 * a);
    sp = (v * t) / a;
  } else if (t <= T - b) {
    x = (v * a) / 2 + v * (t - a);
    sp = v;
  } else {
    const u = T - t;
    x = D - (v * u * u) / (2 * b);
    sp = (v * u) / b;
  }
  return { x, speed: sp / fps, tau: D === 0 ? 1 : x / D };
};

export const Belt: React.FC<{
  spec: BeltSpec;
  items: React.ReactNode[];
  /** distance between item centres along the belt (px) */
  spacing: number;
  /** where item 0 sits at rest, and the fixed cross-axis position */
  origin: { x: number; y: number };
  /** the belt runs along x (default) or y */
  axis?: "x" | "y";
  trackId?: string;
}> = ({ spec, items, spacing, origin, axis = "x", trackId }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const p = beltPose(frame, fps, spec);
  const belt = (
    <>
      {items.map((it, i) => {
        const along = i * spacing - p.x;
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: origin.x + (axis === "x" ? along : 0),
              top: origin.y + (axis === "y" ? along : 0),
              transform: "translate(-50%, -50%)",
            }}
          >
            {it}
          </div>
        );
      })}
    </>
  );
  return trackId ? (
    <Track id={trackId} kind="shape">
      {belt}
    </Track>
  ) : (
    belt
  );
};
