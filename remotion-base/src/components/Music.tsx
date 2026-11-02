import React from "react";
import { useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";

/**
 * Background music that steps out of the way of the sound effects.
 *
 * duckAt: frames where an effect starts; the music dips by `duckDb` around each
 * one (fast attack, slower release) and fades in/out at the ends.
 * loop: repeat the track when it is shorter than the composition (the ducking and
 * fades keep following the composition's frames across the repeat).
 * Only use royalty-free tracks or music the client supplied — keep the licence
 * next to the file in clients/<slug>/assets/music/ and index it in LIBRARY.json.
 */
export const Music: React.FC<{
  src: string;
  volume?: number;
  duckAt?: number[];
  duckDb?: number;
  attack?: number;
  release?: number;
  fadeIn?: number;
  fadeOut?: number;
  loop?: boolean;
}> = ({
  src,
  volume = 0.5,
  duckAt = [],
  duckDb = -9,
  attack = 3,
  release = 18,
  fadeIn = 15,
  fadeOut = 30,
  loop = false,
}) => {
  const { durationInFrames } = useVideoConfig();
  const dip = Math.pow(10, duckDb / 20);
  const gainAt = (f: number) => {
    let g = 1;
    for (const d of duckAt) {
      const t = f - d;
      let k = 0;
      if (t >= -attack && t < 0) k = (t + attack) / attack;
      else if (t >= 0 && t < release * 2)
        k = t < release ? 1 : 1 - (t - release) / release;
      g = Math.min(g, 1 - (1 - dip) * Math.max(0, Math.min(1, k)));
    }
    const fade = Math.min(
      1,
      f / Math.max(1, fadeIn),
      (durationInFrames - f) / Math.max(1, fadeOut),
    );
    return g * Math.max(0, fade);
  };
  return (
    <Audio
      src={src}
      volume={(f) => volume * gainAt(f)}
      loop={loop}
      loopVolumeCurveBehavior="extend"
    />
  );
};
