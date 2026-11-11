/**
 * Bounce — a body dropped onto a floor: it falls, stretches along its travel, squashes on each contact
 * (harder the faster it hits), loses height with every bounce and rolls to rest.
 *
 *   bounceAt(frame, fps, spec)   position, velocity (px/frame) and the last contact of the body at `frame`
 *   bounceContacts(fps, spec)    the frames where it touches the floor
 *   <Bouncer>                    draws its children at that position, stretched and squashed, with a floor shadow
 *
 * The flight is ballistic between contacts (gravity `g`, px/s²); each contact keeps `restitution` of the
 * vertical speed; the horizontal speed bleeds off with `friction` (1/s). Everything is closed-form, so any
 * frame (fractional ones too, for the shutter) is computed directly, without stepping.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import {
  NO_STRETCH,
  Stretch,
  contactSquash,
  stretchFromVelocity,
  stretchTransform,
} from "../lib/motion";
import { Track } from "../components/Track";

export type BounceSpec = {
  /** frame the body is let go */
  start: number;
  /** where it is let go (centre), and the y of its centre when it touches the floor */
  x0: number;
  y0: number;
  floor: number;
  /** horizontal speed at release, px/s */
  vx?: number;
  g?: number;
  restitution?: number;
  friction?: number;
  /** below this vertical speed (px/s) it stops bouncing and rolls */
  restSpeed?: number;
};

const D = {
  vx: 520,
  g: 5200,
  restitution: 0.55,
  friction: 1.4,
  restSpeed: 260,
};

/** Contact times (s after release) and the vertical speed (px/s) of each impact. */
const impacts = (spec: BounceSpec) => {
  const g = spec.g ?? D.g;
  const e = spec.restitution ?? D.restitution;
  const rest = spec.restSpeed ?? D.restSpeed;
  const v1 = Math.sqrt(2 * g * Math.max(0, spec.floor - spec.y0));
  const out: { t: number; v: number }[] = [];
  let t = v1 / g;
  let v = v1;
  while (v > rest && out.length < 12) {
    out.push({ t, v });
    v *= e;
    t += (2 * v) / g;
  }
  if (v1 > 0 && out.length === 0) out.push({ t, v: v1 });
  return { out, g, v1 };
};

export const bounceContacts = (fps: number, spec: BounceSpec) =>
  impacts(spec).out.map((c) => spec.start + c.t * fps);

export const bounceAt = (frame: number, fps: number, spec: BounceSpec) => {
  const { out, g } = impacts(spec);
  const e = spec.restitution ?? D.restitution;
  const vx0 = spec.vx ?? D.vx;
  const lam = spec.friction ?? D.friction;
  const t = Math.max(0, (frame - spec.start) / fps);
  const x =
    spec.x0 + (lam > 0 ? (vx0 * (1 - Math.exp(-lam * t))) / lam : vx0 * t);
  const vxs = vx0 * Math.exp(-lam * t);
  let y: number;
  let vys: number;
  let last: { t: number; v: number } | null = null;
  if (out.length === 0 || t <= out[0].t) {
    y = spec.y0 + 0.5 * g * t * t;
    vys = g * t;
  } else {
    let i = 0;
    while (i + 1 < out.length && t >= out[i + 1].t) i++;
    last = out[i];
    const up = last.v * e; // leaves the floor with this speed
    const tau = t - last.t;
    const flight = i + 1 < out.length ? out[i + 1].t - last.t : (2 * up) / g;
    if (tau <= flight) {
      y = spec.floor - (up * tau - 0.5 * g * tau * tau);
      vys = -(up - g * tau);
    } else {
      y = spec.floor; // at rest on the floor, still rolling
      vys = 0;
    }
  }
  return {
    x,
    y: Math.min(y, spec.floor),
    vx: frame < spec.start ? 0 : vxs / fps, // held still until it is let go
    vy: frame < spec.start ? 0 : vys / fps,
    lastContact: last ? spec.start + last.t * fps : null,
    impact: last ? last.v / impacts(spec).v1 : 0,
  };
};

/** The body's deformation at `frame`: stretch along travel in the air, squash after each contact. */
export const bounceShape = (
  frame: number,
  fps: number,
  spec: BounceSpec,
  opts: { gain?: number; max?: number; squash?: number } = {},
): { stretch: Stretch; squash: Stretch } => {
  const b = bounceAt(frame, fps, spec);
  let stretch = stretchFromVelocity(b.vx, b.vy, {
    gain: opts.gain ?? 0.006,
    max: opts.max ?? 0.32,
  });
  let squash: Stretch = NO_STRETCH;
  if (b.lastContact !== null) {
    squash = contactSquash(frame, fps, b.lastContact, {
      amount: (opts.squash ?? 0.3) * b.impact,
    });
    // right after a contact the squash owns the shape; the stretch comes back as the body climbs
    const k = 1 - Math.exp(-(frame - b.lastContact) / (0.07 * fps));
    stretch = {
      ...stretch,
      along: 1 + (stretch.along - 1) * k,
      across: 1 / (1 + (stretch.along - 1) * k),
    };
  }
  return { stretch, squash };
};

export const Bouncer: React.FC<{
  spec: BounceSpec;
  size: number;
  /** draw a soft shadow on the floor that tightens as the body comes down */
  shadow?: string;
  trackId?: string;
  children: React.ReactNode;
}> = ({ spec, size, shadow, trackId, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const b = bounceAt(frame, fps, spec);
  const { stretch, squash } = bounceShape(frame, fps, spec);
  // a squash about the centre would lift the body off the floor: keep its foot down
  const foot = b.y >= spec.floor - 0.5 ? ((1 - squash.along) * size) / 2 : 0;
  const h = Math.max(0, spec.floor - b.y);
  const body = (
    <div
      style={{
        position: "absolute",
        left: b.x - size / 2,
        top: b.y - size / 2 + foot,
        width: size,
        height: size,
        transform:
          `${stretchTransform(stretch)} ${stretchTransform(squash)}`.trim() ||
          undefined,
      }}
    >
      {children}
    </div>
  );
  return (
    <>
      {shadow ? (
        <div
          style={{
            position: "absolute",
            left: b.x - size * 0.6,
            top: spec.floor + size / 2 - size * 0.08,
            width: size * 1.2,
            height: size * 0.16,
            borderRadius: "50%",
            background: shadow,
            filter: `blur(${6 + h / 30}px)`,
            opacity: Math.max(0.15, 0.7 - h / 1400),
            transform: `scaleX(${1 / (1 + h / 1600)})`,
          }}
        />
      ) : null}
      {trackId ? (
        <Track id={trackId} kind="subject">
          {body}
        </Track>
      ) : (
        body
      )}
    </>
  );
};
