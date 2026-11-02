/**
 * Key — a key slides into a lock and turns; each turn unlocks the next scene,
 * which opens out of the keyhole. The piece can end on a door swinging open.
 *
 * Pure, frame-driven pieces (the caller picks the start frames):
 *   keyTurn(frame, fps, start, opts)   one insert + quarter turn with a small "click"
 *   keyTurns(frame, fps, starts, opts) several turns in a row: cumulative angle + which turn
 *   keyholeShape(cx, cy, s)            keyhole outline (SVG path) centred on its round head
 *   keyholeCover(cx, cy, w, h)         scale at which the keyhole covers the whole frame
 *   doorAngle(p, open)                 door leaf angle for an opening progress
 *   <KeySvg>        the drawn key with an arched bow: seen from the door, or in profile
 *   <KeyholeIris>   the next scene opening out of a keyhole
 *   <DoorSwing>     a door leaf hinged on one side that swings open onto its children
 */
import React from "react";
import { spring, useVideoConfig } from "remotion";
import { Track } from "../components/Track";

export type TurnState = {
  /** 0 → 1: the key slides into the lock */
  insert: number;
  /** rotation of the key about its shank, degrees */
  angle: number;
  /** the turn has reached its stop (the lock "clicks") */
  clicked: boolean;
};

const INSERT = { damping: 200, stiffness: 120 };
const TURN = { damping: 12, stiffness: 160, mass: 0.7 };

/**
 * One turn starting at `start`: the key slides in for `insertFrames`, then turns
 * `step` degrees with a short overshoot that settles (the click).
 */
export const keyTurn = (
  frame: number,
  fps: number,
  start: number,
  opts: { step?: number; insertFrames?: number; insert?: boolean } = {},
): TurnState => {
  const { step = 90, insertFrames = 12, insert = true } = opts;
  const ins = insert
    ? spring({
        frame: frame - start,
        fps,
        config: INSERT,
        durationInFrames: insertFrames,
      })
    : 1;
  const turnAt = start + (insert ? insertFrames : 0);
  const t = spring({ frame: frame - turnAt, fps, config: TURN });
  return {
    insert: ins,
    angle: step * t,
    clicked: frame >= turnAt && t >= 0.98,
  };
};

/**
 * Several turns in a row (the key stays in the lock after the first): the angle
 * adds up, `k` is the index of the turn in progress (-1 before the first) and
 * `p` its progress 0 → 1 (overshoot included).
 */
export const keyTurns = (
  frame: number,
  fps: number,
  starts: number[],
  opts: { step?: number; insertFrames?: number } = {},
) => {
  const step = opts.step ?? 90;
  let angle = 0;
  let k = -1;
  let p = 0;
  let insert = 0;
  starts.forEach((s, i) => {
    const one = keyTurn(frame, fps, s, {
      step,
      insertFrames: opts.insertFrames,
      insert: i === 0,
    });
    if (i === 0) insert = one.insert;
    angle += one.angle;
    if (frame >= s) {
      k = i;
      p = one.angle / step;
    }
  });
  return { angle, k, p, insert };
};

/**
 * Keyhole outline as an SVG path: a round head of radius `s` centred on (cx, cy)
 * and a flared slot below it, 2.2·s tall.
 */
export const keyholeShape = (cx: number, cy: number, s: number) => {
  const r = s;
  const top = 0.42 * s; // half-width of the slot where it meets the head
  const bot = 0.7 * s; // half-width at the foot
  const yJoin = cy + Math.sqrt(r * r - top * top);
  const yFoot = cy + 2.2 * s;
  return [
    `M ${cx - top} ${yJoin}`,
    `A ${r} ${r} 0 1 1 ${cx + top} ${yJoin}`,
    `L ${cx + bot} ${yFoot}`,
    `L ${cx - bot} ${yFoot}`,
    "Z",
  ].join(" ");
};

/** Head radius at which the keyhole's round head alone covers a w × h frame. */
export const keyholeCover = (cx: number, cy: number, w: number, h: number) =>
  Math.hypot(Math.max(cx, w - cx), Math.max(cy, h - cy)) * 1.02;

/** Door leaf angle (degrees about its hinge) for an opening progress p (0 shut → 1 open). */
export const doorAngle = (p: number, open = 105) =>
  open * Math.max(0, Math.min(1.08, p));

// ------------------------------------------------------------------ KeySvg
/** The bow: an arch like a doorway, with a matching hole. Unit box 0–1. */
const BOW = "M 0 1 L 0 0.45 A 0.5 0.45 0 0 1 1 0.45 L 1 1 Z";
const BOW_HOLE =
  "M 0.27 0.84 L 0.27 0.5 A 0.23 0.22 0 0 1 0.73 0.5 L 0.73 0.84 Z";

/**
 * A key drawn in one colour, with an arched bow (like the doorway).
 *
 * view "front" — seen from the door: only the bow and the collar show; (x, y) is
 *   the keyhole, `angle` turns it in the picture plane about that point, and
 *   `insert` (0 → 1) pushes it from close to the camera into the lock.
 * view "profile" — lying on its side, pointing right; (x, y) is the tip of the
 *   shank and `angle` rotates it in the picture plane about the tip.
 */
export const KeySvg: React.FC<{
  x: number;
  y: number;
  view?: "front" | "profile";
  /** bow width (front) or total length (profile), px */
  size?: number;
  color: string;
  /** hole colour (usually the background) */
  hole: string;
  angle?: number;
  insert?: number;
  trackId?: string;
  blurred?: boolean;
}> = ({
  x,
  y,
  view = "front",
  size = 260,
  color,
  hole,
  angle = 0,
  insert = 1,
  trackId,
  blurred = false,
}) => {
  const shadow = `drop-shadow(0 ${10 + 30 * (1 - insert)}px ${14 + 24 * (1 - insert)}px rgba(50,40,30,0.35))`;
  let node: React.ReactNode;
  if (view === "front") {
    const W = size;
    const H = size * 1.25; // bow + collar, pivot at the bottom centre
    const z = 1 + 0.7 * (1 - insert);
    node = (
      <svg
        width={W}
        height={H}
        viewBox="0 0 1 1.25"
        style={{
          position: "absolute",
          left: x - W / 2,
          top: y - H,
          overflow: "visible",
          transformOrigin: `${W / 2}px ${H}px`,
          transform: `rotate(${angle}deg) scale(${z})`,
          opacity: Math.min(1, insert * 3),
          filter: shadow,
        }}
      >
        <path d={BOW} fill={color} />
        <path d={BOW_HOLE} fill={hole} />
        <rect
          x={0.36}
          y={0.98}
          width={0.28}
          height={0.2}
          rx={0.03}
          fill={color}
        />
        <rect
          x={0.4}
          y={1.17}
          width={0.2}
          height={0.08}
          fill={color}
          opacity={0.75}
        />
      </svg>
    );
  } else {
    const L = size;
    const H = L * 0.42;
    node = (
      <svg
        width={L}
        height={H}
        viewBox={`0 0 ${L} ${H}`}
        style={{
          position: "absolute",
          left: x - L,
          top: y - H * 0.68,
          overflow: "visible",
          transformOrigin: `${L}px ${H * 0.68}px`,
          transform: `rotate(${angle}deg)`,
          filter: shadow,
        }}
      >
        <g
          transform={`translate(${0.02 * L} ${H * 0.02}) scale(${0.3 * L} ${H * 0.9})`}
        >
          <path d={BOW} fill={color} />
          <path d={BOW_HOLE} fill={hole} />
        </g>
        <rect
          x={0.31 * L}
          y={H * 0.56}
          width={0.05 * L}
          height={H * 0.24}
          rx={4}
          fill={color}
        />
        <rect
          x={0.35 * L}
          y={H * 0.62}
          width={0.65 * L}
          height={H * 0.12}
          rx={H * 0.06}
          fill={color}
        />
        <path
          d={`M ${0.74 * L} ${H * 0.72} L ${0.74 * L} ${H * 0.96} L ${0.79 * L} ${H * 0.96}
              L ${0.79 * L} ${H * 0.86} L ${0.84 * L} ${H * 0.86} L ${0.84 * L} ${H * 1.02}
              L ${0.9 * L} ${H * 1.02} L ${0.9 * L} ${H * 0.9} L ${0.95 * L} ${H * 0.9}
              L ${0.95 * L} ${H * 0.72} Z`}
          fill={color}
        />
      </svg>
    );
  }
  return trackId ? (
    <Track id={trackId} kind="shape" blurred={blurred}>
      {node}
    </Track>
  ) : (
    <>{node}</>
  );
};

// ------------------------------------------------------------------ KeyholeIris
/**
 * The next scene opens out of a keyhole at (cx, cy): `p` 0 → 1 grows the
 * keyhole from `from` px to past the frame. Pass `trackId` so the verifier sees
 * the opening grow out of the lock.
 */
export const KeyholeIris: React.FC<{
  p: number;
  cx: number;
  cy: number;
  /** head radius at p = 0 */
  from?: number;
  trackId?: string;
  blurred?: boolean;
  children: React.ReactNode;
}> = ({ p, cx, cy, from = 18, trackId, blurred = false, children }) => {
  const { width, height } = useVideoConfig();
  const to = keyholeCover(cx, cy, width, height);
  const q = Math.max(0, p);
  const s = q <= 0 ? 0 : from * Math.pow(to / from, q);
  return (
    <>
      <div
        style={{
          position: "absolute",
          inset: 0,
          clipPath: s > 0 ? `path("${keyholeShape(cx, cy, s)}")` : "inset(50%)",
        }}
      >
        {children}
      </div>
      {trackId ? (
        <Track id={trackId} kind="shape" blurred={blurred}>
          <div
            style={{
              position: "absolute",
              left: cx - s,
              top: cy - s,
              width: 2 * s,
              height: 3.2 * s,
              opacity: s > 1 ? 1 : 0,
              pointerEvents: "none",
            }}
          />
        </Track>
      ) : null}
    </>
  );
};

/** A plain keyhole drawn on a surface (the lock the key goes into). */
export const Keyhole: React.FC<{
  cx: number;
  cy: number;
  s?: number;
  color: string;
  plate?: string;
}> = ({ cx, cy, s = 18, color, plate }) => (
  <svg
    style={{ position: "absolute", inset: 0, overflow: "visible" }}
    width="100%"
    height="100%"
  >
    {plate ? (
      <rect
        x={cx - s * 2.4}
        y={cy - s * 3.2}
        width={s * 4.8}
        height={s * 7.4}
        rx={s * 2.4}
        fill={plate}
      />
    ) : null}
    <path d={keyholeShape(cx, cy, s)} fill={color} />
  </svg>
);

// ------------------------------------------------------------------ DoorSwing
/**
 * A door leaf covering `rect`, hinged on `hinge`, swinging open with p (0 → 1)
 * in perspective onto `children` (what is behind the door). A warm gap of light
 * grows along the opening edge.
 */
export const DoorSwing: React.FC<{
  p: number;
  rect: { x: number; y: number; w: number; h: number };
  color: string;
  light?: string;
  hinge?: "left" | "right";
  open?: number;
  /** the face of the door (panels, knob, the keyhole) */
  face?: React.ReactNode;
  children?: React.ReactNode;
}> = ({
  p,
  rect,
  color,
  light = "#F7DFA4",
  hinge = "left",
  open = 105,
  face,
  children,
}) => {
  const a = doorAngle(p, open) * (hinge === "left" ? -1 : 1);
  const gap = Math.min(1, Math.max(0, p) * 4);
  return (
    <div
      style={{
        position: "absolute",
        left: rect.x,
        top: rect.y,
        width: rect.w,
        height: rect.h,
        perspective: rect.w * 2.2,
      }}
    >
      <div style={{ position: "absolute", inset: 0, overflow: "hidden" }}>
        {children}
        <div
          style={{
            position: "absolute",
            inset: 0,
            background: `linear-gradient(${hinge === "left" ? 270 : 90}deg, ${light} 0%, transparent 60%)`,
            opacity: 0.55 * gap * (1 - Math.min(1, p)),
            mixBlendMode: "screen",
          }}
        />
      </div>
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: color,
          transformOrigin: hinge === "left" ? "0% 50%" : "100% 50%",
          transform: `rotateY(${a}deg)`,
          backfaceVisibility: "hidden",
          boxShadow: `0 0 ${60 * gap}px rgba(0,0,0,${0.35 * gap})`,
          filter: `brightness(${1 - 0.35 * Math.min(1, Math.abs(a) / open)})`,
        }}
      >
        {face}
      </div>
    </div>
  );
};
