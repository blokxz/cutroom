import React from "react";
import { AbsoluteFill } from "remotion";
import { Format } from "../lib/formats";

/** Overlay that tints the areas covered by the platform's UI (margins from the verifier specs). Use only while composing. */
export const SafeZones: React.FC<{ format: Format }> = ({ format }) => {
  const { safe } = format;
  const band: React.CSSProperties = {
    position: "absolute",
    background: "rgba(230,40,60,0.18)",
    outline: "2px dashed rgba(230,40,60,0.6)",
  };
  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      <div style={{ ...band, left: 0, right: 0, top: 0, height: safe.top }} />
      <div
        style={{ ...band, left: 0, right: 0, bottom: 0, height: safe.bottom }}
      />
      <div
        style={{
          ...band,
          top: safe.top,
          bottom: safe.bottom,
          left: 0,
          width: safe.left,
        }}
      />
      <div
        style={{
          ...band,
          top: safe.top,
          bottom: safe.bottom,
          right: 0,
          width: safe.right,
        }}
      />
    </AbsoluteFill>
  );
};
