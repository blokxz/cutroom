/**
 * Reusable moves. Each one takes a progress value (0 → 1) or a start frame and
 * returns plain markup, so the caller decides the curve (tween / land / settle).
 *
 *   Morph        a box that becomes another box (position, size, radius, colour)
 *   IrisOpen     the next scene opens out of a point (usually the subject)
 *   MaskReveal   wipe reveal in a direction
 *   SplitText    words or letters arriving one after another with a spring
 *   Typewriter   text typed at a fixed rate with a caret
 *   pushThrough  camera keys that push into a rectangle until it fills the frame
 *
 * Bigger moves, each in its own file (pure math exported next to the component):
 *   ArchWindow    a framed window that morphs arch → rect → circle; the next scene
 *                 opens out of a point of the previous photo        (./ArchWindow)
 *   PostcardDrop  cards fall, squash on landing, stack with a tilt, resolve into a grid
 *                                                                    (./PostcardDrop)
 *   LightArc      a disc of light on an arc, colour morning → night; an iris is born
 *                 from it                                            (./LightArc)
 *   PathCamera    a camera travelling a drawn path across a world of photos, with
 *                 the trail drawing itself                           (./PathCamera)
 *   Key           a key slides into the lock and turns; each turn opens the next
 *                 scene out of the keyhole; a door swings open at the end  (./Key)
 *   WrittenPostcard  handwriting fills the back of a postcard, a photo stamp lands,
 *                 the card flips to show the place                 (./WrittenPostcard)
 *   LightFlood    a field of light floods the frame and drains in rings onto the
 *                 next scene                                         (./LightFlood)
 *   Belt          places on a belt that starts, cruises and brakes exactly on an item
 *                                                                    (./Belt)
 *   ObjectWipe    an object crosses the lens and uncovers the next place (./ObjectWipe)
 *   Calendar      desk-calendar pages tear off and reveal the place under them
 *                                                                    (./Calendar)
 *   FilmStrip     a film strip rolls, then one frame grows to fill the screen (./FilmStrip)
 *   Dominoes      cards tip over one after another, each starting on contact (./Dominoes)
 *   CauseEffect   a cause touches a target; squash and effect start on the hit (./CauseEffect)
 *   DepthStage    one camera through layers: parallax and a focus pull (./Depth)
 */
import React from "react";
import {
  interpolate,
  interpolateColors,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { CamKey, CLAMP, EASE } from "../lib/motion";
import { Track } from "../components/Track";

export type Box = {
  x: number;
  y: number;
  w: number;
  h: number;
  r?: number;
  bg?: string;
};

// ------------------------------------------------------------------ Morph
export const Morph: React.FC<{
  from: Box;
  to: Box;
  p: number;
  style?: React.CSSProperties;
  children?: React.ReactNode;
}> = ({ from, to, p, style, children }) => {
  const m = (a: number, b: number) => a + (b - a) * p;
  const bg =
    from.bg && to.bg
      ? interpolateColors(Math.max(0, Math.min(1, p)), [0, 1], [from.bg, to.bg])
      : (to.bg ?? from.bg);
  return (
    <div
      style={{
        position: "absolute",
        left: m(from.x, to.x),
        top: m(from.y, to.y),
        width: m(from.w, to.w),
        height: m(from.h, to.h),
        borderRadius: m(from.r ?? 0, to.r ?? 0),
        background: bg,
        overflow: "hidden",
        ...style,
      }}
    >
      {children}
    </div>
  );
};

// ------------------------------------------------------------------ IrisOpen
/** Pass `trackId` to let the verifier see the opening circle grow out of the subject. */
export const IrisOpen: React.FC<{
  p: number;
  cx: number;
  cy: number;
  trackId?: string;
  /** set when the iris is rendered inside <MotionBlur> */
  blurred?: boolean;
  children: React.ReactNode;
}> = ({ p, cx, cy, trackId, blurred = false, children }) => {
  const { width, height } = useVideoConfig();
  const far = Math.hypot(Math.max(cx, width - cx), Math.max(cy, height - cy));
  const r = Math.max(0, p) * far;
  return (
    <>
      <div
        style={{
          position: "absolute",
          inset: 0,
          clipPath: `circle(${r}px at ${cx}px ${cy}px)`,
        }}
      >
        {children}
      </div>
      {trackId ? (
        <Track id={trackId} kind="shape" blurred={blurred}>
          <div
            style={{
              position: "absolute",
              left: cx - r,
              top: cy - r,
              width: 2 * r,
              height: 2 * r,
              opacity: r > 1 ? 1 : 0,
              pointerEvents: "none",
            }}
          />
        </Track>
      ) : null}
    </>
  );
};

// ------------------------------------------------------------------ MaskReveal
export const MaskReveal: React.FC<{
  p: number;
  dir?: "up" | "down" | "left" | "right";
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({ p, dir = "up", style, children }) => {
  const q = (1 - Math.max(0, Math.min(1, p))) * 100;
  const inset = {
    up: `${q}% 0 0 0`,
    down: `0 0 ${q}% 0`,
    left: `0 ${q}% 0 0`,
    right: `0 0 0 ${q}%`,
  }[dir];
  return (
    <div style={{ clipPath: `inset(${inset})`, ...style }}>{children}</div>
  );
};

// ------------------------------------------------------------------ SplitText
export const SplitText: React.FC<{
  text: string;
  start: number;
  by?: "word" | "char";
  stagger?: number; // frames between pieces
  rise?: number; // px each piece travels up
  damping?: number;
  style?: React.CSSProperties;
}> = ({
  text,
  start,
  by = "word",
  stagger = 3,
  rise = 40,
  damping = 12,
  style,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pieces = by === "word" ? text.split(/(\s+)/) : Array.from(text);
  let k = 0;
  return (
    <span style={{ display: "inline-block", ...style }}>
      {pieces.map((piece, i) => {
        if (/^\s+$/.test(piece)) return <span key={i}>{piece}</span>;
        const s = spring({
          frame: frame - start - k++ * stagger,
          fps,
          config: { damping, stiffness: 140, mass: 0.8 },
        });
        return (
          <span
            key={i}
            style={{
              display: "inline-block",
              opacity: Math.min(1, s * 1.5),
              translate: `0px ${(1 - s) * rise}px`,
              whiteSpace: "pre",
            }}
          >
            {piece}
          </span>
        );
      })}
    </span>
  );
};

// ------------------------------------------------------------------ Typewriter
export const Typewriter: React.FC<{
  text: string;
  start: number;
  cps?: number;
  caret?: boolean;
  style?: React.CSSProperties;
}> = ({ text, start, cps = 18, caret = true, style }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const n = Math.max(
    0,
    Math.min(text.length, Math.floor(((frame - start) / fps) * cps)),
  );
  const done = n >= text.length;
  const blink = Math.floor(frame / (fps / 2)) % 2 === 0;
  return (
    <span style={style}>
      {text.slice(0, n)}
      {caret && (!done || blink) ? (
        <span style={{ opacity: frame >= start ? 1 : 0 }}>▍</span>
      ) : null}
    </span>
  );
};

// ------------------------------------------------------------------ pushThrough
/**
 * Camera keys that push into `rect` (composition coordinates) between f0 and f1
 * until it fills `fill` of the frame. Combine with the scene's other keys.
 */
export const pushThrough = (
  rect: Box,
  f0: number,
  f1: number,
  frame: { width: number; height: number },
  fill = 1.0,
): CamKey[] => {
  const z = Math.min(frame.width / rect.w, frame.height / rect.h) * fill;
  return [
    { f: f0, fx: frame.width / 2, fy: frame.height / 2, z: 1 },
    {
      f: f1,
      fx: rect.x + rect.w / 2,
      fy: rect.y + rect.h / 2,
      z,
      ease: EASE.in,
    },
  ];
};

/** Small helper: progress of a stretch [f0, f1] with an easing, clamped. */
export const progress = (
  frame: number,
  f0: number,
  f1: number,
  easing = EASE.out,
) => interpolate(frame, [f0, f1], [0, 1], { ...CLAMP, easing });

export * from "./ArchWindow";
export * from "./PostcardDrop";
export * from "./LightArc";
export * from "./PathCamera";
export * from "./Key";
export * from "./WrittenPostcard";
export * from "./LightFlood";
export * from "./Belt";
export * from "./ObjectWipe";
export * from "./Calendar";
export * from "./FilmStrip";
export * from "./Dominoes";
export * from "./CauseEffect";
export * from "./Depth";
export * from "./Entrances";
export * from "./Silk";
