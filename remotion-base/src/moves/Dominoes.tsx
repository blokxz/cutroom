/**
 * Dominoes — a row of upright cards tips over one after another; each card starts to fall the
 * moment the one before it touches it. A cause that is always visible (the falling wave) carries
 * the piece; the contact is the boundary.
 *
 *   tipAngle(frame, fps, start, opts)       0 → 90° with gravity (angle grows with the time squared)
 *   chainStarts(n, first, fps, opts)        the frame each card starts, so card k+1 starts when card k touches it
 *   <Dominoes>                              the row, falling in order, each card showing its content
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { Track } from "../components/Track";

export type TipOpts = {
  /** seconds a free fall from upright to flat takes */
  fallS?: number;
  /** degrees at which a falling card touches the next one */
  contactDeg?: number;
};

const FLAT = 90;

/** Angle of one card: upright before `start`, then gravity pulls it flat in `fallS`. */
export const tipAngle = (frame: number, fps: number, start: number, opts: TipOpts = {}) => {
  const t = (frame - start) / fps;
  if (t <= 0) return 0;
  const u = Math.min(1, t / (opts.fallS ?? 0.7));
  return FLAT * u * u;
};

/** Start frame of each of `n` cards. Card k+1 starts when card k reaches `contactDeg`. */
export const chainStarts = (n: number, first: number, fps: number, opts: TipOpts = {}): number[] => {
  const c = Math.min(FLAT, Math.max(1, opts.contactDeg ?? 18));
  const gap = (opts.fallS ?? 0.7) * fps * Math.sqrt(c / FLAT);
  return Array.from({ length: n }, (_, k) => Math.round(first + k * gap));
};

export const Dominoes: React.FC<{
  cards: React.ReactNode[];
  card: { w: number; h: number };
  /** x of card 0's centre and the shared floor line (y of the card bottoms) */
  x0: number;
  floorY: number;
  spacing: number;
  first: number;
  opts?: TipOpts;
  /** how long a fallen card lingers flat before it fades (seconds) */
  fadeS?: number;
  trackId?: string;
}> = ({ cards, card, x0, floorY, spacing, first, opts, fadeS = 0.5, trackId }) => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const starts = chainStarts(cards.length, first, fps, opts);
  const row = (
    <>
      {cards.map((node, k) => {
        const a = tipAngle(f, fps, starts[k], opts);
        const land = starts[k] + (opts?.fallS ?? 0.7) * fps;
        const o = f <= land ? 1 : Math.max(0, 1 - (f - land) / (fadeS * fps));
        return (
          <div
            key={k}
            style={{
              position: "absolute",
              left: x0 + k * spacing - card.w / 2,
              top: floorY - card.h,
              width: card.w,
              height: card.h,
              transformOrigin: "100% 100%",
              transform: `rotate(${a}deg)`,
              opacity: o,
              borderRadius: 10,
              overflow: "hidden",
              boxShadow: "0 18px 30px -14px rgba(0,0,0,.35)",
            }}
          >
            {node}
          </div>
        );
      })}
    </>
  );
  return trackId ? (
    <Track id={trackId} kind="shape">
      {row}
    </Track>
  ) : (
    row
  );
};
