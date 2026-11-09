/**
 * Example reel (9:16) of the fictional sample client — concept "a desk calendar": the calendar block
 * is the set. It rises into place, its pages are torn away one by one and each page leaves a
 * place of the studio under it; the last page stays, with the free dates. Family: calendar
 * (surface carry, wipe boundary). Survivor: the calendar block.
 *
 * | t (s)     | beat           | moves                                 | holds still    | carries into next |
 * |-----------|----------------|---------------------------------------|----------------|-------------------|
 * | 0.0–1.4   | calendar settles | block rises and lands               | ground         | calendar block    |
 * | 1.4–2.4   | rest           | camera drift stops (hold)             | calendar block | calendar block    |
 * | 2.4–3.1   | tear March     | page lifts, falls; camera shakes      | ground         | calendar block    |
 * | 3.1–3.5   | tear April     | second page torn, short               | ground         | calendar block    |
 * | 3.5–4.3   | rest           | camera drift stops (hold)             | calendar block | calendar block    |
 * | 4.3–5.0   | tear May       | last tear; the free-dates page shows  | ground         | calendar block    |
 * | 5.0–8.0   | CTA hold       | one pulse on the number               | everything     | —                 |
 *
 * Sound: the cue list in dates.cues.json comes from tools/sound_events.py run on the draft render.
 */
import React from "react";
import { AbsoluteFill, Img, Sequence, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Audio } from "@remotion/media";
import { Accent } from "../../components/Accent";
import { Camera, Lattice } from "../../components/Camera";
import { MotionBlur } from "../../components/MotionBlur";
import { Paper } from "../../components/Paper";
import { SafeZones } from "../../components/SafeZones";
import { Beat, Beats, Track, TrackRoot } from "../../components/Track";
import { FORMATS } from "../../lib/formats";
import { EASE, land, tween } from "../../lib/motion";
import { Calendar } from "../../moves";
import { SAMPLE as B, CONTACT, asset } from "./brand";
import { Brief, Copy, CopyProvider, contactFrom, useCopy } from "../../lib/brief";
import cues from "./dates.cues.json";

export const SAMPLE_DATES_FRAMES = 240;

export const SAMPLE_DATES_COPY: Copy = {
  headline: "Tus fechas / libres",
  subtitle: "",
  lines: ["Marzo", "Abril", "Mayo"],
  ctaText: "Reservá tu fecha",
  contact: contactFrom(undefined, CONTACT),
};

const K = { rise: 0, tear: [72, 93, 129], hold: 150, pulse: 176 } as const;
const BEATS: Beat[] = [
  { f: 0, name: "calendar settles", kind: "move" },
  { f: 42, name: "rest", kind: "rest" },
  { f: K.tear[0], name: "tear March", kind: "move" },
  { f: K.tear[1], name: "tear April", kind: "move" },
  { f: 105, name: "rest", kind: "rest" },
  { f: K.tear[2], name: "tear May", kind: "move" },
  { f: K.hold, name: "CTA hold", kind: "hold" },
];
const BOX = { x: 130, y: 400, w: 780, h: 1080 };
const eyebrow: React.CSSProperties = {
  fontFamily: B.fonts.text,
  fontWeight: 500,
  letterSpacing: "0.32em",
  textTransform: "uppercase",
  color: B.colors.soft,
};

const Place: React.FC<{ photo: string; label: string; id: string }> = ({ photo, label, id }) => (
  <div style={{ position: "absolute", inset: 0 }}>
    <Img src={asset(photo)} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover" }} />
    <Track id={id} kind="text" blurred>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          bottom: 56,
          textAlign: "center",
          fontFamily: B.fonts.display,
          fontStyle: "italic",
          fontSize: 120,
          color: B.colors.paper,
          textShadow: "0 4px 24px rgba(0,0,0,.45)",
        }}
      >
        {label}
      </div>
    </Track>
  </div>
);

type Props = { showSafeZones?: boolean; brief?: Brief };

export const SampleDates: React.FC<Props> = ({ brief, ...rest }) => (
  <CopyProvider brief={brief} defaults={SAMPLE_DATES_COPY}>
    <Scene {...rest} />
  </CopyProvider>
);

const Scene: React.FC<Omit<Props, "brief">> = ({ showSafeZones = false }) => {
  const copy = useCopy();
  const [m1, m2, m3] = copy.lines;
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rise = land(frame, fps, K.rise, { damping: 14 });
  const cta = tween(frame, [K.hold, K.hold + 16], [0, 1], EASE.snap);
  const pulse =
    frame >= K.pulse && frame < K.pulse + 14
      ? 1 + 0.035 * Math.sin(((frame - K.pulse) / 14) * Math.PI)
      : 1;
  const centre = { fx: 540, fy: 940 };

  return (
    <TrackRoot>
      <AbsoluteFill>
        <Beats beats={BEATS} />
        <Paper color={B.colors.ground} />
        <Camera
          keys={[
            { f: 0, ...centre, z: 1 },
            { f: K.tear[0], ...centre, z: 1.0 },
            { f: K.tear[2], ...centre, z: 1.04 },
            { f: K.hold, ...centre, z: 1.0 },
          ]}
          holds={[
            [42, K.tear[0]],
            [105, K.tear[2]],
          ]}
          shakes={[
            { f: K.tear[0] + 12, amp: 7 },
            { f: K.tear[1] + 12, amp: 7 },
            { f: K.tear[2] + 12, amp: 9 },
          ]}
          stillFrom={K.hold}
          driftAmp={4}
        >
          <Lattice
            bounds={{ x0: -200, y0: -200, x1: 1300, y1: 2200 }}
            spacing={140}
            color={B.colors.ink}
            opacity={0.1}
          />
          <MotionBlur shutterAngle={180} samples={5} travel={60}>
            <AbsoluteFill style={{ translate: `0px ${(1 - rise) * 260}px`, opacity: Math.min(1, rise * 2) }}>
              <Calendar
                box={BOX}
                paper={B.colors.paper}
                header={B.colors.accent}
                trackId="calendar"
                pages={[
                  { tearAt: K.tear[0], content: <Place id="place-1" photo="photos/sample-1.jpg" label={m1} /> },
                  { tearAt: K.tear[1], content: <Place id="place-2" photo="photos/sample-2.jpg" label={m2} /> },
                  { tearAt: K.tear[2], content: <Place id="place-3" photo="photos/sample-3.jpg" label={m3} /> },
                  {
                    content: (
                      <div style={{ position: "absolute", inset: 0, opacity: cta }}>
                        <Track id="cta-top" kind="text" blurred>
                          <div style={{ position: "absolute", left: 0, right: 0, top: 250, textAlign: "center", fontFamily: B.fonts.display, fontSize: 104, color: B.colors.ink, lineHeight: 1.05 }}>
                            <Accent text={copy.headline} color={B.colors.accent} />
                          </div>
                        </Track>
                        <Track id="cta-phone" kind="text" blurred>
                          <div style={{ position: "absolute", left: 0, right: 0, top: 560, textAlign: "center" }}>
                            <div style={{ ...eyebrow, fontSize: 28 }}>{copy.ctaText}</div>
                            <div style={{ fontFamily: B.fonts.display, fontSize: 76, color: B.colors.accent2, scale: String(pulse), marginTop: 12 }}>
                              {copy.contact}
                            </div>
                          </div>
                        </Track>
                      </div>
                    ),
                  },
                ]}
              />
            </AbsoluteFill>
          </MotionBlur>
        </Camera>

        {(cues as { f: number; effect: string; volume: number }[]).map((c) => (
          <Sequence key={`${c.f}-${c.effect}`} from={c.f} layout="none">
            <Audio src={staticFile(`sfx/${c.effect}.wav`)} volume={c.volume} />
          </Sequence>
        ))}

        {showSafeZones && <SafeZones format={FORMATS.reel} />}
      </AbsoluteFill>
    </TrackRoot>
  );
};
