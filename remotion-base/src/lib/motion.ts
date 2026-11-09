// Motion helpers. Everything is a pure function of the frame number.
import { Easing, interpolate, random, spring } from "remotion";

// Pick the curve by intent:
//   snap  — fast arrivals, whips, pops (most of the move happens early)
//   glide — camera moves and slow drifts (soft start and stop)
//   out   — plain decelerating entrance for secondary elements
export const EASE = {
  snap: Easing.bezier(0.16, 1, 0.3, 1),
  glide: Easing.bezier(0.45, 0, 0.55, 1),
  out: Easing.out(Easing.cubic),
  in: Easing.in(Easing.cubic),
  // a whip: slow start, fast middle, hard stop — for a camera that jumps to where a beat lands
  whip: Easing.bezier(0.76, 0, 0.24, 1),
};

export const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

/** interpolate between two frames with clamping and an easing. */
export const tween = (
  frame: number,
  [f0, f1]: [number, number],
  [v0, v1]: [number, number],
  easing: (t: number) => number = EASE.out,
) => interpolate(frame, [f0, f1], [v0, v1], { ...CLAMP, easing });

/** A landing: a spring that overshoots a little and settles. 0 → 1. */
export const land = (
  frame: number,
  fps: number,
  start: number,
  opts: { damping?: number; stiffness?: number; mass?: number } = {},
) =>
  spring({
    frame: frame - start,
    fps,
    config: {
      damping: opts.damping ?? 11,
      stiffness: opts.stiffness ?? 110,
      mass: opts.mass ?? 0.9,
    },
  });

/** A firm arrival without visible bounce. 0 → 1. */
export const settle = (frame: number, fps: number, start: number) =>
  spring({ frame: frame - start, fps, config: { damping: 200 } });

/** Slow, organic hand-held drift: sum of two sines with seeded phases. */
export const drift = (frame: number, fps: number, amp = 6, seed = "drift") => {
  const t = frame / fps;
  const p1 = random(seed + "a") * Math.PI * 2;
  const p2 = random(seed + "b") * Math.PI * 2;
  return {
    x: amp * (Math.sin(t * 0.55 + p1) * 0.7 + Math.sin(t * 1.3 + p2) * 0.3),
    y: amp * (Math.sin(t * 0.43 + p2) * 0.7 + Math.sin(t * 1.1 + p1) * 0.3),
    r: (amp / 20) * Math.sin(t * 0.37 + p1),
  };
};

// ---- Camera keys -----------------------------------------------------------
// fx/fy: the point of the composition that sits at the screen centre; z: zoom.
export type CamKey = {
  f: number;
  fx: number;
  fy: number;
  z: number;
  rot?: number;
  ease?: (t: number) => number;
};

export const cameraAt = (frame: number, keys: CamKey[]) => {
  if (frame <= keys[0].f) return keys[0];
  for (let i = 0; i < keys.length - 1; i++) {
    const a = keys[i];
    const b = keys[i + 1];
    if (frame <= b.f) {
      const p = interpolate(frame, [a.f, b.f], [0, 1], {
        ...CLAMP,
        easing: b.ease ?? EASE.glide,
      });
      return {
        f: frame,
        fx: a.fx + (b.fx - a.fx) * p,
        fy: a.fy + (b.fy - a.fy) * p,
        z: a.z * Math.pow(b.z / a.z, p), // zoom interpolates multiplicatively — feels linear to the eye
        rot: (a.rot ?? 0) + ((b.rot ?? 0) - (a.rot ?? 0)) * p,
      };
    }
  }
  return keys[keys.length - 1];
};

// ---- Operated-camera helpers -------------------------------------------------
// Pure functions of the frame number (no state, no Math.random): the same frame gives the
// same picture. <Camera> composes them; compositions can also call them directly.

/** Move every key (except the first) `frames` earlier so the camera arrives before the subject
 *  does and the subject seems to be followed. Keys stay strictly increasing, one frame apart at least. */
export const leadKeys = (keys: CamKey[], frames: number): CamKey[] => {
  const out: CamKey[] = [];
  keys.forEach((k, i) => {
    if (i === 0) return out.push({ ...k });
    const f = Math.max(out[i - 1].f + 1, k.f - Math.max(0, frames));
    out.push({ ...k, f: Math.min(f, Math.max(k.f, out[i - 1].f + 1)) });
  });
  return out;
};

/** Keys for a whip: the camera waits where it is until `whipFrames` before the landing, then
 *  jumps to `to` with EASE.whip so it is already there when the beat lands at `landFrame`. */
export const whipKeys = (
  from: CamKey,
  to: Omit<CamKey, "f" | "ease">,
  landFrame: number,
  whipFrames = 6,
): CamKey[] => {
  const start = Math.max(from.f + 1, landFrame - Math.max(1, whipFrames));
  return [
    from,
    { ...from, f: start },
    { ...to, f: Math.max(start + 1, landFrame), ease: EASE.whip },
  ];
};

/** A decaying shake after a landing. Zero before `hitFrame`; amplitude (px) falls off with
 *  `decayS` seconds; phases come from the seed. */
export const shake = (
  frame: number,
  fps: number,
  hitFrame: number,
  opts: { amp?: number; decayS?: number; freq?: number; seed?: string } = {},
) => {
  const t = (frame - hitFrame) / fps;
  if (t < 0) return { x: 0, y: 0, r: 0 };
  const amp = opts.amp ?? 10;
  const seed = opts.seed ?? "shake";
  const env = amp * Math.exp(-t / (opts.decayS ?? 0.18));
  const w = 2 * Math.PI * (opts.freq ?? 9) * t;
  const p1 = random(seed + "x") * Math.PI * 2;
  const p2 = random(seed + "y") * Math.PI * 2;
  return {
    x: env * Math.sin(w + p1),
    y: env * Math.sin(w * 1.27 + p2),
    r: (env / 40) * Math.sin(w * 0.8 + p1),
  };
};

/** 1 outside the hold ranges, 0 inside them, with a `rampS`-second ramp at each edge.
 *  Multiply the hand-held drift by it so the camera is still while the picture is read. */
export const holdFactor = (
  frame: number,
  fps: number,
  holds: [number, number][],
  rampS = 0.4,
) => {
  const ramp = Math.max(1, rampS * fps);
  let f = 1;
  for (const [a, b] of holds) {
    const into = interpolate(frame, [a - ramp, a], [0, 1], CLAMP);
    const out = interpolate(frame, [b, b + ramp], [1, 0], CLAMP);
    f = Math.min(f, 1 - Math.min(into, out));
  }
  return f;
};

/** Points of a regular grid inside [x0,x1]×[y0,y1] (composition pixels), aligned to the spacing. */
export const latticePoints = (
  b: { x0: number; y0: number; x1: number; y1: number },
  spacing: number,
) => {
  const pts: { x: number; y: number }[] = [];
  const s = Math.max(1, spacing);
  const first = (v: number) => Math.ceil(v / s) * s || 0; // `|| 0` turns -0 into 0
  for (let y = first(b.y0); y <= b.y1; y += s)
    for (let x = first(b.x0); x <= b.x1; x += s) pts.push({ x, y });
  return pts;
};
