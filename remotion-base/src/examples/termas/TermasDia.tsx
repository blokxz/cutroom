/**
 * Reel A — "Un día en las termas" (reel 9:16, 12 s). Family: light_clock. A disc of light crosses the sky
 * while the photos run from sunrise to sunset; the disc is what carries from every photo to the next.
 *
 * | t (s)     | beat           | moves                              | holds still | carries into next |
 * |-----------|----------------|------------------------------------|-------------|-------------------|
 * | 0.0–1.3   | amanecer       | sunrise photo, the disc is born    | ground      | the light         |
 * | 1.3–2.2   | rest           | slow push                          | the photo   | the light         |
 * | 2.2–2.8   | vapor          | steam photo dissolves in           | ground      | the light         |
 * | 2.8–3.7   | rest           | slow push                          | the photo   | the light         |
 * | 3.7–4.3   | interior       | indoor steam                       | ground      | the light         |
 * | 4.3–5.1   | rest           |                                    | the photo   | the light         |
 * | 5.1–5.7   | mediodía       | blue sky pool                      | ground      | the light         |
 * | 5.7–6.5   | rest           |                                    | the photo   | the light         |
 * | 6.5–7.1   | vista aérea    | aerial view                        | ground      | the light         |
 * | 7.1–7.9   | rest           |                                    | the photo   | the light         |
 * | 7.9–8.5   | atardecer      | sunset photo                       | ground      | the light         |
 * | 8.5–9.0   | rest           |                                    | the photo   | the light         |
 * | 9.0–12.0  | logo hold      | closing card fades in              | everything  | —                 |
 */
import React from "react";
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from "remotion";
import { Audio } from "@remotion/media";
import { LightArc } from "../../moves";
import { Paper } from "../../components/Paper";
import { SafeZones } from "../../components/SafeZones";
import { Beat, Beats, TrackRoot, Track } from "../../components/Track";
import { FORMATS } from "../../lib/formats";
import { CLAMP, EASE, tween } from "../../lib/motion";
import { Brief, CopyProvider, useCopy } from "../../lib/brief";
import { Cover, EndCard, PHOTOS, T, TERMAS_COPY, asset } from "./common";

export const TERMAS_DIA_FRAMES = 360;

// photo, focus, frame it comes in
const SCENES: {
  src: string;
  focus: [number, number];
  at: number;
  name: string;
}[] = [
  { src: PHOTOS.sunrise, focus: [60, 50], at: 0, name: "amanecer" },
  { src: PHOTOS.steam, focus: [55, 55], at: 66, name: "vapor" },
  { src: PHOTOS.indoor, focus: [50, 60], at: 111, name: "interior" },
  { src: PHOTOS.sky, focus: [50, 55], at: 153, name: "mediodía" },
  { src: PHOTOS.aerial, focus: [50, 55], at: 195, name: "vista aérea" },
  { src: PHOTOS.sunset, focus: [45, 55], at: 237, name: "atardecer" },
];
const HOLD = 270;
const BEATS: Beat[] = [
  ...SCENES.flatMap((s, i) => [
    { f: s.at, name: s.name, kind: "move" as const },
    { f: s.at + (i === 0 ? 40 : 18), name: "rest", kind: "rest" as const },
  ]),
  { f: HOLD, name: "logo hold", kind: "hold" },
];
const ARC = { x0: 150, x1: 930, y: 560, lift: 230 };

type Props = { showSafeZones?: boolean; brief?: Brief };

export const TermasDia: React.FC<Props> = ({ brief, ...rest }) => (
  <CopyProvider brief={brief} defaults={TERMAS_COPY}>
    <Scene {...rest} />
  </CopyProvider>
);

const Scene: React.FC<Omit<Props, "brief">> = ({ showSafeZones = false }) => {
  const copy = useCopy();
  const frame = useCurrentFrame();
  // the disc moves while a photo arrives and holds still while it rests
  const stops = SCENES.map((_, i) => 0.03 + (0.94 * i) / (SCENES.length - 1));
  const later = SCENES.slice(1);
  const u = interpolate(
    frame,
    [0, ...later.flatMap((s) => [s.at, s.at + 20])],
    [stops[0], ...later.flatMap((_, i) => [stops[i], stops[i + 1]])],
    { ...CLAMP, easing: EASE.glide },
  );
  const born = tween(frame, [0, 24], [0, 1]);
  const end = tween(frame, [HOLD, HOLD + 16], [0, 1], EASE.snap);
  return (
    <TrackRoot>
      <AbsoluteFill>
        <Beats beats={BEATS} />
        <Paper color={T.colors.ink} />
        {SCENES.map((s, i) => {
          const fade = i === 0 ? 1 : tween(frame, [s.at, s.at + 18], [0, 1]);
          // a push that arrives with the photo and then rests
          const zoom =
            1.02 + 0.04 * tween(frame, [s.at, s.at + 22], [0, 1], EASE.out);
          return (
            <Track key={s.src} id={`photo-${i}`} kind="image" blurred>
              <AbsoluteFill style={{ opacity: frame < s.at ? 0 : fade }}>
                <Cover src={s.src} focus={s.focus} zoom={zoom} />
              </AbsoluteFill>
            </Track>
          );
        })}
        <LightArc
          arc={ARC}
          u={u}
          size={110}
          opacity={born}
          halo={0.5}
          trackId="light"
          blurred
        />
        <EndCard p={end} copy={copy} />
        <Sequence layout="none">
          <Audio src={asset("score/termas-dia.wav")} />
        </Sequence>
        {showSafeZones && <SafeZones format={FORMATS.reel} />}
      </AbsoluteFill>
    </TrackRoot>
  );
};
