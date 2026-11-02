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
