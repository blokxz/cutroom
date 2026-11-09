/**
 * Calendar — a desk calendar whose pages tear off one by one; each torn page reveals the place
 * under it. The last page is never torn (a blank "your dates" page with the contact).
 *
 *   tearPose(frame, fps, start, opts)   pose of a page torn off at `start`: lifts on its hinge, falls, fades
 *   <Calendar>                          the block: a stack of pages, torn in order, final page stays
 *
 * Pages are listed top first. `tearAt` is the frame each page starts to tear; the page under it is
 * already in place, so it is revealed as the torn page falls away.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { EASE } from "../lib/motion";
import { Track } from "../components/Track";

export type TearPose = {
  x: number;
  y: number;
  /** degrees, around the top-left hinge */
  r: number;
  opacity: number;
  gone: boolean;
};

/** Before `start` the page is in place; it lifts on its hinge for `liftS`, then falls and fades. */
export const tearPose = (
  frame: number,
  fps: number,
  start: number,
  opts: { liftS?: number; fallS?: number; drop?: number; spin?: number } = {},
): TearPose => {
  const t = (frame - start) / fps;
  if (t <= 0) return { x: 0, y: 0, r: 0, opacity: 1, gone: false };
  const lift = opts.liftS ?? 0.18;
  const fall = opts.fallS ?? 0.7;
  if (t < lift) {
    const u = EASE.out(t / lift);
    return { x: 0, y: -10 * u, r: -16 * u, opacity: 1, gone: false };
  }
  const u = Math.min(1, (t - lift) / fall);
  const g = u * u; // gravity: distance grows with the square of the time
  return {
    x: 60 * u,
    y: -10 + (opts.drop ?? 1500) * g,
    r: -16 + (opts.spin ?? 28) * u,
    opacity: Math.max(0, 1 - Math.max(0, (u - 0.55) / 0.45)),
    gone: u >= 1,
  };
};

export type CalendarPage = {
  /** frame the page starts to tear; omit on the final page */
  tearAt?: number;
  content: React.ReactNode;
};

export const Calendar: React.FC<{
  box: { x: number; y: number; w: number; h: number };
  pages: CalendarPage[];
  paper?: string;
  header?: string;
  headerH?: number;
  trackId?: string;
}> = ({
  box,
  pages,
  paper = "#FBF7EF",
  header = "#C65D4A",
  headerH = 96,
  trackId,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const body = (
    <div style={{ position: "absolute", left: box.x, top: box.y, width: box.w, height: box.h }}>
      {pages
        .map((pg, i) => {
          const pose =
            pg.tearAt === undefined
              ? { x: 0, y: 0, r: 0, opacity: 1, gone: false }
              : tearPose(frame, fps, pg.tearAt);
          if (pose.gone) return null;
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                inset: 0,
                transformOrigin: "0 0",
                transform: `translate(${pose.x}px, ${pose.y}px) rotate(${pose.r}deg)`,
                opacity: pose.opacity,
                background: paper,
                borderRadius: 14,
                overflow: "hidden",
                boxShadow: "0 18px 40px rgba(0,0,0,0.18)",
              }}
            >
              <div style={{ height: headerH, background: header }} />
              <div style={{ position: "absolute", top: headerH, left: 0, right: 0, bottom: 0 }}>
                {pg.content}
              </div>
            </div>
          );
        })
        .reverse()}
    </div>
  );
  return trackId ? (
    <Track id={trackId} kind="shape">
      {body}
    </Track>
  ) : (
    body
  );
};

/** The first page that is still in place at `frame` (or the last one). */
export const pageInPlace = (
  frame: number,
  fps: number,
  pages: CalendarPage[],
) => {
  const i = pages.findIndex(
    (p) => p.tearAt === undefined || !tearPose(frame, fps, p.tearAt).gone,
  );
  return i < 0 ? pages.length - 1 : i;
};

