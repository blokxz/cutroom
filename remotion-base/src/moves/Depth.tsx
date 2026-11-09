/**
 * Depth — one camera, several layers at different distances. The camera dollies and pans through
 * them: near layers move and grow faster than far ones (parallax), and the layers away from the
 * focus distance blur (depth of field). The camera and the nearest plane carry the piece.
 *
 *   layerScale(z, camZ, focal)            size of a layer at distance z relative to its size at the focal distance
 *   layerOffset(layerX, camX, scale)      where the layer sits horizontally (or vertically) for that camera
 *   blurPx(z, camZ, focusZ, opts)         circle of confusion in px: 0 at the focus distance, growing away from it
 *   depthCameraAt(frame, keys)            camera position at a frame, eased between keys
 *   <DepthStage>                          lays the layers out for the camera and focus of this frame
 *
 * Layers are supplied as separate elements (cut-outs, panels, photos at different sizes); this move
 * does not segment a photo. A layer at or behind the camera plane is not drawn.
 */
import React from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import { EASE } from "../lib/motion";
import { Track } from "../components/Track";

export type DepthCam = { f: number; x: number; y: number; z: number; focusZ: number };
export type DepthLayer = { z: number; x: number; y: number; node: React.ReactNode; id?: string };

/** Distance in front of the camera before a layer is too close to draw (fraction of the focal length). */
const NEAR = 0.15;

/** 1 at the focal distance, larger when nearer the lens, smaller when far. Infinity-safe: 0 behind the lens. */
export const layerScale = (z: number, camZ: number, focal = 1000): number => {
  const d = focal + (z - camZ);
  if (d <= focal * NEAR) return 0;
  return focal / d;
};

export const layerOffset = (layerPos: number, camPos: number, scale: number) =>
  (layerPos - camPos) * scale;

export const blurPx = (
  z: number,
  camZ: number,
  focusZ: number,
  opts: { focal?: number; aperture?: number; max?: number } = {},
): number => {
  const focal = opts.focal ?? 1000;
  const d = focal + (z - camZ);
  if (d <= focal * NEAR) return 0;
  const coc = ((opts.aperture ?? 0.012) * Math.abs(z - focusZ) * focal) / d;
  return Math.min(opts.max ?? 24, coc);
};

export const depthCameraAt = (frame: number, keys: DepthCam[]): DepthCam => {
  if (keys.length === 0) throw new Error("depthCameraAt: no keys");
  if (frame <= keys[0].f) return keys[0];
  for (let i = 1; i < keys.length; i++) {
    const a = keys[i - 1];
    const b = keys[i];
    if (frame <= b.f) {
      const u = EASE.glide((frame - a.f) / (b.f - a.f));
      const m = (p: number, q: number) => p + (q - p) * u;
      return { f: frame, x: m(a.x, b.x), y: m(a.y, b.y), z: m(a.z, b.z), focusZ: m(a.focusZ, b.focusZ) };
    }
  }
  return keys[keys.length - 1];
};

export const DepthStage: React.FC<{
  layers: DepthLayer[];
  keys: DepthCam[];
  focal?: number;
  aperture?: number;
  maxBlur?: number;
  trackId?: string;
}> = ({ layers, keys, focal = 1000, aperture, maxBlur, trackId }) => {
  const f = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const cam = depthCameraAt(f, keys);
  const ordered = [...layers].sort((a, b) => b.z - a.z); // far first
  const stage = (
    <>
      {ordered.map((l, i) => {
        const s = layerScale(l.z, cam.z, focal);
        if (s === 0) return null;
        const b = blurPx(l.z, cam.z, cam.focusZ, { focal, aperture, max: maxBlur });
        return (
          <div
            key={l.id ?? i}
            style={{
              position: "absolute",
              left: width / 2 + layerOffset(l.x, cam.x, s),
              top: height / 2 + layerOffset(l.y, cam.y, s),
              transform: `translate(-50%, -50%) scale(${s})`,
              filter: b > 0.4 ? `blur(${b.toFixed(2)}px)` : undefined,
            }}
          >
            {l.node}
          </div>
        );
      })}
    </>
  );
  return trackId ? (
    <Track id={trackId} kind="shape">
      {stage}
    </Track>
  ) : (
    stage
  );
};
