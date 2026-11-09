/**
 * CauseEffect — something travels (the cause), touches something (the contact) and the effect
 * starts on that exact frame: the target squashes and recoils and an effect plays out from it.
 * The cause stays in the picture, so nothing is cut.
 *
 *   approach(frame, spec)     the cause's position: it accelerates into the contact, rebounds after it
 *   impactPose(frame, fps, hitAt, opts)   squash scale and recoil of the target after the hit
 *   effectProgress(frame, hitAt, durFrames)  0 → 1 from the hit, for whatever the effect draws
 *   <CauseEffect>             cause + target + an effect drawn from its progress
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { Track } from "../components/Track";

export type Point = { x: number; y: number };
export type ApproachSpec = {
  from: Point;
  /** where the cause touches the target */
  to: Point;
  start: number;
  hitAt: number;
  /** px the cause rebounds after the contact */
  rebound?: number;
};

export const approach = (frame: number, s: ApproachSpec): Point => {
  if (s.hitAt <= s.start) throw new Error("approach: hitAt must be after start");
  const u = (frame - s.start) / (s.hitAt - s.start);
  if (u <= 0) return s.from;
  if (u < 1) {
    const g = u * u; // accelerating into the hit
    return { x: s.from.x + (s.to.x - s.from.x) * g, y: s.from.y + (s.to.y - s.from.y) * g };
  }
  // after the hit: a short rebound along the same line that settles back to the contact point
  const t = Math.min(1, (frame - s.hitAt) / (s.hitAt - s.start));
  const dx = s.to.x - s.from.x;
  const dy = s.to.y - s.from.y;
  const len = Math.hypot(dx, dy) || 1;
  const back = (s.rebound ?? 40) * Math.sin(Math.PI * Math.min(1, t * 1.0)) * (1 - t);
  return { x: s.to.x - (dx / len) * back, y: s.to.y - (dy / len) * back };
};

export const impactPose = (
  frame: number,
  fps: number,
  hitAt: number,
  opts: { squash?: number; settleS?: number; recoilPx?: number } = {},
) => {
  const t = (frame - hitAt) / fps;
  if (t < 0) return { sx: 1, sy: 1, recoil: 0 };
  const settle = opts.settleS ?? 0.45;
  const env = Math.exp((-4 * t) / settle) * Math.cos(2 * Math.PI * (t / (settle / 2)));
  const q = (opts.squash ?? 0.22) * env;
  return { sx: 1 + q, sy: 1 - q, recoil: (opts.recoilPx ?? 14) * Math.max(0, env) };
};

export const effectProgress = (frame: number, hitAt: number, durFrames: number) =>
  Math.min(1, Math.max(0, (frame - hitAt) / Math.max(1, durFrames)));

export const CauseEffect: React.FC<{
  cause: React.ReactNode;
  target: React.ReactNode;
  spec: ApproachSpec;
  /** centre of the target; the effect is drawn centred on it */
  targetAt: Point;
  effectFrames?: number;
  effect?: (p: number) => React.ReactNode;
  impact?: { squash?: number; settleS?: number; recoilPx?: number };
  trackId?: string;
}> = ({ cause, target, spec, targetAt, effectFrames = 24, effect, impact, trackId }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pos = approach(f, spec);
  const pose = impactPose(f, fps, spec.hitAt, impact);
  const dir = Math.sign(spec.to.x - spec.from.x) || 1;
  const body = (
    <>
      <div
        style={{
          position: "absolute",
          left: targetAt.x + dir * pose.recoil,
          top: targetAt.y,
          transform: `translate(-50%, -50%) scale(${pose.sx}, ${pose.sy})`,
        }}
      >
        {target}
      </div>
      {effect && f >= spec.hitAt && (
        <div style={{ position: "absolute", left: targetAt.x, top: targetAt.y }}>
          {effect(effectProgress(f, spec.hitAt, effectFrames))}
        </div>
      )}
      <div
        style={{
          position: "absolute",
          left: pos.x,
          top: pos.y,
          transform: "translate(-50%, -50%)",
        }}
      >
        {cause}
      </div>
    </>
  );
  return trackId ? (
    <Track id={trackId} kind="subject">
      {body}
    </Track>
  ) : (
    body
  );
};
