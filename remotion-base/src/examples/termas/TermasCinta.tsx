/**
 * Reel C — "Cinta de recuerdos" (reel 9:16, 12 s). Family: film_strip. A strip of photos rolls through the
 * frame and stops on each one; at the end the last photo grows until it fills the screen and the closing
 * card lands on it. The strip is what carries.
 *
 * | t (s)     | beat        | moves                              | holds still | carries into next |
 * |-----------|-------------|------------------------------------|-------------|-------------------|
 * | 0.0–1.0   | la cinta    | the strip slides in                | ground      | the strip         |
 * | 1.0–2.2   | rest        | drift                              | the strip   | the strip         |
 * | 2.2–3.1   | roll 1      | the strip rolls to the next photo  | ground      | the strip         |
 * | …         | rest / roll | four more rolls, a rest after each | the strip   | the strip         |
 * | 8.0–8.9   | grow        | the last photo grows to full frame | ground      | the photo         |
 * | 8.9–12.0  | logo hold   | closing card                       | everything  | —                 |
 */
import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { Audio } from "@remotion/media";
import { MotionBlur } from "../../components/MotionBlur";
import { FilmStrip } from "../../moves";
import { Paper } from "../../components/Paper";
import { SafeZones } from "../../components/SafeZones";
import { Beat, Beats, Track, TrackRoot } from "../../components/Track";
import { FORMATS } from "../../lib/formats";
import { EASE, tween } from "../../lib/motion";
import { Brief, CopyProvider, useCopy } from "../../lib/brief";
import { Cover, EndCard, PHOTOS, T, TERMAS_COPY, asset } from "./common";

export const TERMAS_CINTA_FRAMES = 360;

const FRAMES = [
  {
    src: PHOTOS.sunrise,
    focus: [60, 50] as [number, number],
    name: "amanecer",
  },
  { src: PHOTOS.steam, focus: [55, 55] as [number, number], name: "vapor" },
  { src: PHOTOS.sky, focus: [50, 55] as [number, number], name: "cielo" },
  { src: PHOTOS.indoor, focus: [50, 60] as [number, number], name: "interior" },
  {
    src: PHOTOS.aerial,
    focus: [50, 55] as [number, number],
    name: "vista aérea",
  },
  {
    src: PHOTOS.sunset,
    focus: [45, 55] as [number, number],
    name: "atardecer",
  },
];
const ROLL_S = 0.7;
const LEG = Math.round(ROLL_S * 30);
const REST = 20;
const ROLLS: number[] = [60];
for (let i = 1; i < 5; i++) ROLLS.push(ROLLS[i - 1] + LEG + REST);
const GROW = ROLLS[4] + LEG + 14;
const GROW_LEN = 24;
const HOLD = GROW + GROW_LEN;
const BEATS: Beat[] = [
  { f: 0, name: "la cinta", kind: "move" },
  { f: 30, name: "rest", kind: "rest" },
  ...ROLLS.flatMap((f, i) => [
    { f, name: `roll → ${FRAMES[i + 1].name}`, kind: "move" as const },
    { f: f + LEG, name: "rest", kind: "rest" as const },
  ]),
  { f: GROW, name: "grow", kind: "move" },
  { f: HOLD, name: "logo hold", kind: "hold" },
];

type Props = { showSafeZones?: boolean; brief?: Brief };

export const TermasCinta: React.FC<Props> = ({ brief, ...rest }) => (
  <CopyProvider brief={brief} defaults={TERMAS_COPY}>
    <Scene {...rest} />
  </CopyProvider>
);

const Scene: React.FC<Omit<Props, "brief">> = ({ showSafeZones = false }) => {
  const copy = useCopy();
  const frame = useCurrentFrame();
  const slide = tween(frame, [0, 30], [1, 0], EASE.out); // the strip arrives from below
  // the cream card comes in over the growing photo, slowly enough not to read as a cut
  const end = tween(frame, [GROW + 8, GROW + 40], [0, 1], EASE.glide);
  return (
    <TrackRoot>
      <AbsoluteFill>
        <Beats beats={BEATS} />
        <Paper color={T.colors.ground} />
        <AbsoluteFill
          style={{
            translate: `0px ${slide * 900}px`,
            opacity: 1 - slide * 0.6,
          }}
        >
          <MotionBlur shutterAngle={180} samples={5} travel={40}>
            <FilmStrip
              frames={FRAMES.map((f) => (
                <Cover key={f.src} src={f.src} focus={f.focus} />
              ))}
              cell={{ w: 640, h: 880 }}
              gap={40}
              x0={540}
              y={900}
              stops={ROLLS.map((at, i) => ({ at, index: i + 1 }))}
              moveS={ROLL_S}
              stripColor={T.colors.ink}
              grow={{
                index: 5,
                at: GROW,
                growS: GROW_LEN / 30,
                fill: { x: 0, y: 0, w: 1080, h: 1920 },
              }}
              trackId="strip"
              blurred
              growEase={EASE.snap}
            />
          </MotionBlur>
        </AbsoluteFill>
        <Track id="photo-last" kind="image" blurred>
          <AbsoluteFill style={{ opacity: 0 }} />
        </Track>
        <EndCard p={end} copy={copy} />
        <Sequence layout="none">
          <Audio src={asset("score/termas-cinta.wav")} />
        </Sequence>
        {showSafeZones && <SafeZones format={FORMATS.reel} />}
      </AbsoluteFill>
    </TrackRoot>
  );
};
