import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import {
  CamKey,
  cameraAt,
  drift,
  holdFactor,
  latticePoints,
  shake,
} from "../lib/motion";

/**
 * An operated camera: keyed framing + slow hand-held drift.
 * - `stillFrom` fades the drift out for the rest of the piece (e.g. the final CTA hold).
 * - `holds` are [from, to] frame ranges where the drift is zero (a camera that stops while the
 *   picture is read); it ramps in and out around them.
 * - `shakes` add a decaying, seeded shake on each landing frame.
 * Build the keys with leadKeys / whipKeys from lib/motion for a camera that follows and whips.
 */
export const Camera: React.FC<{
  keys: CamKey[];
  driftAmp?: number;
  stillFrom?: number;
  holds?: [number, number][];
  shakes?: { f: number; amp?: number; decayS?: number }[];
  children: React.ReactNode;
}> = ({ keys, driftAmp = 5, stillFrom, holds, shakes, children }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const k = cameraAt(frame, keys);
  const fadeStill =
    stillFrom === undefined
      ? 1
      : Math.max(0, Math.min(1, (stillFrom - frame) / fps));
  const fade = Math.min(fadeStill, holds ? holdFactor(frame, fps, holds) : 1);
  const d = drift(frame, fps, driftAmp * fade);
  let sx = 0;
  let sy = 0;
  let sr = 0;
  (shakes ?? []).forEach((s, i) => {
    const h = shake(frame, fps, s.f, {
      amp: s.amp,
      decayS: s.decayS,
      seed: `shake${i}`,
    });
    sx += h.x;
    sy += h.y;
    sr += h.r;
  });
  const tx = width / 2 - (k.fx + d.x) * k.z + sx;
  const ty = height / 2 - (k.fy + d.y) * k.z + sy;
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          transformOrigin: "0 0",
          transform: `translate(${tx}px, ${ty}px) scale(${k.z}) rotate(${(k.rot ?? 0) + d.r + sr}deg)`,
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

/**
 * A faint grid of dots fixed in the world, so a camera move has something to slide against on
 * an empty ground. Put it inside <Camera>, behind the content.
 */
export const Lattice: React.FC<{
  bounds: { x0: number; y0: number; x1: number; y1: number };
  spacing?: number;
  dot?: number;
  color?: string;
  opacity?: number;
}> = ({ bounds, spacing = 120, dot = 4, color = "#000", opacity = 0.12 }) => (
  <AbsoluteFill style={{ pointerEvents: "none" }}>
    {latticePoints(bounds, spacing).map((p) => (
      <div
        key={`${p.x}:${p.y}`}
        style={{
          position: "absolute",
          left: p.x - dot / 2,
          top: p.y - dot / 2,
          width: dot,
          height: dot,
          borderRadius: "50%",
          background: color,
          opacity,
        }}
      />
    ))}
  </AbsoluteFill>
);
