/**
 * Studio-only demos for the moves that had none, so every move in the library has one clip, one sheet and
 * one row in the gallery. Same rules as MovesDemo.tsx: the fictional sample client (synthetic photos), no
 * brief, one move each, a small slate naming the move.
 *
 *   MovesDemo-Squash       a ball dropped on a floor (stretch in flight, squash on contact), then three
 *                          entrances that stretch along their travel
 *   MovesDemo-Morph        a button is pressed and becomes the card it opens
 *   MovesDemo-PushThrough  the camera pushes into one card of a wall until it is the frame
 *   MovesDemo-IrisOpen     the next place opens out of a point of the photo before
 *   MovesDemo-MaskReveal   lines rise from behind their masks, then a photo is uncovered
 *   MovesDemo-SplitText    a line arrives word by word, a name letter by letter
 *   MovesDemo-Typewriter   a message typed on a card, with a caret
 *   MovesDemo-ArchWindow   one window: arch, then rectangle, then circle, the photo inside
 *   MovesDemo-Caption      the caption system on two photos: blur-in serif line, one word on a box
 *   MovesDemo-Camera       an operated camera: drift in the holds, a whip to each photo, a shake on landing
 *   MovesDemo-Steam        a change of place through a veil of steam
 *   MovesDemo-Stream       a stream drawing its course down the frame
 */
import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { Paper } from "../../components/Paper";
import { Camera } from "../../components/Camera";
import { Caption } from "../../components/Caption";
import { Track } from "../../components/Track";
import { CLAMP, CamKey, EASE, land, tween, whipKeys } from "../../lib/motion";
import {
  ArchWindow,
  Bouncer,
  IrisOpen,
  MaskReveal,
  Morph,
  SplitText,
  Steam,
  StreamRibbon,
  Typewriter,
  archShape,
  buildPath,
  circleShape,
  entrancePose,
  mixShape,
  progress,
  pushThrough,
  rectShape,
  streamPoints,
  veilDensity,
} from "../../moves";
import { SAMPLE as B, asset } from "../sample/brand";

export const LIBRARY_DEMO_FRAMES = {
  squash: 130,
  morph: 120,
  push: 140,
  iris: 100,
  mask: 110,
  split: 100,
  type: 130,
  arch: 130,
  caption: 150,
  camera: 160,
  steam: 120,
  stream: 150,
};

const W = 1080;
const H = 1920;
const PHOTO = { w: 1600, h: 1200 };

const cover = (src: string, style: React.CSSProperties = {}) => (
  <Img
    src={asset(src)}
    style={{
      position: "absolute",
      inset: 0,
      width: "100%",
      height: "100%",
      objectFit: "cover",
      ...style,
    }}
  />
);

/** The move's name, small, top left, in every demo: the gallery and the sheets read it. */
const Slate: React.FC<{ name: string; light?: boolean }> = ({
  name,
  light,
}) => (
  <div
    style={{
      position: "absolute",
      left: 72,
      top: 96,
      fontFamily: B.fonts.text,
      fontWeight: 600,
      fontSize: 30,
      letterSpacing: 1,
      color: light ? "rgba(255,255,255,.85)" : B.colors.soft,
    }}
  >
    cutroom · {name}
  </div>
);

// ------------------------------------------------------------------ Squash
const FLOOR = 1170;
const BALL = 150;

export const SquashDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const kinds = ["drop", "rise", "slide"] as const;
  const colors = [B.colors.accent2, B.colors.ink, B.colors.soft];
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <div
        style={{
          position: "absolute",
          left: 60,
          right: 60,
          top: FLOOR + BALL / 2,
          height: 3,
          background: B.colors.line,
        }}
      />
      <Bouncer
        spec={{ start: 8, x0: 170, y0: 330, floor: FLOOR, vx: 700 }}
        size={BALL}
        shadow="rgba(43,45,51,.35)"
        trackId="ball"
      >
        <div
          style={{
            width: "100%",
            height: "100%",
            borderRadius: "50%",
            background: `radial-gradient(circle at 35% 30%, #fff6 0%, #fff0 38%), ${B.colors.accent}`,
          }}
        />
      </Bouncer>
      {kinds.map((k, i) => {
        const p = entrancePose(frame, fps, 70 + i * 10, k, {
          distance: k === "slide" ? 520 : 360,
          dir: -1,
        });
        return (
          <Track key={k} id={`entrance-${k}`} kind="subject">
            <div
              style={{
                position: "absolute",
                left: 150 + i * 290 - 100,
                top: 1480,
                width: 200,
                height: 200,
                borderRadius: 32,
                background: colors[i],
                opacity: p.opacity,
                transform: `translate(${p.x}px, ${p.y}px) rotate(${p.r}deg) scale(${p.s}) scale(${p.sx}, ${p.sy})`,
              }}
            />
          </Track>
        );
      })}
      <Slate name="Squash" />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Morph
export const MorphDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const press =
    1 - 0.05 * Math.sin(Math.PI * Math.min(1, Math.max(0, (frame - 18) / 10)));
  const p =
    frame < 30 ? 0 : land(frame, fps, 30, { damping: 14, stiffness: 120 });
  const from = { x: 290, y: 1480, w: 500, h: 120, r: 60, bg: B.colors.accent };
  const to = { x: 90, y: 330, w: 900, h: 1200, r: 36, bg: B.colors.paper };
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <Track id="morph" kind="shape">
        <Morph
          from={from}
          to={to}
          p={p}
          style={{
            scale: String(press),
            boxShadow: "0 30px 60px -28px rgba(0,0,0,.45)",
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: 0,
              opacity: interpolate(p, [0.25, 0.8], [0, 1], CLAMP),
            }}
          >
            {cover("photos/sample-2.jpg")}
          </div>
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: B.fonts.text,
              fontWeight: 600,
              fontSize: 44,
              color: "#fff",
              opacity: interpolate(p, [0, 0.2], [1, 0], CLAMP),
            }}
          >
            Ver el taller
          </div>
        </Morph>
      </Track>
      <div
        style={{
          position: "absolute",
          left: 150,
          top: 1330,
          fontFamily: B.fonts.display,
          fontSize: 96,
          color: "#fff",
        }}
      >
        <SplitText text="El taller" start={62} stagger={4} />
      </div>
      <Slate name="Morph" />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ pushThrough
const CARD = { w: 300, h: 533, gap: 40 };
const GRID_X = (W - (3 * CARD.w + 2 * CARD.gap)) / 2;
const GRID_Y = (H - (3 * CARD.h + 2 * CARD.gap)) / 2;
const cardRect = (i: number) => ({
  x: GRID_X + (i % 3) * (CARD.w + CARD.gap),
  y: GRID_Y + Math.floor(i / 3) * (CARD.h + CARD.gap),
  w: CARD.w,
  h: CARD.h,
});
const WALL = [1, 2, 3, 4, 5, 6, 3, 1, 2];

export const PushThroughDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const target = cardRect(4);
  const keys: CamKey[] = [
    { f: 0, fx: W / 2, fy: H / 2, z: 0.94 },
    ...pushThrough(target, 34, 78, { width: W, height: H }),
  ];
  const u = progress(frame, 34, 78, EASE.in);
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <Camera keys={keys} driftAmp={4} stillFrom={60}>
        {WALL.map((n, i) => {
          const r = cardRect(i);
          return (
            <div
              key={i}
              style={{
                position: "absolute",
                left: r.x,
                top: r.y,
                width: r.w,
                height: r.h,
                borderRadius: i === 4 ? 18 * (1 - u) : 18,
                overflow: "hidden",
                boxShadow: "0 18px 30px -18px rgba(0,0,0,.4)",
              }}
            >
              {cover(`photos/sample-${n}.jpg`)}
            </div>
          );
        })}
      </Camera>
      <div
        style={{
          position: "absolute",
          left: 90,
          top: 1380,
          fontFamily: B.fonts.display,
          fontSize: 110,
          color: "#fff",
        }}
      >
        <SplitText text="Adentro" start={88} stagger={4} />
      </div>
      <Slate name="pushThrough" light={frame > 70} />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ IrisOpen
const POINT = { x: 700, y: 820 };

export const IrisOpenDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const p = progress(frame, 34, 64, EASE.in);
  const push = 1 + 0.18 * progress(frame, 26, 64, EASE.in);
  const ring = progress(frame, 8, 30, EASE.out);
  return (
    <AbsoluteFill style={{ overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transformOrigin: `${POINT.x}px ${POINT.y}px`,
          scale: String(push),
        }}
      >
        {cover("photos/sample-3.jpg")}
      </div>
      <div
        style={{
          position: "absolute",
          left: POINT.x - 60,
          top: POINT.y - 60,
          width: 120,
          height: 120,
          borderRadius: "50%",
          border: "6px solid #fff",
          opacity: ring * (1 - p * 4),
          scale: String(0.6 + 0.4 * ring),
        }}
      />
      <IrisOpen p={p} cx={POINT.x} cy={POINT.y} trackId="iris">
        {cover("photos/sample-5.jpg")}
      </IrisOpen>
      <Slate name="IrisOpen" light />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ MaskReveal
const LINES = ["Diseño", "Color", "Detalle"];

export const MaskRevealDemo: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <Track id="lines" kind="text">
        <div
          style={{
            position: "absolute",
            left: 90,
            top: 300,
            display: "flex",
            flexDirection: "column",
            gap: 4,
          }}
        >
          {LINES.map((t, i) => {
            const u = progress(frame, 10 + i * 6, 26 + i * 6, EASE.snap);
            return (
              <div key={t} style={{ overflow: "hidden", height: 170 }}>
                <div
                  style={{
                    fontFamily: B.fonts.display,
                    fontSize: 156,
                    lineHeight: "170px",
                    color: i === 1 ? B.colors.accent2 : B.colors.ink,
                    translate: `0px ${(1 - u) * 110}%`,
                  }}
                >
                  {t}
                </div>
              </div>
            );
          })}
        </div>
      </Track>
      <MaskReveal
        p={progress(frame, 52, 80, EASE.snap)}
        dir="right"
        style={{
          position: "absolute",
          left: 90,
          top: 900,
          width: 900,
          height: 760,
          borderRadius: 28,
          overflow: "hidden",
        }}
      >
        {cover("photos/sample-4.jpg")}
      </MaskReveal>
      <Slate name="MaskReveal" />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ SplitText
export const SplitTextDemo: React.FC = () => (
  <AbsoluteFill>
    <Paper color={B.colors.ground} />
    <div
      style={{
        position: "absolute",
        left: 90,
        right: 90,
        top: 640,
        fontFamily: B.fonts.display,
        fontSize: 124,
        lineHeight: 1.05,
        color: B.colors.ink,
      }}
    >
      <SplitText
        text="Hecho a mano, pieza por pieza"
        start={8}
        stagger={4}
        rise={60}
      />
    </div>
    <div
      style={{
        position: "absolute",
        left: 90,
        top: 1120,
        fontFamily: B.fonts.text,
        fontWeight: 600,
        fontSize: 64,
        color: B.colors.accent,
      }}
    >
      <SplitText
        text="Estudio Ejemplo"
        by="char"
        start={44}
        stagger={1.6}
        rise={34}
        damping={10}
      />
    </div>
    <Slate name="SplitText" />
  </AbsoluteFill>
);

// ------------------------------------------------------------------ Typewriter
const MSG1 = "Llegamos el viernes a la tarde.";
const MSG2 = "¿Tienen lugar para dos?";

export const TypewriterDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const cps = 16;
  const second = 14 + Math.ceil((MSG1.length / cps) * fps) + 10;
  const lift = land(frame, fps, 0, { damping: 16 });
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <div
        style={{
          position: "absolute",
          left: 90,
          top: 700,
          width: 900,
          height: 420,
          padding: "60px 64px",
          boxSizing: "border-box",
          borderRadius: 28,
          background: B.colors.paper,
          boxShadow: "0 30px 60px -30px rgba(0,0,0,.35)",
          fontFamily: B.fonts.text,
          fontSize: 54,
          lineHeight: 1.4,
          color: B.colors.ink,
          translate: `0px ${(1 - lift) * 80}px`,
          opacity: Math.min(1, lift * 2),
        }}
      >
        <div>
          <Typewriter text={MSG1} start={14} cps={cps} caret={frame < second} />
        </div>
        <div style={{ color: B.colors.accent }}>
          {frame >= second ? (
            <Typewriter text={MSG2} start={second} cps={cps} />
          ) : null}
        </div>
      </div>
      <Slate name="Typewriter" />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ ArchWindow
export const ArchWindowDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const arch = archShape(540, 960, 520, 820);
  const rect = rectShape(540, 960, 900, 1300, 36);
  const circle = circleShape(540, 960, 780);
  const a = frame < 26 ? 0 : land(frame, fps, 26, { damping: 15 });
  const b = frame < 80 ? 0 : land(frame, fps, 80, { damping: 15 });
  const shape = mixShape(mixShape(arch, rect, a), circle, b);
  const born = land(frame, fps, 0, { damping: 18 });
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <ArchWindow
        shape={shape}
        photo={{
          src: asset("photos/sample-6.jpg"),
          ...PHOTO,
          focus: [0.5, 0.5],
        }}
        frame={{ color: B.colors.paper, width: 14 }}
        zoom={1 + 0.08 * tween(frame, [0, 130], [0, 1], EASE.glide)}
        opacity={Math.min(1, born * 1.5)}
        trackId="window"
      />
      <Slate name="ArchWindow" />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Caption
export const CaptionDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const fade = tween(frame, [70, 80], [0, 1], EASE.glide);
  const fonts = { display: B.fonts.display, text: B.fonts.text };
  return (
    <AbsoluteFill>
      {cover("photos/sample-2.jpg", {
        scale: String(1.04 + 0.04 * (frame / 150)),
      })}
      <div style={{ position: "absolute", inset: 0, opacity: fade }}>
        {cover("photos/sample-6.jpg", {
          scale: String(1.08 - 0.04 * (frame / 150)),
        })}
      </div>
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(180deg, rgba(0,0,0,0) 35%, rgba(0,0,0,.45) 100%)",
        }}
      />
      <Caption
        text="Pensado|para {quedarse}"
        at={0}
        out={57}
        id="cap-1"
        fonts={fonts}
        box={B.colors.accent}
        top={1180}
      />
      <Caption
        text="Cada pieza|tiene su {historia}"
        at={75}
        out={140}
        id="cap-2"
        fonts={fonts}
        box={B.colors.accent2}
        top={1180}
      />
      <Slate name="Caption" light />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Camera
const PANEL = 1180; // photo width plus the gap between photos in the world

export const CameraDemo: React.FC = () => {
  const k0: CamKey = { f: 0, fx: W / 2, fy: H / 2, z: 1 };
  const first = whipKeys(k0, { fx: PANEL + W / 2, fy: H / 2, z: 1 }, 56, 8);
  const second = whipKeys(
    first[first.length - 1],
    { fx: 2 * PANEL + W / 2, fy: H / 2, z: 1.06 },
    116,
    8,
  );
  const keys = [...first, ...second.slice(1)];
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <Camera
        keys={keys}
        driftAmp={10}
        holds={[
          [44, 50],
          [104, 110],
        ]}
        shakes={[
          { f: 56, amp: 16 },
          { f: 116, amp: 16 },
        ]}
      >
        {[1, 4, 5].map((n, i) => (
          <Track key={n} id={`photo-${i}`} kind="image">
            <div
              style={{
                position: "absolute",
                left: i * PANEL,
                top: 0,
                width: W,
                height: H,
                overflow: "hidden",
              }}
            >
              {cover(`photos/sample-${n}.jpg`)}
            </div>
          </Track>
        ))}
      </Camera>
      <Slate name="Camera" light />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Steam
export const SteamDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const swap = tween(frame, [54, 68], [0, 1], EASE.glide);
  return (
    <AbsoluteFill>
      {cover("photos/sample-1.jpg", {
        scale: String(1.02 + 0.05 * (frame / 120)),
      })}
      <div style={{ position: "absolute", inset: 0, opacity: swap }}>
        {cover("photos/sample-5.jpg", {
          scale: String(1.1 - 0.05 * (frame / 120)),
        })}
      </div>
      <Steam
        density={veilDensity(frame, [60], {
          base: 0.06,
          peak: 0.85,
          before: 16,
          after: 26,
        })}
        trackId="steam"
        leadFrames={120}
      />
      <Slate name="Steam" light />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Stream
const COURSE = buildPath(
  `M ${streamPoints(-120, H + 120, 40, { amp: 260, wavelength: 1300 })
    .map((p) => `${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
    .join(" L ")}`,
);

export const StreamDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const s = COURSE.length * progress(frame, 6, 112, EASE.glide);
  return (
    <AbsoluteFill>
      <Paper color="#E9EDDF" />
      <StreamRibbon path={COURSE} s={s} width={200} flow={frame * 2} />
      <Slate name="Stream" />
    </AbsoluteFill>
  );
};
