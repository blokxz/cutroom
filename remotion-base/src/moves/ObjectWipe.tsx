/**
 * ObjectWipe — something in the scene crosses the lens (a towel, a branch, a door frame, a hand)
 * and uncovers the next place as it leaves.
 *
 *   wipeBar(p, extent, thickness)        { lead, trail, revealed } along the crossing axis
 *   barRect(dir, lead, thickness, w, h)  the object's box for a direction
 *   revealInset(dir, revealed, w, h)     CSS inset() that shows the part the object has passed
 *   <ObjectWipe>                         previous scene, next scene clipped behind the object, object
 *
 * Progress p: 0 = object fully off-frame before the crossing, 1 = fully off-frame after it.
 */
import React from "react";
import { Track } from "../components/Track";

export type WipeDir = "right" | "left" | "down" | "up";

export const wipeBar = (p: number, extent: number, thickness: number) => {
  const q = Math.max(0, Math.min(1, p));
  const lead = q * (extent + thickness);
  const trail = lead - thickness;
  return {
    lead,
    trail,
    revealed: Math.max(0, Math.min(extent, trail)),
  };
};

/** The object's box: `lead` is its leading edge measured from the side it enters. */
export const barRect = (
  dir: WipeDir,
  lead: number,
  thickness: number,
  w: number,
  h: number,
) => {
  switch (dir) {
    case "right":
      return { left: lead - thickness, top: 0, width: thickness, height: h };
    case "left":
      return { left: w - lead, top: 0, width: thickness, height: h };
    case "down":
      return { left: 0, top: lead - thickness, width: w, height: thickness };
    case "up":
      return { left: 0, top: h - lead, width: w, height: thickness };
  }
};

/** CSS clip-path inset() that keeps only the revealed part of the next scene. */
export const revealInset = (
  dir: WipeDir,
  revealed: number,
  w: number,
  h: number,
) => {
  switch (dir) {
    case "right":
      return `inset(0px ${w - revealed}px 0px 0px)`;
    case "left":
      return `inset(0px 0px 0px ${w - revealed}px)`;
    case "down":
      return `inset(0px 0px ${h - revealed}px 0px)`;
    case "up":
      return `inset(${h - revealed}px 0px 0px 0px)`;
  }
};

export const ObjectWipe: React.FC<{
  p: number;
  dir?: WipeDir;
  size: { w: number; h: number };
  thickness?: number;
  /** the scene being covered */
  from: React.ReactNode;
  /** the scene uncovered behind the object */
  to: React.ReactNode;
  /** the crossing object; by default a plain bar of `color` */
  object?: React.ReactNode;
  color?: string;
  trackId?: string;
}> = ({
  p,
  dir = "right",
  size,
  thickness = 360,
  from,
  to,
  object,
  color = "#F4EFE6",
  trackId,
}) => {
  const horizontal = dir === "right" || dir === "left";
  const extent = horizontal ? size.w : size.h;
  const bar = wipeBar(p, extent, thickness);
  const rect = barRect(dir, bar.lead, thickness, size.w, size.h);
  const body = (
    <div style={{ position: "absolute", ...rect, overflow: "hidden" }}>
      {object ?? <div style={{ width: "100%", height: "100%", background: color }} />}
    </div>
  );
  return (
    <>
      <div style={{ position: "absolute", inset: 0 }}>{from}</div>
      <div
        style={{
          position: "absolute",
          inset: 0,
          clipPath: revealInset(dir, bar.revealed, size.w, size.h),
        }}
      >
        {to}
      </div>
      {trackId ? (
        <Track id={trackId} kind="shape">
          {body}
        </Track>
      ) : (
        body
      )}
    </>
  );
};
