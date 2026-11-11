/**
 * Entrances and carries — how things arrive, and how a cast gathers into one place.
 *
 *   entrancePose(frame, fps, start, kind, opts)   offset from the resting place: x, y, scale, rotation, opacity
 *   gatherPose(frame, fps, i, n, spec)            one of n elements travelling from its origin into a shared target
 *   <Gather>                                      a cast that converges on a point (a logo, a card) and is absorbed there
 *
 * Entrances: `rise` (from below, settles), `drop` (from above, lands with a squash), `slide` (from the side,
 * decelerating), `pop` (scale spring, small overshoot), `swing` (rotates in and settles). All are 0 before `start`
 * and exactly the resting pose (0 offset, scale 1) after they settle. Moving entrances (rise, drop, slide) stretch
 * along their travel while they are fast (`stretch` is the gain, 0 turns it off); a drop also squashes where it lands.
 */
import React from "react";
import { spring, useCurrentFrame, useVideoConfig } from "remotion";
import {
  EASE,
  stretchAxes,
  stretchFromVelocity,
  velocityOf,
} from "../lib/motion";
import { squash } from "./PostcardDrop";
import { Track } from "../components/Track";

export type EntranceKind = "rise" | "drop" | "slide" | "pop" | "swing";
export type EntrancePose = {
  x: number;
  y: number;
  s: number;
  r: number;
  opacity: number;
  sx: number;
  sy: number;
};

const spr = (
  frame: number,
  fps: number,
  start: number,
  damping: number,
  stiffness = 120,
) =>
  spring({
    frame: frame - start,
    fps,
    config: { damping, stiffness, mass: 0.9 },
  });

const basePose = (
  frame: number,
  fps: number,
  start: number,
  kind: EntranceKind,
  d: number,
  dir: 1 | -1,
): EntrancePose => {
  const rest: EntrancePose = {
    x: 0,
    y: 0,
    s: 1,
    r: 0,
    opacity: 1,
    sx: 1,
    sy: 1,
  };
  const o = Math.min(1, (frame - start) / (0.18 * fps)); // fades in over the first 0.18 s
  switch (kind) {
    case "rise":
      return { ...rest, y: d * (1 - spr(frame, fps, start, 14)), opacity: o };
    case "drop": {
      const p = spr(frame, fps, start, 16, 150);
      const sq = squash(frame, fps, start + Math.round(0.45 * fps), 0.07);
      return { ...rest, y: -d * (1 - p), opacity: o, sx: sq.sx, sy: sq.sy };
    }
    case "slide":
      return {
        ...rest,
        x:
          dir * d * (1 - EASE.snap(Math.min(1, (frame - start) / (0.7 * fps)))),
        opacity: o,
      };
    case "pop":
      return { ...rest, s: spr(frame, fps, start, 10, 160), opacity: o };
    case "swing":
      return {
        ...rest,
        r: dir * 14 * (1 - spr(frame, fps, start, 8, 90)),
        opacity: o,
      };
  }
};

export const entrancePose = (
  frame: number,
  fps: number,
  start: number,
  kind: EntranceKind,
  opts: { distance?: number; dir?: 1 | -1; stretch?: number } = {},
): EntrancePose => {
  if (frame < start)
    return {
      x: 0,
      y: 0,
      s: kind === "pop" ? 0 : 1,
      r: 0,
      opacity: 0,
      sx: 1,
      sy: 1,
    };
  const d = opts.distance ?? 240;
  const dir = opts.dir ?? 1;
  const pose = basePose(frame, fps, start, kind, d, dir);
  const gain = opts.stretch ?? 0.005;
  if (gain <= 0 || (kind !== "rise" && kind !== "drop" && kind !== "slide"))
    return pose;
  const v = velocityOf(
    (f) => basePose(f, fps, start, kind, d, dir),
    frame,
    0.5,
    start,
  );
  const st = stretchAxes(stretchFromVelocity(v.vx, v.vy, { gain, max: 0.3 }));
  return { ...pose, sx: pose.sx * st.sx, sy: pose.sy * st.sy };
};

export type GatherSpec = {
  /** where element i starts, and the shared target */
  origins: { x: number; y: number }[];
  target: { x: number; y: number };
  /** frame the first element leaves, frames between departures, seconds each trip takes */
  start: number;
  stagger: number;
  tripS: number;
};

/** Element i: eased flight to the target, shrinking to `endScale`; `arrived` is true from its landing frame. */
export const gatherPose = (
  frame: number,
  fps: number,
  i: number,
  spec: GatherSpec,
  endScale = 0.2,
) => {
  const from = spec.origins[i];
  const t0 = spec.start + i * spec.stagger;
  const u = Math.min(1, Math.max(0, (frame - t0) / (spec.tripS * fps)));
  const e = EASE.whip(u);
  return {
    x: from.x + (spec.target.x - from.x) * e,
    y: from.y + (spec.target.y - from.y) * e,
    s: 1 + (endScale - 1) * e,
    arrived: u >= 1,
    arrivalFrame: t0 + Math.round(spec.tripS * fps),
  };
};

export const Gather: React.FC<{
  items: React.ReactNode[];
  spec: GatherSpec;
  endScale?: number;
  trackId?: string;
}> = ({ items, spec, endScale = 0.2, trackId }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cast = (
    <>
      {items.map((node, i) => {
        const p = gatherPose(f, fps, i, spec, endScale);
        if (p.arrived) return null; // absorbed by the target
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: p.x,
              top: p.y,
              transform: `translate(-50%, -50%) scale(${p.s})`,
            }}
          >
            {node}
          </div>
        );
      })}
    </>
  );
  return trackId ? (
    <Track id={trackId} kind="subject" blurred>
      {cast}
    </Track>
  ) : (
    cast
  );
};
