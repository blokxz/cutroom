/**
 * Steam — soft puffs of vapour that rise and sway. At rest it is a faint veil; around a scene change it
 * thickens until it covers the frame, and the next photo appears as it thins: the change happens through
 * the steam (for hot springs, the steam is the place's own survivor).
 *
 *   steamPuffs(n, seed, area)      seeded puffs: start point, radius, rise speed, sway
 *   puffAt(puff, frame, fps, area) where a puff is at a frame (it wraps to the bottom when it leaves the top)
 *   veilDensity(frame, changes, o) 0–1: the base veil, swelling to `peak` around each change frame
 *   <Steam>                        the puffs, as radial gradients, at a density
 */
import React from "react";
import { random, useCurrentFrame, useVideoConfig } from "remotion";
import { Track } from "../components/Track";

export type Puff = {
  x: number;
  y: number;
  r: number;
  rise: number;
  sway: number;
  phase: number;
};
export type Area = { w: number; h: number };

export const steamPuffs = (n: number, seed: string, area: Area): Puff[] =>
  Array.from({ length: n }, (_, i) => ({
    x: random(`${seed}x${i}`) * area.w,
    y: random(`${seed}y${i}`) * area.h,
    r: area.w * (0.28 + 0.34 * random(`${seed}r${i}`)),
    rise: 40 + 70 * random(`${seed}v${i}`), // px per second
    sway: 20 + 50 * random(`${seed}s${i}`),
    phase: random(`${seed}p${i}`) * Math.PI * 2,
  }));

/** Position of a puff: rising, swaying, wrapping from the top back to below the frame. */
export const puffAt = (p: Puff, frame: number, fps: number, area: Area) => {
  const t = frame / fps;
  const span = area.h + 2 * p.r;
  const y = ((((p.y - p.rise * t + p.r) % span) + span) % span) - p.r;
  const x = p.x + p.sway * Math.sin(t * 0.9 + p.phase);
  return { x, y, r: p.r };
};

/** Density of the veil: `base` everywhere, a smooth swell to `peak` from `before` frames before a change to `after` after it. */
export const veilDensity = (
  frame: number,
  changes: number[],
  o: { base?: number; peak?: number; before?: number; after?: number } = {},
): number => {
  const base = o.base ?? 0.12;
  const peak = o.peak ?? 0.92;
  const before = o.before ?? 12;
  const after = o.after ?? 22;
  let d = base;
  for (const c of changes) {
    if (frame < c - before || frame > c + after) continue;
    const u =
      frame <= c ? (frame - (c - before)) / before : 1 - (frame - c) / after;
    const s = Math.sin((Math.PI / 2) * Math.max(0, Math.min(1, u)));
    d = Math.max(d, base + (peak - base) * s * s);
  }
  return d;
};

export const Steam: React.FC<{
  density: number;
  count?: number;
  seed?: string;
  color?: string;
  /** tracks one lead puff that crosses the frame from bottom to top over `leadFrames`, so the verifier can follow the steam */
  trackId?: string;
  leadFrames?: number;
}> = ({
  density,
  count = 16,
  seed = "steam",
  color = "255,255,255",
  trackId,
  leadFrames = 450,
}) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const area = { w: width, h: height };
  const puffs = steamPuffs(count, seed, area);
  const layer = (
    <div style={{ position: "absolute", inset: 0, pointerEvents: "none" }}>
      {puffs.map((p, i) => {
        const at = puffAt(p, frame, fps, area);
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: at.x - at.r,
              top: at.y - at.r,
              width: at.r * 2,
              height: at.r * 2,
              borderRadius: "50%",
              background: `radial-gradient(circle, rgba(${color},${(0.85 * density).toFixed(3)}) 0%, rgba(${color},${(0.45 * density).toFixed(3)}) 38%, rgba(${color},0) 70%)`,
            }}
          />
        );
      })}
      {/* a flat wash so the peak really covers the frame */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: `rgba(${color},${(Math.max(0, density - 0.45) * 1.2).toFixed(3)})`,
        }}
      />
    </div>
  );
  if (!trackId) return layer;
  const r = width * 0.42;
  const y = height + r - ((height + 2 * r) * frame) / leadFrames;
  const x = width * 0.5 + width * 0.12 * Math.sin(frame / fps);
  return (
    <>
      {layer}
      <Track id={trackId} kind="subject">
        <div
          style={{
            position: "absolute",
            left: x - r,
            top: y - r,
            width: r * 2,
            height: r * 2,
            borderRadius: "50%",
            background: `radial-gradient(circle, rgba(${color},${(0.55 * Math.max(density, 0.35)).toFixed(3)}) 0%, rgba(${color},0) 70%)`,
          }}
        />
      </Track>
    </>
  );
};
