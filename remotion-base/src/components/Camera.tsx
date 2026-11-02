import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from "remotion";
import { CamKey, cameraAt, drift } from "../lib/motion";

/**
 * An operated camera: keyed framing + slow hand-held drift.
 * Pass `stillFrom` to fade the drift out (e.g. for the final CTA hold).
 */
export const Camera: React.FC<{
  keys: CamKey[];
  driftAmp?: number;
  stillFrom?: number;
  children: React.ReactNode;
}> = ({ keys, driftAmp = 5, stillFrom, children }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const k = cameraAt(frame, keys);
  const fade =
    stillFrom === undefined
      ? 1
      : Math.max(0, Math.min(1, (stillFrom - frame) / fps));
  const d = drift(frame, fps, driftAmp * fade);
  const tx = width / 2 - (k.fx + d.x) * k.z;
  const ty = height / 2 - (k.fy + d.y) * k.z;
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          transformOrigin: "0 0",
          transform: `translate(${tx}px, ${ty}px) scale(${k.z}) rotate(${(k.rot ?? 0) + d.r}deg)`,
        }}
      >
        {children}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
