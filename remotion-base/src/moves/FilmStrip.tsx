/**
 * FilmStrip — a strip of frames rolls through the lens, stops on a frame, and that frame grows
 * until it fills the screen (a morph, not a cut). The strip is the survivor.
 *
 *   stripOffset(frame, fps, stops, spacing, moveS)  distance the strip has rolled at `frame`
 *   cellRect(p, from, to)                           a rectangle between two rectangles (the growing frame)
 *   <FilmStrip>                                     frames with sprocket holes, rolling, then one grows
 *
 * `stops` lists, in time order, the frame each roll starts and the cell index it ends on.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { EASE } from "../lib/motion";
import { Track } from "../components/Track";

export type StripStop = { at: number; index: number };
export type Rect = { x: number; y: number; w: number; h: number };

const ease = EASE.glide;

/** Rolled distance: each stop eases from the previous resting cell to its own over `moveS`. */
export const stripOffset = (
  frame: number,
  fps: number,
  stops: StripStop[],
  spacing: number,
  moveS = 0.9,
): number => {
  let prev = 0;
  for (const s of stops) {
    const to = s.index * spacing;
    const u = Math.min(1, Math.max(0, (frame - s.at) / (moveS * fps)));
    if (frame < s.at) return prev;
    if (u < 1) return prev + (to - prev) * ease(u);
    prev = to;
  }
  return prev;
};

/** Linear blend of two rectangles with an easing already applied to `p`. */
export const cellRect = (p: number, from: Rect, to: Rect): Rect => {
  const q = Math.min(1, Math.max(0, p));
  const m = (a: number, b: number) => a + (b - a) * q;
  return {
    x: m(from.x, to.x),
    y: m(from.y, to.y),
    w: m(from.w, to.w),
    h: m(from.h, to.h),
  };
};

export const FilmStrip: React.FC<{
  frames: React.ReactNode[];
  /** size of one frame and the gap between frames (px) */
  cell: { w: number; h: number };
  gap?: number;
  /** y of the strip centre; the strip rolls along x with cell 0 centred at `x0` */
  y: number;
  x0: number;
  stops: StripStop[];
  moveS?: number;
  /** the frame (index) that grows to `fill` from `growAt` for `growS` seconds */
  grow?: { index: number; at: number; growS?: number; fill: Rect };
  stripColor?: string;
  /** easing of the growing frame (default: a glide) */
  growEase?: (t: number) => number;
  trackId?: string;
  /** mark the strip as blurred for the verifier: put the strip inside <MotionBlur> when it moves fast */
  blurred?: boolean;
}> = ({
  frames,
  cell,
  gap = 36,
  y,
  x0,
  stops,
  moveS,
  grow,
  stripColor = "#161616",
  growEase = EASE.glide,
  trackId,
  blurred,
}) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const spacing = cell.w + gap;
  const rolled = stripOffset(f, fps, stops, spacing, moveS);
  const pad = 44;
  const strip = (
    <>
      <div
        style={{
          position: "absolute",
          left: x0 - cell.w / 2 - rolled - spacing * 2,
          top: y - cell.h / 2 - pad,
          width: spacing * (frames.length + 4),
          height: cell.h + pad * 2,
          background: stripColor,
        }}
      >
        {Array.from({ length: (frames.length + 4) * 4 }, (_, i) => (
          <React.Fragment key={i}>
            {[8, cell.h + pad * 2 - 24].map((top) => (
              <div
                key={top}
                style={{
                  position: "absolute",
                  left: 12 + i * (spacing / 4),
                  top,
                  width: 22,
                  height: 16,
                  borderRadius: 4,
                  background: "#F2EFE8",
                }}
              />
            ))}
          </React.Fragment>
        ))}
      </div>
      {frames.map((node, i) => {
        const at = x0 - rolled + i * spacing;
        const growing = grow && grow.index === i;
        const p = growing
          ? Math.min(
              1,
              Math.max(0, (f - grow.at) / ((grow.growS ?? 0.8) * fps)),
            )
          : 0;
        const r = growing
          ? cellRect(
              growEase(p),
              { x: at - cell.w / 2, y: y - cell.h / 2, w: cell.w, h: cell.h },
              grow.fill,
            )
          : { x: at - cell.w / 2, y: y - cell.h / 2, w: cell.w, h: cell.h };
        return (
          <div
            key={i}
            style={{
              position: "absolute",
              left: r.x,
              top: r.y,
              width: r.w,
              height: r.h,
              overflow: "hidden",
              borderRadius: growing ? 12 * (1 - p) : 12,
              zIndex: growing && p > 0 ? 2 : 1,
            }}
          >
            {node}
          </div>
        );
      })}
    </>
  );
  return trackId ? (
    <Track id={trackId} kind="shape" blurred={blurred}>
      {strip}
    </Track>
  ) : (
    strip
  );
};
