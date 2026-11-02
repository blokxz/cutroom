/**
 * PathCamera — a camera that travels along a drawn path across a world of
 * placed photos, with the trail drawing itself behind it.
 *
 * The path math is done here in TypeScript (not with the DOM's getPointAtLength)
 * so every frame is deterministic and testable:
 *   buildPath(d)                 parse an SVG path (M L H V C Q Z, absolute and relative)
 *                                and return { length, at(s), d }: point + tangent angle at arc length s
 *   nearestLength(path, pt)      arc length of the path point closest to pt (to time stops at photos)
 *   pathFrame(path, s, zoom, screen)   the world transform that puts the point at s on `screen`
 *   <PathCamera>                 renders the world under that transform
 *   <PathTrail>                  the path drawn up to s, solid or as dots
 */
import React from "react";

type Pt = { x: number; y: number };
type Seg =
  | { k: "L"; a: Pt; b: Pt }
  | { k: "Q"; a: Pt; c: Pt; b: Pt }
  | { k: "C"; a: Pt; c1: Pt; c2: Pt; b: Pt };

/** Parse a path string into line / quadratic / cubic segments (absolute coordinates). */
export const parsePath = (d: string): Seg[] => {
  const tokens =
    d.match(/[MLHVCQZmlhvcqz]|-?(?:\d+\.?\d*|\.\d+)(?:e[-+]?\d+)?/g) ?? [];
  const segs: Seg[] = [];
  let i = 0;
  let cmd = "";
  let cur: Pt = { x: 0, y: 0 };
  let start: Pt = { x: 0, y: 0 };
  const num = () => {
    const v = Number(tokens[i++]);
    if (Number.isNaN(v)) throw new Error(`bad path near token ${i - 1}: ${d}`);
    return v;
  };
  const isCmd = (t: string | undefined) => !!t && /^[A-Za-z]$/.test(t);
  while (i < tokens.length) {
    if (isCmd(tokens[i])) cmd = tokens[i++];
    else if (!cmd) throw new Error(`path must start with a command: ${d}`);
    const rel = cmd === cmd.toLowerCase();
    const P = (x: number, y: number): Pt =>
      rel ? { x: cur.x + x, y: cur.y + y } : { x, y };
    switch (cmd.toUpperCase()) {
      case "M": {
        cur = P(num(), num());
        start = cur;
        cmd = rel ? "l" : "L"; // extra pairs after M are line-tos
        break;
      }
      case "L": {
        const b = P(num(), num());
        segs.push({ k: "L", a: cur, b });
        cur = b;
        break;
      }
      case "H": {
        const x = num();
        const b = { x: rel ? cur.x + x : x, y: cur.y };
        segs.push({ k: "L", a: cur, b });
        cur = b;
        break;
      }
      case "V": {
        const y = num();
        const b = { x: cur.x, y: rel ? cur.y + y : y };
        segs.push({ k: "L", a: cur, b });
        cur = b;
        break;
      }
      case "Q": {
        const c = P(num(), num());
        const b = P(num(), num());
        segs.push({ k: "Q", a: cur, c, b });
        cur = b;
        break;
      }
      case "C": {
        const c1 = P(num(), num());
        const c2 = P(num(), num());
        const b = P(num(), num());
        segs.push({ k: "C", a: cur, c1, c2, b });
        cur = b;
        break;
      }
      case "Z": {
        if (cur.x !== start.x || cur.y !== start.y)
          segs.push({ k: "L", a: cur, b: start });
        cur = start;
        cmd = "";
        break;
      }
      default:
        throw new Error(
          `unsupported path command "${cmd}" (use M L H V C Q Z)`,
        );
    }
  }
  return segs;
};

const pointOn = (s: Seg, t: number): Pt => {
  const u = 1 - t;
  if (s.k === "L")
    return { x: s.a.x + (s.b.x - s.a.x) * t, y: s.a.y + (s.b.y - s.a.y) * t };
  if (s.k === "Q")
    return {
      x: u * u * s.a.x + 2 * u * t * s.c.x + t * t * s.b.x,
      y: u * u * s.a.y + 2 * u * t * s.c.y + t * t * s.b.y,
    };
  return {
    x:
      u * u * u * s.a.x +
      3 * u * u * t * s.c1.x +
      3 * u * t * t * s.c2.x +
      t * t * t * s.b.x,
    y:
      u * u * u * s.a.y +
      3 * u * u * t * s.c1.y +
      3 * u * t * t * s.c2.y +
      t * t * t * s.b.y,
  };
};

export type PathModel = {
  d: string;
  length: number;
  /** point and tangent angle (degrees) at arc length s (clamped to [0, length]) */
  at: (s: number) => { x: number; y: number; angle: number };
  /** the flattened polyline and the cumulative length at each of its points */
  points: Pt[];
  cum: number[];
};

/** Flatten a path (`samples` points per curve) into an arc-length table. */
export const buildPath = (d: string, samples = 64): PathModel => {
  const segs = parsePath(d);
  if (!segs.length) throw new Error(`empty path: ${d}`);
  const points: Pt[] = [segs[0].a];
  for (const s of segs) {
    const n = s.k === "L" ? 1 : samples;
    for (let j = 1; j <= n; j++) points.push(pointOn(s, j / n));
  }
  const cum = [0];
  for (let j = 1; j < points.length; j++)
    cum.push(
      cum[j - 1] +
        Math.hypot(
          points[j].x - points[j - 1].x,
          points[j].y - points[j - 1].y,
        ),
    );
  const length = cum[cum.length - 1];
  const at = (s: number) => {
    const L = Math.max(0, Math.min(length, s));
    let lo = 0;
    let hi = cum.length - 1;
    while (hi - lo > 1) {
      const mid = (lo + hi) >> 1;
      if (cum[mid] <= L) lo = mid;
      else hi = mid;
    }
    // skip zero-length steps so the tangent is defined
    let j = lo;
    while (j + 1 < points.length - 1 && cum[j + 1] - cum[j] < 1e-9) j++;
    const a = points[j];
    const b = points[Math.min(j + 1, points.length - 1)];
    const segLen = cum[j + 1] - cum[j] || 1;
    const t = Math.max(0, Math.min(1, (L - cum[j]) / segLen));
    return {
      x: a.x + (b.x - a.x) * t,
      y: a.y + (b.y - a.y) * t,
      angle: (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI,
    };
  };
  return { d, length, at, points, cum };
};

/** Arc length of the polyline point closest to `pt`. */
export const nearestLength = (path: PathModel, pt: Pt) => {
  let best = 0;
  let bestD = Infinity;
  for (let j = 0; j < path.points.length - 1; j++) {
    const a = path.points[j];
    const b = path.points[j + 1];
    const dx = b.x - a.x;
    const dy = b.y - a.y;
    const l2 = dx * dx + dy * dy;
    const t = l2
      ? Math.max(0, Math.min(1, ((pt.x - a.x) * dx + (pt.y - a.y) * dy) / l2))
      : 0;
    const d = Math.hypot(a.x + dx * t - pt.x, a.y + dy * t - pt.y);
    if (d < bestD) {
      bestD = d;
      best = path.cum[j] + Math.sqrt(l2) * t;
    }
  }
  return best;
};

/**
 * World transform (translate, then scale about the world origin) that puts the
 * path point at arc length `s` on `screen` at `zoom`.
 */
export const pathFrame = (
  path: PathModel,
  s: number,
  zoom: number,
  screen: Pt,
) => {
  const p = path.at(s);
  return {
    tx: screen.x - p.x * zoom,
    ty: screen.y - p.y * zoom,
    z: zoom,
    point: p,
  };
};

export const PathCamera: React.FC<{
  path: PathModel;
  /** arc length the camera is at */
  s: number;
  zoom?: number;
  /** where the path point sits on screen (default: frame centre) */
  screen: Pt;
  /** offset in world px added to the target (lead the subject a little) */
  lead?: Pt;
  children: React.ReactNode;
}> = ({ path, s, zoom = 1, screen, lead = { x: 0, y: 0 }, children }) => {
  const f = pathFrame(path, s, zoom, screen);
  const tx = f.tx - lead.x * zoom;
  const ty = f.ty - lead.y * zoom;
  return (
    <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          transformOrigin: "0 0",
          transform: `translate(${tx}px, ${ty}px) scale(${zoom})`,
        }}
      >
        {children}
      </div>
    </div>
  );
};

/** The path drawn from its start up to arc length `s` (world coordinates). */
export const PathTrail: React.FC<{
  path: PathModel;
  s: number;
  color: string;
  width?: number;
  /** draw dots every `dots` px instead of a solid line */
  dots?: number;
  opacity?: number;
}> = ({ path, s, color, width = 6, dots, opacity = 1 }) => {
  const upTo = Math.max(0, Math.min(path.length, s));
  if (dots) {
    const n = Math.floor(upTo / dots);
    return (
      <>
        {Array.from({ length: n + 1 }, (_, i) => {
          const p = path.at(i * dots);
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: p.x - width / 2,
                top: p.y - width / 2,
                width,
                height: width,
                borderRadius: "50%",
                background: color,
                opacity,
              }}
            />
          );
        })}
      </>
    );
  }
  // the drawn part is our own polyline up to `upTo`, so it matches `at()` exactly
  const pts = path.points.filter((_, j) => path.cum[j] < upTo);
  const end = path.at(upTo);
  const d = [...pts, end]
    .map((p, j) => `${j ? "L" : "M"}${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" ");
  return (
    <svg
      width={1}
      height={1}
      style={{
        position: "absolute",
        left: 0,
        top: 0,
        overflow: "visible",
        opacity,
      }}
    >
      <path
        d={d}
        fill="none"
        stroke={color}
        strokeWidth={width}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};
