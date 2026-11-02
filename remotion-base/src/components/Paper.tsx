import React from "react";
import { AbsoluteFill } from "remotion";

/** Flat background with a fine, static paper grain (deterministic SVG noise). */
export const Paper: React.FC<{ color: string; grain?: number }> = ({
  color,
  grain = 0.35,
}) => (
  <AbsoluteFill style={{ background: color }}>
    <svg
      width="100%"
      height="100%"
      style={{
        position: "absolute",
        inset: 0,
        opacity: grain,
        mixBlendMode: "multiply",
      }}
    >
      <filter id="paper-grain">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.85"
          numOctaves="2"
          seed="4"
        />
        <feColorMatrix values="0 0 0 0 .45  0 0 0 0 .43  0 0 0 0 .38  0 0 0 .18 0" />
      </filter>
      <rect width="100%" height="100%" filter="url(#paper-grain)" />
    </svg>
  </AbsoluteFill>
);
