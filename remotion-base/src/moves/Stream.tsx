/**
 * Stream — a meandering stream seen from above: a centre line that wanders, a ribbon that widens into pools and
 * narrows over riffles, banks with grass and wet stone, a darker deep channel, flow highlights that travel
 * downstream, and pebbles. It reveals along the path as the camera walks it.
 *
 *   streamCenter(y, opts)            x of the stream's centre line at height y (two sines, so no two bends match)
 *   streamWidthAt(y, base)           ribbon width: pools and riffles along the course
 *   streamPoints(y0, y1, step, opts) the centre line sampled from y0 to y1
 *   ribbonSides(points, widthAt)     left and right edges of a ribbon around a polyline
 *   <StreamRibbon>                   the drawn stream up to arc length `s` of the path model
 */
import React from "react";
import { random, useCurrentFrame } from "remotion";
import type { PathModel } from "./PathCamera";

export type StreamOpts = {
  cx?: number;
  amp?: number;
  wavelength?: number;
  phase?: number;
};
export type XY = { x: number; y: number };

const TAU = Math.PI * 2;

export const streamCenter = (y: number, o: StreamOpts = {}): number => {
  const cx = o.cx ?? 540;
  const amp = o.amp ?? 300;
  const wl = o.wavelength ?? 1150;
  const ph = o.phase ?? 0;
  return (
    cx +
    (amp *
      (Math.sin((TAU * y) / wl + ph) +
        0.45 * Math.sin((TAU * y) / (wl * 0.43) + ph * 2.3 + 1.1))) /
      1.45
  );
};

export const streamWidthAt = (y: number, base = 190): number =>
  base *
  (1 +
    0.28 * Math.sin((TAU * y) / 870 + 0.6) +
    0.12 * Math.sin((TAU * y) / 310));

export const streamPoints = (
  y0: number,
  y1: number,
  step: number,
  o: StreamOpts = {},
): XY[] => {
  const n = Math.max(1, Math.ceil((y1 - y0) / step));
  return Array.from({ length: n + 1 }, (_, i) => {
    const y = y0 + ((y1 - y0) * i) / n;
    return { x: streamCenter(y, o), y };
  });
};

/** Left and right edges of a ribbon of width `widthAt(point)` centred on the polyline. */
export const ribbonSides = (points: XY[], widthAt: (p: XY) => number) => {
  const left: XY[] = [];
  const right: XY[] = [];
  points.forEach((p, i) => {
    const a = points[Math.max(0, i - 1)];
    const b = points[Math.min(points.length - 1, i + 1)];
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const len = Math.hypot(dx, dy) || 1;
    const nx = -dy / len;
    const ny = dx / len;
    const h = widthAt(p) / 2;
    left.push({ x: p.x + nx * h, y: p.y + ny * h });
    right.push({ x: p.x - nx * h, y: p.y - ny * h });
  });
  return { left, right };
};

const poly = (pts: XY[]) =>
  pts.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
const line = (pts: XY[]) => `M${poly(pts).replace(/ /g, " L")}`;

/** The model's points up to arc length s, ending exactly at s. */
const upTo = (path: PathModel, s: number): { pts: XY[]; cum: number[] } => {
  const pts: XY[] = [];
  const cum: number[] = [];
  for (let i = 0; i < path.points.length && path.cum[i] <= s; i++) {
    pts.push(path.points[i]);
    cum.push(path.cum[i]);
  }
  const e = path.at(Math.min(s, path.length));
  const last = pts[pts.length - 1];
  if (!last || last.x !== e.x || last.y !== e.y) {
    pts.push({ x: e.x, y: e.y });
    cum.push(Math.min(s, path.length));
  }
  return { pts, cum };
};

/** 0 → 1 over `len` px: the stream's head is a tapered tip, not a flat cut. */
export const headTaper = (distFromHead: number, len = 260): number => {
  const t = Math.min(1, Math.max(0, distFromHead / len));
  return t * t * (3 - 2 * t);
};

export const StreamRibbon: React.FC<{
  path: PathModel;
  /** arc length drawn so far */
  s: number;
  width?: number;
  /** water, deep channel, wet bank, grass, highlight */
  colors?: {
    water: string;
    deep: string;
    bank: string;
    grass: string;
    light: string;
    stone: string[];
  };
  seed?: string;
  /** what drives the glints' drift (px); default: the frame. Drive it with the camera so the water is still when the shot rests */
  flow?: number;
  /** draw only the part of the course between these two heights (plus a margin): the cut is off-screen, the work stays small */
  window?: [number, number];
  /** taper the tip of a stream that is still being revealed (default: only when `s` is shorter than the course) */
  taper?: boolean;
}> = ({
  path,
  s,
  width = 190,
  colors = {
    water: "#86A3AC",
    deep: "#5E7E89",
    bank: "#6E705F",
    grass: "#C9D2BE",
    light: "#EAF3F4",
    stone: ["#8A8A7E", "#665A4E", "#A39C90"],
  },
  seed = "stream",
  flow,
  window,
  taper,
}) => {
  const frame = useCurrentFrame();
  const drift = flow ?? frame * 6;
  const full = upTo(path, s);
  let lo = 0;
  let hi = full.pts.length;
  if (window) {
    const inside = full.pts
      .map((p, i) => (p.y >= window[0] && p.y <= window[1] ? i : -1))
      .filter((i) => i >= 0);
    if (inside.length < 2) return null;
    lo = Math.max(0, inside[0] - 1);
    hi = Math.min(full.pts.length, inside[inside.length - 1] + 2);
  }
  const pts = full.pts.slice(lo, hi);
  const cum = full.cum.slice(lo, hi);
  if (pts.length < 2) return null;
  const tip = taper ?? s < path.length - 1;
  const head = cum[cum.length - 1];
  const idx = new Map(pts.map((p, i) => [p, i]));
  const w = (k: number) => (p: XY) =>
    streamWidthAt(p.y, width) *
    k *
    (tip ? 0.04 + 0.96 * headTaper(head - cum[idx.get(p) ?? 0]) : 1);
  const ribbon = (k: number) => {
    const { left, right } = ribbonSides(pts, w(k));
    return poly([...left, ...right.reverse()]);
  };
  const pad = width * 2.4;
  const xs = pts.map((p) => p.x);
  const ys = pts.map((p) => p.y);
  const x0 = Math.min(...xs) - pad;
  const y0 = Math.min(...ys) - pad;
  const bw = Math.max(...xs) + pad - x0;
  const bh = Math.max(...ys) + pad - y0;
  // highlights slide downstream at different speeds and sit at different distances from the centre
  // glints: short, thin and irregular, at different distances from the centre, each lane slower or faster
  const lanes = [
    { off: 0.0, dash: "14 90 5 160 22 240", speed: 6, w: 2.6, o: 0.7 },
    { off: 0.22, dash: "9 120 20 210 6 150", speed: 4, w: 2, o: 0.55 },
    { off: -0.24, dash: "18 180 7 100 12 260", speed: 8, w: 2.2, o: 0.5 },
    { off: 0.34, dash: "6 140 10 300", speed: 3, w: 1.6, o: 0.4 },
    { off: -0.36, dash: "12 200 5 170", speed: 5, w: 1.6, o: 0.4 },
  ];
  const lane = (off: number) => {
    const { left, right } = ribbonSides(
      pts,
      (p) => streamWidthAt(p.y, width) * Math.abs(off) * 2,
    );
    return off >= 0 ? left : right;
  };
  const stones = Array.from(
    { length: Math.floor(path.length / 55) },
    (_, i) => {
      const at = path.at(Math.min(s, i * 55 + random(`${seed}a${i}`) * 40));
      if (i * 55 > s) return null;
      const side = random(`${seed}s${i}`) > 0.5 ? 1 : -1;
      const d =
        streamWidthAt(at.y, width) * (0.55 + 0.4 * random(`${seed}d${i}`));
      return {
        x: at.x + side * d,
        y: at.y + (random(`${seed}y${i}`) - 0.5) * 50,
        r: 5 + 13 * random(`${seed}r${i}`),
        c: colors.stone[
          Math.floor(random(`${seed}c${i}`) * colors.stone.length)
        ],
      };
    },
  );
  return (
    <svg
      style={{ position: "absolute", left: x0, top: y0, overflow: "visible" }}
      width={bw}
      height={bh}
      viewBox={`${x0} ${y0} ${bw} ${bh}`}
    >
      <defs>
        <filter id="soft24" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="26" />
        </filter>
        <filter id="soft6" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="7" />
        </filter>
        <filter id="edge" x="-20%" y="-20%" width="140%" height="140%">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.012"
            numOctaves="2"
            seed="3"
            result="n"
          />
          <feDisplacementMap in="SourceGraphic" in2="n" scale="26" />
        </filter>
      </defs>
      <polygon
        points={ribbon(3.4)}
        fill={colors.grass}
        opacity={0.6}
        filter="url(#soft24)"
      />
      <polygon
        points={ribbon(1.38)}
        fill={colors.bank}
        opacity={0.92}
        filter="url(#edge)"
      />
      <polygon points={ribbon(1)} fill={colors.water} filter="url(#edge)" />
      <polygon
        points={ribbon(0.52)}
        fill={colors.deep}
        opacity={0.85}
        filter="url(#soft6)"
      />
      {stones.map((st, i) =>
        st ? (
          <ellipse
            key={i}
            cx={st.x}
            cy={st.y}
            rx={st.r * 1.25}
            ry={st.r}
            fill={st.c}
            opacity={0.9}
          />
        ) : null,
      )}
      {lanes.map((l, i) => (
        <path
          key={i}
          d={line(l.off === 0 ? pts : lane(l.off))}
          fill="none"
          stroke={colors.light}
          strokeWidth={l.w}
          strokeLinecap="round"
          strokeDasharray={l.dash}
          strokeDashoffset={(-drift * l.speed) / 6}
          opacity={l.o}
        />
      ))}
    </svg>
  );
};
