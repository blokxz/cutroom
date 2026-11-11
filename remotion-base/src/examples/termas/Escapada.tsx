/**
 * Reel "Escapada" (reel 9:16, 15 s) for Bungalows Concordia, after the client's own reference reel: one photo
 * per scene with a slow camera, a two-line caption (a small sans line, then a large serif italic line that comes
 * in out of a blur, one word on a moss box) and a cream closing card with the logo. What is new: every scene
 * change happens through the steam of the hot springs, which rises, covers the frame and thins onto the next
 * photo. The steam and the caption's place carry from scene to scene.
 *
 * | t (s)      | beat              | moves                                   | holds still | carries        |
 * |------------|-------------------|-----------------------------------------|-------------|----------------|
 * | 0.0–0.8    | vapor             | first photo out of the steam, caption   | ground      | steam, caption |
 * | 0.8–2.3    | rest              | slow drift                              | the photo   | steam, caption |
 * | 1.9–2.7    | agua tibia        | through the steam, caption              | ground      | steam, caption |
 * | …          | five more scenes  | the same, each with its own caption     | the photo   | steam, caption |
 * | 11.8–12.5  | cierre            | the cream card comes in through steam   | ground      | steam          |
 * | 12.5–15.0  | logo hold         | logo, call to action, handle            | everything  | —              |
 */
import React from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import { Audio } from "@remotion/media";
import { Caption, blurIn } from "../../components/Caption";
import { Paper } from "../../components/Paper";
import { SafeZones } from "../../components/SafeZones";
import { Beat, Beats, Track, TrackRoot } from "../../components/Track";
import { FORMATS } from "../../lib/formats";
import { EASE, tween } from "../../lib/motion";
import {
  Brief,
  Copy,
  CopyProvider,
  contactFrom,
  useCopy,
} from "../../lib/brief";
import { Steam, veilDensity } from "../../moves";
import { CONTACT } from "../../clients/bungalows-concordia/brand";
import { Cover, Logo, PHOTOS, T, asset } from "./common";

export const ESCAPADA_FRAMES = 450;

// lines: "small line|large line", a {word} in the large line sits on the moss box
export const ESCAPADA_COPY: Copy = {
  headline: "",
  subtitle: "",
  lines: [
    "Imaginate despertar|entre {vapor}",
    "Rodeado de|{verde}",
    "Tu lugar|para frenar",
    "Cortá con|la {rutina}",
  ],
  ctaText: "Reservá tu escapada",
  contact: contactFrom(undefined, CONTACT),
};

// long scenes carry a caption; two short ones are a breath with the picture alone, so the cut is never a metronome
const SCENES: {
  src: string;
  focus: [number, number];
  pan: number;
  name: string;
  dur: number;
  caption?: number;
  ease: (t: number) => number;
}[] = [
  {
    src: "photos/hero.jpg",
    focus: [45, 55],
    pan: -1,
    name: "vapor",
    dur: 86,
    caption: 0,
    ease: EASE.snap,
  },
  {
    src: PHOTOS.sunrise,
    focus: [60, 55],
    pan: 1,
    name: "respiro",
    dur: 30,
    ease: EASE.whip,
  },
  {
    src: PHOTOS.aerial,
    focus: [50, 50],
    pan: -1,
    name: "rodeado de verde",
    dur: 70,
    caption: 1,
    ease: EASE.out,
  },
  {
    src: "photos/living.jpg",
    focus: [45, 60],
    pan: 1,
    name: "tu lugar",
    dur: 70,
    caption: 2,
    ease: EASE.snap,
  },
  {
    src: "photos/kitchen.jpg",
    focus: [45, 55],
    pan: -1,
    name: "todo listo",
    dur: 30,
    ease: EASE.glide,
  },
  {
    src: PHOTOS.sunset,
    focus: [50, 55],
    pan: 1,
    name: "la rutina",
    dur: 82,
    caption: 3,
    ease: EASE.out,
  },
];
const AT = SCENES.map((_, i) =>
  SCENES.slice(0, i).reduce((n, s) => n + s.dur, 0),
);
const END = AT[AT.length - 1] + SCENES[SCENES.length - 1].dur + 4;
const HOLD = END + 20;
const MOVE = 24;
const BEATS: Beat[] = [
  ...SCENES.flatMap((s, i) => [
    { f: AT[i], name: s.name, kind: "move" as const },
    {
      f: AT[i] + Math.min(MOVE, s.dur - 12),
      name: "rest",
      kind: "rest" as const,
    },
  ]),
  { f: END, name: "cierre", kind: "move" },
  { f: HOLD, name: "logo hold", kind: "hold" },
];

type Props = { showSafeZones?: boolean; brief?: Brief };

export const Escapada: React.FC<Props> = ({ brief, ...rest }) => (
  <CopyProvider brief={brief} defaults={ESCAPADA_COPY}>
    <Scene {...rest} />
  </CopyProvider>
);

const Scene: React.FC<Omit<Props, "brief">> = ({ showSafeZones = false }) => {
  const copy = useCopy();
  const frame = useCurrentFrame();
  const density = veilDensity(frame, [...AT.slice(1), END + 6], {
    base: 0.05,
    peak: 0.82,
    before: 7,
    after: 26,
  });
  const opening = tween(frame, [0, 22], [1, 0], EASE.out); // the reel opens out of the steam
  const end = tween(frame, [END - 6, END + 18], [0, 1], EASE.glide);
  const cta = blurIn(frame, HOLD - 6, 9999, 16);
  return (
    <TrackRoot>
      <AbsoluteFill>
        <Beats beats={BEATS} />
        <Paper color={T.colors.ink} />
        {SCENES.map((s, i) => {
          const at = AT[i];
          const shown = i === 0 ? 1 : tween(frame, [at - 5, at + 9], [0, 1]);
          // a push that arrives with the scene, then a very slow drift while it rests
          const push = tween(frame, [at, at + MOVE], [0, 1], s.ease);
          const drift = tween(
            frame,
            [at + MOVE, at + s.dur + 12],
            [0, 1],
            (t) => t,
          );
          const zoom = 1.04 + 0.05 * push + 0.006 * drift;
          return (
            <Track key={s.src} id={`photo-${i}`} kind="image">
              <AbsoluteFill
                style={{
                  opacity: frame < at - 5 ? 0 : shown,
                  translate: `${s.pan * 14 * push}px 0px`,
                }}
              >
                <Cover src={s.src} focus={s.focus} zoom={zoom} />
              </AbsoluteFill>
            </Track>
          );
        })}
        {SCENES.map((s, i) =>
          s.caption === undefined ? null : (
            <Caption
              key={i}
              id={`cap-${s.caption}`}
              text={copy.lines[s.caption] ?? ""}
              at={AT[i]}
              out={(AT[i + 1] ?? END) - 18}
              fonts={T.fonts}
              box={T.colors.ink}
            />
          ),
        )}
        {/* the closing card */}
        <AbsoluteFill style={{ opacity: end }}>
          <AbsoluteFill style={{ background: T.colors.ground }} />
          <Track id="logo" kind="logo">
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: 560,
                display: "flex",
                justifyContent: "center",
              }}
            >
              <Logo width={640} />
            </div>
          </Track>
          <Track id="cta" kind="text">
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: 1210,
                textAlign: "center",
                ...cta,
                fontFamily: T.fonts.text,
                fontWeight: 500,
                fontSize: 34,
                letterSpacing: "0.34em",
                textTransform: "uppercase",
                color: T.colors.ink,
              }}
            >
              {copy.ctaText}
            </div>
          </Track>
          <Track id="contact" kind="text">
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: 1280,
                textAlign: "center",
                ...cta,
                fontFamily: T.fonts.display,
                fontStyle: "italic",
                fontSize: 44,
                color: "#7D4F55",
              }}
            >
              {copy.contact}
            </div>
          </Track>
        </AbsoluteFill>
        <Steam
          density={Math.max(density, opening)}
          trackId="steam"
          seed="escapada"
        />
        <Sequence layout="none">
          <Audio src={asset("score/escapada.wav")} />
        </Sequence>
        {showSafeZones && <SafeZones format={FORMATS.reel} />}
      </AbsoluteFill>
    </TrackRoot>
  );
};
