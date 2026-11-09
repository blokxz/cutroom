/**
 * Reel B — "El arroyo" (reel 9:16, 12 s). Family: trail. A line of water is drawn through the grounds and
 * the camera follows it, photo to photo (the stream of the logo made into a walk). The line is what carries.
 *
 * | t (s)     | beat        | moves                               | holds still | carries into next |
 * |-----------|-------------|-------------------------------------|-------------|-------------------|
 * | 0.0–1.0   | el arroyo   | the line draws in, first photo lands| ground      | the line          |
 * | 1.0–2.2   | rest        | drift                               | the photo   | the line          |
 * | 2.2–3.1   | → aérea     | camera walks the line               | ground      | the line          |
 * | 3.1–3.9   | rest        |                                     | the photo   | the line          |
 * | 3.9–4.8   | → cielo     |                                     | ground      | the line          |
 * | 4.8–5.5   | rest        |                                     | the photo   | the line          |
 * | 5.5–6.5   | → interior  |                                     | ground      | the line          |
 * | 6.5–7.2   | rest        |                                     | the photo   | the line          |
 * | 7.2–8.1   | → amanecer  |                                     | ground      | the line          |
 * | 8.1–8.9   | rest        |                                     | the photo   | the line          |
 * | 8.9–9.8   | → atardecer |                                     | ground      | the line          |
 * | 9.8–12.0  | logo hold   | closing card                        | everything  | —                 |
 */
import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { Audio } from "@remotion/media";
import { Lattice } from "../../components/Camera";
import { Paper } from "../../components/Paper";
import { SafeZones } from "../../components/SafeZones";
import { Beat, Beats, Track, TrackRoot } from "../../components/Track";
import { FORMATS } from "../../lib/formats";
import { EASE, tween } from "../../lib/motion";
import { Brief, CopyProvider, useCopy } from "../../lib/brief";
import { MotionBlur } from "../../components/MotionBlur";
import {
  PathCamera,
  StreamRibbon,
  buildPath,
  nearestLength,
  streamCenter,
  streamPoints,
} from "../../moves";
import { Cover, EndCard, PHOTOS, T, TERMAS_COPY, asset } from "./common";

export const TERMAS_ARROYO_FRAMES = 360;

const STOP_Y = [0, 1500, 3000, 4500, 6000, 7500];
const BEND = { cx: 540, amp: 300, wavelength: 1150 };
const STOPS = [
  {
    src: PHOTOS.stream,
    r: -2,
    name: "el arroyo",
    focus: [50, 50] as [number, number],
  },
  {
    src: PHOTOS.aerial,
    r: 2,
    name: "vista aérea",
    focus: [50, 55] as [number, number],
  },
  {
    src: PHOTOS.sky,
    r: -2,
    name: "cielo",
    focus: [50, 55] as [number, number],
  },
  {
    src: PHOTOS.indoor,
    r: 2,
    name: "interior",
    focus: [50, 60] as [number, number],
  },
  {
    src: PHOTOS.sunrise,
    r: -2,
    name: "amanecer",
    focus: [60, 50] as [number, number],
  },
  {
    src: PHOTOS.sunset,
    r: 1,
    name: "atardecer",
    focus: [45, 55] as [number, number],
  },
].map((p, i) => ({ ...p, y: STOP_Y[i], x: streamCenter(STOP_Y[i], BEND) }));
// the stream wanders: its centre line is sampled every 40 px and the camera walks it
const D = `M ${streamPoints(-900, 7900, 40, BEND)
  .map((p) => `${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
  .join(" L ")}`;
const TRAIL = buildPath(D);
const AT = STOPS.map((p) => nearestLength(TRAIL, p));

// frames: open, rest, then (leg, rest) x 4 and a last leg
const LEG = 28;
const REST = 22;
const LEGS: number[] = [66];
for (let i = 1; i < 5; i++) LEGS.push(LEGS[i - 1] + LEG + REST);
const HOLD = LEGS[4] + LEG;
const BEATS: Beat[] = [
  { f: 0, name: "el arroyo", kind: "move" },
  { f: 30, name: "rest", kind: "rest" },
  ...LEGS.flatMap((f, i) => [
    { f, name: `→ ${STOPS[i + 1].name}`, kind: "move" as const },
    ...(i < 4 ? [{ f: f + LEG, name: "rest", kind: "rest" as const }] : []),
  ]),
  { f: HOLD, name: "logo hold", kind: "hold" },
];

type Props = { showSafeZones?: boolean; brief?: Brief };

export const TermasArroyo: React.FC<Props> = ({ brief, ...rest }) => (
  <CopyProvider brief={brief} defaults={TERMAS_COPY}>
    <Scene {...rest} />
  </CopyProvider>
);

const Scene: React.FC<Omit<Props, "brief">> = ({ showSafeZones = false }) => {
  const copy = useCopy();
  const frame = useCurrentFrame();
  // each leg has its own curve so the walk does not feel mechanical
  const LEG_EASE = [EASE.glide, EASE.whip, EASE.glide, EASE.snap, EASE.whip];
  const leg = LEGS.findIndex((f) => frame >= f && frame < f + LEG);
  const done = LEGS.filter((f) => frame >= f + LEG).length;
  const s =
    leg >= 0
      ? tween(
          frame,
          [LEGS[leg], LEGS[leg] + LEG],
          [AT[leg], AT[leg + 1]],
          LEG_EASE[leg],
        )
      : AT[done];
  const drawn = Math.max(s, tween(frame, [0, 30], [0, AT[0]], EASE.out));
  const end = tween(frame, [HOLD, HOLD + 16], [0, 1], EASE.snap);
  return (
    <TrackRoot>
      <AbsoluteFill>
        <Beats beats={BEATS} />
        <Paper color={T.colors.ground} />
        <MotionBlur shutterAngle={180} samples={5} travel={70}>
          <PathCamera path={TRAIL} s={s} zoom={1} screen={{ x: 540, y: 960 }}>
            <Lattice
              bounds={{ x0: -600, y0: -1200, x1: 1700, y1: 8700 }}
              spacing={170}
              color={T.colors.ink}
              opacity={0.06}
            />
            <StreamRibbon path={TRAIL} s={drawn} width={230} flow={s} />
            {STOPS.map((p, i) => {
              const landed =
                i === 0 ? tween(frame, [8, 30], [0, 1], EASE.out) : 1;
              return (
                <Track key={p.src} id={`card-${i}`} kind="image" blurred>
                  <div
                    style={{
                      position: "absolute",
                      left: p.x - 370,
                      top: p.y - 480,
                      width: 740,
                      height: 960,
                      background: T.colors.paper,
                      boxShadow: "0 30px 60px -24px rgba(18,50,74,.5)",
                      rotate: `${p.r}deg`,
                      opacity: landed,
                      scale: String(0.94 + 0.06 * landed),
                    }}
                  >
                    <div
                      style={{
                        position: "absolute",
                        inset: 24,
                        overflow: "hidden",
                      }}
                    >
                      <Cover src={p.src} focus={p.focus} />
                    </div>
                  </div>
                </Track>
              );
            })}
          </PathCamera>
        </MotionBlur>
        <EndCard p={end} copy={copy} />
        <Sequence layout="none">
          <Audio src={asset("score/termas-arroyo.wav")} />
        </Sequence>
        {showSafeZones && <SafeZones format={FORMATS.reel} />}
      </AbsoluteFill>
    </TrackRoot>
  );
};
