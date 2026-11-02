/**
 * ArchWindow — a framed window whose outline morphs between shapes (arch → rect →
 * circle) and whose next scene opens out of a point of the previous photo.
 *
 * The idea: one window carries the whole piece. Each place sits inside it; the
 * next place is born as a small arch on a point of interest of the photo before
 * (a door, the steam, a ray of sun), grows into the next shape, and the window
 * outline follows it. The photo before pushes into that same point while the
 * new one opens, so the point never moves on screen.
 *
 * Everything here is pure and progress-driven: the caller computes shapes with
 * `mixShape` / `windowFromPoint` from its own curves and renders <ArchWindow>.
 *
 *   archShape / rectShape / circleShape   build a WindowShape around a centre
 *   mixShape(a, b, p)                     outline between two shapes
 *   coverLayout(photo, frame, focus, anchor, zoom)
 *                                         photo "cover" inside a frame, framed on
 *                                         `focus`, zoomed about `anchor` (which stays put)
 *   anchorPoint(shape, photo)             where the anchor sits on screen
 *   windowFromPoint(point, target, p)     a small arch at `point` grown into `target`
 *   <ArchWindow>                          renders a shape with its photo and frame
 */
import React from "react";
import { Img } from "remotion";
import { Track, TrackKind } from "../components/Track";

export type WindowShape = {
  x: number;
  y: number;
  w: number;
  h: number;
  /** radius of the two top corners */
  rt: number;
  /** radius of the two bottom corners */
  rb: number;
};

/** A tall arch: round top (radius w/2), slightly rounded foot. */
export const archShape = (
  cx: number,
  cy: number,
  w: number,
  h: number,
  rb = 24,
): WindowShape => ({ x: cx - w / 2, y: cy - h / 2, w, h, rt: w / 2, rb });

export const rectShape = (
  cx: number,
  cy: number,
  w: number,
  h: number,
  r = 36,
): WindowShape => ({ x: cx - w / 2, y: cy - h / 2, w, h, rt: r, rb: r });

export const circleShape = (
  cx: number,
  cy: number,
  d: number,
): WindowShape => ({
  x: cx - d / 2,
  y: cy - d / 2,
  w: d,
  h: d,
  rt: d / 2,
  rb: d / 2,
});

const lerp = (a: number, b: number, p: number) => a + (b - a) * p;

/** The outline between two shapes. p is not clamped, so a spring may overshoot. */
export const mixShape = (
  a: WindowShape,
  b: WindowShape,
  p: number,
): WindowShape => ({
  x: lerp(a.x, b.x, p),
  y: lerp(a.y, b.y, p),
  w: lerp(a.w, b.w, p),
  h: lerp(a.h, b.h, p),
  rt: lerp(a.rt, b.rt, p),
  rb: lerp(a.rb, b.rb, p),
});

/** CSS border-radius for a shape (radii never exceed what the box can hold). */
export const shapeRadius = (s: WindowShape) => {
  const max = Math.max(0, Math.min(s.w / 2, s.h / 2));
  const rt = Math.max(0, Math.min(s.rt, max));
  const rb = Math.max(0, Math.min(s.rb, max));
  return `${rt}px ${rt}px ${rb}px ${rb}px`;
};

export type Photo = {
  src: string;
  /** natural size in px (needed for exact, deterministic framing) */
  w: number;
  h: number;
  /** point of the photo kept near the frame centre, in 0–1 photo units */
  focus?: [number, number];
  /** point the photo zooms into — where the next scene opens — in 0–1 photo units */
  anchor?: [number, number];
};

const clamp = (v: number, lo: number, hi: number) =>
  Math.max(lo, Math.min(hi, v));

/**
 * Lay a photo inside a frame of size `frame` so it covers it, framed on `focus`,
 * then zoom by `zoom` about `anchor`. Returns the photo scale `s`, its offset
 * (`ox`, `oy`, frame coordinates) and the anchor's position in the frame
 * (`ax`, `ay`) — which does not depend on `zoom`.
 */
export const coverLayout = (
  photo: { w: number; h: number },
  frame: { w: number; h: number },
  focus: [number, number] = [0.5, 0.5],
  anchor: [number, number] = focus,
  zoom = 1,
) => {
  const s0 = Math.max(frame.w / photo.w, frame.h / photo.h);
  const ox0 = clamp(
    frame.w / 2 - focus[0] * photo.w * s0,
    frame.w - photo.w * s0,
    0,
  );
  const oy0 = clamp(
    frame.h / 2 - focus[1] * photo.h * s0,
    frame.h - photo.h * s0,
    0,
  );
  const ax = ox0 + anchor[0] * photo.w * s0;
  const ay = oy0 + anchor[1] * photo.h * s0;
  const s = s0 * zoom;
  return {
    s,
    ox: ax - anchor[0] * photo.w * s,
    oy: ay - anchor[1] * photo.h * s,
    ax,
    ay,
  };
};

/** Screen position of a photo's anchor inside a window shape. */
export const anchorPoint = (shape: WindowShape, photo: Photo) => {
  const L = coverLayout(photo, shape, photo.focus, photo.anchor ?? photo.focus);
  return { x: shape.x + L.ax, y: shape.y + L.ay };
};

/**
 * The next window being born: a small arch (`seed` px, scaled by `pop`) centred on
 * `point`, grown into `target` by `p`. Use a snappy spring for `pop` and an
 * in-out curve for `p`.
 */
export const windowFromPoint = (
  point: { x: number; y: number },
  target: WindowShape,
  p: number,
  pop = 1,
  seed = { w: 90, h: 120 },
): WindowShape => {
  const w = seed.w * pop;
  const h = seed.h * pop;
  const small: WindowShape = {
    x: point.x - w / 2,
    y: point.y - h / 2,
    w,
    h,
    rt: w / 2,
    rb: Math.min(10, w / 2),
  };
  return mixShape(small, target, p);
};

export const ArchWindow: React.FC<{
  shape: WindowShape;
  photo: Photo;
  /** zoom about the photo's anchor (1 = cover) */
  zoom?: number;
  /** colour and width of the painted frame around the window */
  frame?: { color: string; width: number };
  /** soft drop shadow under the window */
  shadow?: boolean;
  opacity?: number;
  /** opacity of the photo alone (fade it to show what the window holds instead) */
  photoOpacity?: number;
  background?: string;
  trackId?: string;
  trackKind?: TrackKind;
  inFrame?: boolean;
  blurred?: boolean;
  style?: React.CSSProperties;
  /** drawn inside the window, over the photo (window coordinates) */
  children?: React.ReactNode;
}> = ({
  shape,
  photo,
  zoom = 1,
  frame,
  shadow = true,
  opacity = 1,
  photoOpacity = 1,
  background = "transparent",
  trackId,
  trackKind = "subject",
  inFrame = false,
  blurred = false,
  style,
  children,
}) => {
  const L = coverLayout(
    photo,
    shape,
    photo.focus,
    photo.anchor ?? photo.focus,
    zoom,
  );
  const shadows = [
    frame ? `0 0 0 ${frame.width}px ${frame.color}` : null,
    shadow ? "0 40px 80px -36px rgba(60, 42, 34, 0.55)" : null,
  ].filter(Boolean);
  const box = (
    <div
      style={{
        position: "absolute",
        left: shape.x,
        top: shape.y,
        width: Math.max(0, shape.w),
        height: Math.max(0, shape.h),
        borderRadius: shapeRadius(shape),
        overflow: "hidden",
        background,
        opacity,
        boxShadow: shadows.length ? shadows.join(", ") : undefined,
        ...style,
      }}
    >
      <Img
        src={photo.src}
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: photo.w,
          height: photo.h,
          maxWidth: "none",
          transformOrigin: "0 0",
          transform: `translate(${L.ox}px, ${L.oy}px) scale(${L.s})`,
          opacity: photoOpacity,
        }}
      />
      {children}
    </div>
  );
  return trackId ? (
    <Track id={trackId} kind={trackKind} inFrame={inFrame} blurred={blurred}>
      {box}
    </Track>
  ) : (
    box
  );
};
