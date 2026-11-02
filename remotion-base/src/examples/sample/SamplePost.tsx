/**
 * Example feed post (4:5) of the fictional sample client — concept "a typographic system": the three brand words
 * are the set. They arrive one by one, hold as a stack, then fly into the card's
 * tagline while the card is revealed behind them. Survivor: the words.
 *
 * | t (s)     | beat             | moves                              | holds still | carries into next |
 * |-----------|------------------|------------------------------------|-------------|-------------------|
 * | 0.0–1.3   | "Diseño"         | letters arrive one by one          | ground      | Diseño            |
 * | 1.3–1.8   | rest             | drift                              | Diseño      | Diseño            |
 * | 1.8–2.5   | "Color"          | Diseño rises and shrinks, Color in | ground      | both words        |
 * | 2.5–3.2   | "Detalle"        | Detalle arrives                    | stack       | stack             |
 * | 3.2–4.3   | rest on the stack| drift                              | stack       | words             |
 * | 4.3–5.5   | words → tagline  | words fly into the card, card wipes up | ground  | card              |
 * | 5.5–8.0   | CTA hold         | one pulse on the number            | everything  | —                 |
 */
import React from "react";
import {
  AbsoluteFill,
  Img,
  Sequence,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Audio } from "@remotion/media";
import { MotionBlur } from "../../components/MotionBlur";
import { Accent } from "../../components/Accent";
import { Camera } from "../../components/Camera";
import { Paper } from "../../components/Paper";
import { SafeZones } from "../../components/SafeZones";
import { Beat, Beats, Track, TrackRoot } from "../../components/Track";
import { FORMATS } from "../../lib/formats";
import { EASE, land, tween } from "../../lib/motion";
import { MaskReveal, SplitText, progress } from "../../moves";
import { SAMPLE as B, CLIENT, CONTACT, asset } from "./brand";
import {
  Brief,
  Copy,
  CopyProvider,
  contactFrom,
  useCopy,
} from "../../lib/brief";

export const SAMPLE_POST_FRAMES = 240;

// on-screen copy; a brief (render.mjs --brief) overrides it — " / " marks the accented part.
// lines: the three brand words, in order (they also form the tagline under the card);
// headline: CTA line above the card; ctaText + contact: under the card.
export const SAMPLE_POST_COPY: Copy = {
  headline: "Hecho / a mano",
  subtitle: "",
  lines: ["Diseño", "Color", "Detalle"],
  ctaText: "Escribinos por WhatsApp",
  contact: contactFrom(undefined, CONTACT),
};
const img = (f: string) => asset(f);
const K = {
  w1: 0,
  w2: 55,
  w3: 75,
  fly: [130, 165],
  hold: 165,
  pulse: 185,
} as const;
const BEATS: Beat[] = [
  { f: 0, name: "Diseño", kind: "move" },
  { f: 40, name: "rest", kind: "rest" },
  { f: K.w2, name: "Color", kind: "move" },
  { f: K.w3, name: "Detalle", kind: "move" },
  { f: 96, name: "rest on the stack", kind: "rest" },
  { f: K.fly[0], name: "words into the tagline", kind: "move" },
  { f: K.hold, name: "CTA hold", kind: "hold" },
];
const CARD = { x: 110, y: 330, w: 860, h: 540 };
const eyebrow: React.CSSProperties = {
  fontFamily: B.fonts.text,
  fontWeight: 500,
  letterSpacing: "0.32em",
  textTransform: "uppercase",
  color: B.colors.soft,
};

type Layout = { cx: number; cy: number; size: number };

const Word: React.FC<{
  id: string;
  text: string;
  start: number;
  a: Layout;
  b: Layout;
  c: Layout;
  ab: number;
  bc: number;
  color: string;
  italic?: boolean;
}> = ({ id, text, start, a, b, c, ab, bc, color, italic }) => {
  const lerp = (k: keyof Layout) => {
    const v = a[k] + (b[k] - a[k]) * ab;
    return v + (c[k] - v) * bc;
  };
  const size = lerp("size");
  return (
    <Track id={id} kind="text" blurred>
      <div
        style={{
          position: "absolute",
          left: lerp("cx"),
          top: lerp("cy"),
          translate: "-50% -50%",
          whiteSpace: "nowrap",
          fontFamily: B.fonts.display,
          fontWeight: 400,
          fontStyle: italic ? "italic" : "normal",
          fontSize: 150,
          scale: String(size / 150),
          color,
          lineHeight: 1,
        }}
      >
        <SplitText
          text={text}
          start={start}
          by="char"
          stagger={2.5}
          rise={50}
        />
      </div>
    </Track>
  );
};

type Props = { showSafeZones?: boolean; brief?: Brief };

export const SamplePost: React.FC<Props> = ({ brief, ...rest }) => (
  <CopyProvider brief={brief} defaults={SAMPLE_POST_COPY}>
    <Scene {...rest} />
  </CopyProvider>
);

const Scene: React.FC<Omit<Props, "brief">> = ({ showSafeZones = false }) => {
  const copy = useCopy();
  const [w1, w2, w3] = copy.lines;
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const up = land(frame, fps, K.w2, { damping: 14 }); // stack forms
  // words leave the card area fast, then the card wipes up behind them
  const fly = progress(frame, K.fly[0], K.fly[1], EASE.snap);
  const wipe = progress(frame, K.fly[0] + 16, K.fly[1] + 8, EASE.snap);
  const tagline = tween(frame, [K.fly[1] - 6, K.fly[1] + 4], [0, 1]);
  const wordsOut = tween(frame, [K.fly[1] - 4, K.fly[1] + 4], [0, 1]);
  const cta = tween(frame, [K.hold, K.hold + 16], [0, 1], EASE.snap);
  const pulse =
    frame >= K.pulse && frame < K.pulse + 14
      ? 1 + 0.035 * Math.sin(((frame - K.pulse) / 14) * Math.PI)
      : 1;

  // three layouts for the words: alone → stack → tagline under the card
  const tagY = CARD.y + CARD.h + 52;
  const words = [
    {
      id: "word-1",
      text: w1,
      start: K.w1,
      a: { cx: 540, cy: 620, size: 170 },
      b: { cx: 540, cy: 420, size: 130 },
      c: { cx: 420, cy: tagY, size: 30 },
      ab: up,
      color: B.colors.ink,
    },
    {
      id: "word-2",
      text: w2,
      start: K.w2 + 4,
      a: { cx: 540, cy: 640, size: 130 },
      b: { cx: 540, cy: 640, size: 130 },
      c: { cx: 535, cy: tagY, size: 30 },
      ab: 1,
      color: B.colors.accent2,
      italic: true,
    },
    {
      id: "word-3",
      text: w3,
      start: K.w3,
      a: { cx: 540, cy: 860, size: 130 },
      b: { cx: 540, cy: 860, size: 130 },
      c: { cx: 645, cy: tagY, size: 30 },
      ab: 1,
      color: B.colors.accent,
    },
  ];

  return (
    <TrackRoot>
      <AbsoluteFill>
        <Beats beats={BEATS} />
        <Paper color={B.colors.ground} />
        <Camera
          keys={[
            { f: 0, fx: 540, fy: 675, z: 1 },
            { f: K.fly[0], fx: 540, fy: 675, z: 1.02 },
            { f: K.fly[1], fx: 540, fy: 660, z: 1 },
          ]}
          stillFrom={K.hold}
          driftAmp={3}
        >
          {/* the card, revealed upward behind the flying words */}
          <Track id="card" inFrame>
            <div
              style={{
                position: "absolute",
                left: CARD.x,
                top: CARD.y,
                width: CARD.w,
                height: CARD.h,
                opacity: wipe > 0 ? 1 : 0,
              }}
            >
              <MaskReveal
                p={wipe}
                dir="up"
                style={{ position: "absolute", inset: 0 }}
              >
                <div
                  style={{
                    position: "absolute",
                    inset: 0,
                    borderRadius: 30,
                    overflow: "hidden",
                    background: B.colors.paper,
                    boxShadow: "0 30px 60px -20px rgba(60,50,40,.35)",
                  }}
                >
                  <Img
                    src={img("photos/sample-2.jpg")}
                    style={{
                      position: "absolute",
                      left: 0,
                      top: 0,
                      width: "100%",
                      height: "60%",
                      objectFit: "cover",
                      objectPosition: "center 45%",
                    }}
                  />
                  <div
                    style={{
                      position: "absolute",
                      left: 44,
                      top: 250,
                      width: 150,
                      height: 150,
                      borderRadius: "50%",
                      background: B.colors.paper,
                      boxShadow: `0 0 0 6px ${B.colors.paper}, 0 0 0 8px ${B.colors.line}`,
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                    }}
                  >
                    <Img src={img("logo.png")} style={{ width: 112 }} />
                  </div>
                  <div
                    style={{
                      ...eyebrow,
                      position: "absolute",
                      left: 220,
                      right: 30,
                      top: 352,
                      textAlign: "center",
                      fontSize: 21,
                    }}
                  >
                    — Estudio —
                  </div>
                  <div
                    style={{
                      position: "absolute",
                      left: 220,
                      right: 30,
                      top: 382,
                      textAlign: "center",
                      fontFamily: B.fonts.script,
                      fontSize: 80,
                      color: B.colors.accent,
                      lineHeight: 1,
                    }}
                  >
                    Para vos
                  </div>
                  <div
                    style={{
                      position: "absolute",
                      left: 220,
                      right: 30,
                      top: 478,
                      textAlign: "center",
                      fontFamily: B.fonts.display,
                      fontSize: 26,
                      letterSpacing: "0.14em",
                      color: B.colors.ink,
                    }}
                  >
                    {CLIENT.name.toUpperCase()}
                  </div>
                </div>
              </MaskReveal>
            </div>
          </Track>

          <MotionBlur shutterAngle={180} samples={5}>
            <AbsoluteFill style={{ opacity: 1 - wordsOut }}>
              {words.map((w) => (
                <Word key={w.id} {...w} bc={fly} />
              ))}
            </AbsoluteFill>
          </MotionBlur>

          {/* the settled tagline replaces the flown words exactly where they land */}
          <Track id="tagline" kind="text">
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: tagY - 20,
                textAlign: "center",
                opacity: tagline,
                fontFamily: B.fonts.display,
                fontSize: 30,
                color: B.colors.ink,
                letterSpacing: "0.06em",
              }}
            >
              {w1} · <i style={{ color: B.colors.accent2 }}>{w2}</i> ·{" "}
              <span style={{ color: B.colors.accent }}>{w3}</span>
            </div>
          </Track>
        </Camera>

        <Track id="cta-top" kind="text">
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: 120,
              textAlign: "center",
              opacity: cta,
              translate: `0px ${(1 - cta) * 24}px`,
            }}
          >
            <div
              style={{
                fontFamily: B.fonts.display,
                fontWeight: 400,
                fontSize: 84,
                color: B.colors.ink,
              }}
            >
              <Accent text={copy.headline} color={B.colors.accent} />
            </div>
          </div>
        </Track>
        <Track id="cta-phone" kind="text">
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: 1010,
              textAlign: "center",
              opacity: cta,
              translate: `0px ${(1 - cta) * 24}px`,
            }}
          >
            <div style={{ ...eyebrow, fontSize: 22 }}>{copy.ctaText}</div>
            <div
              style={{
                fontFamily: B.fonts.display,
                fontWeight: 400,
                fontSize: 84,
                color: B.colors.accent2,
                scale: String(pulse),
                marginTop: 6,
              }}
            >
              {copy.contact}
            </div>
          </div>
        </Track>

        <Sequence from={4} layout="none">
          <Audio src={staticFile("sfx/click.wav")} volume={0.7} />
        </Sequence>
        <Sequence from={K.w2 + 4} layout="none">
          <Audio src={staticFile("sfx/click.wav")} volume={0.7} />
        </Sequence>
        <Sequence from={K.w3} layout="none">
          <Audio src={staticFile("sfx/click.wav")} volume={0.7} />
        </Sequence>
        <Sequence from={K.fly[0]} layout="none">
          <Audio src={staticFile("sfx/air-in.wav")} volume={0.9} />
        </Sequence>
        <Sequence from={K.fly[1] - 2} layout="none">
          <Audio src={staticFile("sfx/tap.wav")} volume={0.9} />
        </Sequence>
        <Sequence from={K.hold} layout="none">
          <Audio src={staticFile("sfx/chime.wav")} volume={0.8} />
        </Sequence>

        {showSafeZones && <SafeZones format={FORMATS.post} />}
      </AbsoluteFill>
    </TrackRoot>
  );
};
