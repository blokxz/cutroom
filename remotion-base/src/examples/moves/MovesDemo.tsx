/**
 * Studio-only demos of the bigger moves, with the fictional sample client (synthetic photos).
 * They are not pieces (no brief, no beat sheet): each shows one move working so
 * it can be judged and tuned before it is used inside a bespoke concept.
 *
 *   MovesDemo-PostcardDrop  four cards fall, squash, stack, then resolve into a grid
 *   MovesDemo-LightArc      the disc crosses the day; an iris opens out of it at dusk
 *   MovesDemo-PathCamera    the camera walks a drawn trail across placed photos
 *   MovesDemo-Key           a key turns in each lock and the next place opens out of
 *                           the keyhole; the last place swings open like a door
 *   MovesDemo-WrittenPostcard  the back of a postcard is written, the stamp lands,
 *                           the card flips to show the place
 *   MovesDemo-LightFlood    light floods the frame and drains in rings onto the next place
 *   MovesDemo-Belt          four places on a belt that starts, cruises and brakes on the last
 *   MovesDemo-ObjectWipe    a bar crosses the lens and uncovers the next place
 *   MovesDemo-Calendar      pages tear off one by one; the last page stays for the dates
 *   MovesDemo-FilmStrip     a film strip rolls through the lens, then one frame grows to fill the screen
 *   MovesDemo-Dominoes      photo cards tip over one after another, each starting on contact
 *   MovesDemo-CauseEffect   a ball hits a card: it squashes on that frame and a ring spreads from it
 *   MovesDemo-Depth         one camera dollies through layers; parallax and a focus pull
 *   MovesDemo-Silk          slow translucent ribbons as a living background that loops exactly
 *   MovesDemo-Gather        five entrances (rise, drop, slide, pop, swing), then the cast gathers into a logo
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
import { CLAMP, EASE, land } from "../../lib/motion";
import {
  DoorSwing,
  Handwriting,
  KeySvg,
  Keyhole,
  KeyholeIris,
  LightArc,
  Postcard,
  Stamp,
  flipAngle,
  keyTurn,
  writeSchedule,
  writingEnd,
  PathCamera,
  PathTrail,
  PostcardDrop,
  Belt,
  Calendar,
  CauseEffect,
  DepthStage,
  Dominoes,
  FilmStrip,
  Gather,
  LightFlood,
  Silk,
  entrancePose,
  ObjectWipe,
  buildPath,
  nearestLength,
  progress,
} from "../../moves";
import { SAMPLE as B, CONTACT, asset } from "../sample/brand";

export const MOVES_DEMO_FRAMES = {
  postcards: 150,
  light: 150,
  path: 210,
  key: 220,
  written: 300,
  flood: 120,
  belt: 130,
  wipe: 100,
  calendar: 210,
  strip: 190,
  dominoes: 150,
  cause: 120,
  depth: 150,
  gather: 130,
  silk: 240,
};

// ------------------------------------------------------------------ PostcardDrop
export const PostcardDropDemo: React.FC = () => (
  <AbsoluteFill>
    <Paper color={B.colors.ground} />
    <PostcardDrop
      brand={B}
      table={{ x: 540, y: 900 }}
      cards={[
        { src: asset("photos/sample-1.jpg"), at: 4, caption: "El taller" },
        { src: asset("photos/sample-2.jpg"), at: 26, caption: "La mesa" },
        { src: asset("photos/sample-3.jpg"), at: 48, caption: "El color" },
        { src: asset("photos/sample-4.jpg"), at: 70, caption: "El detalle" },
      ]}
      gridAt={104}
      grid={{ area: { x: 90, y: 420, w: 860, h: 1000 }, cols: 2, gap: 30 }}
    />
  </AbsoluteFill>
);

// ------------------------------------------------------------------ LightArc
const ARC = { x0: 160, x1: 920, y: 760, lift: 420 };
const DAY = ["#F7DFA4", "#F2B160", "#D9826E", B.colors.accent];

export const LightArcDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const u = progress(frame, 10, 100, EASE.glide);
  const born = land(frame, fps, 4);
  const iris = progress(frame, 104, 132, EASE.in);
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <LightArc
        arc={ARC}
        u={u}
        size={90}
        colors={DAY}
        scale={0.3 + 0.7 * born}
        halo={(frame % 40) / 40}
        iris={{
          p: iris,
          children: (
            <Img
              src={asset("photos/sample-4.jpg")}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          ),
        }}
      />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ PathCamera
const TRAIL = buildPath(
  "M 300 300 C 900 300 1300 700 1400 1200 C 1500 1700 600 1700 500 2300",
);
const STOPS = [
  { src: "photos/sample-1.jpg", x: 300, y: 300, r: -3 },
  { src: "photos/sample-2.jpg", x: 1400, y: 1200, r: 2.5 },
  { src: "photos/sample-3.jpg", x: 500, y: 2300, r: -2 },
];

export const PathCameraDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const at = STOPS.map((s) => nearestLength(TRAIL, s));
  // walk stop to stop, pausing at each photo
  const s = interpolate(
    frame,
    [10, 80, 110, 180],
    [at[0], at[1], at[1], at[2]],
    {
      ...CLAMP,
      easing: EASE.glide,
    },
  );
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <PathCamera
        path={TRAIL}
        s={s}
        zoom={0.62}
        screen={{ x: width / 2, y: height / 2 }}
      >
        <PathTrail
          path={TRAIL}
          s={s}
          color={B.colors.accent}
          width={12}
          dots={34}
        />
        {STOPS.map((p) => (
          <div
            key={p.src}
            style={{
              position: "absolute",
              left: p.x - 330,
              top: p.y - 400,
              width: 660,
              height: 800,
              background: B.colors.paper,
              boxShadow: "0 22px 40px -18px rgba(50,40,30,.45)",
              rotate: `${p.r}deg`,
            }}
          >
            <Img
              src={asset(p.src)}
              style={{
                position: "absolute",
                left: 28,
                top: 28,
                width: 604,
                height: 640,
                objectFit: "cover",
              }}
            />
          </div>
        ))}
      </PathCamera>
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Key
const LOCK = { x: 540, y: 960 };
const photo = (src: string) => (
  <Img
    src={asset(src)}
    style={{ width: "100%", height: "100%", objectFit: "cover" }}
  />
);

/** One lock: plate + keyhole, the key going in and turning, fading as the iris opens. */
const Lock: React.FC<{ at: number; irisAt: number; plate: string }> = ({
  at,
  irisAt,
  plate,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const turn = keyTurn(frame, fps, at + 6);
  const shown = interpolate(frame, [at, at + 6], [0, 1], CLAMP);
  const gone = interpolate(frame, [irisAt, irisAt + 8], [1, 0], CLAMP);
  if (frame < at) return null;
  return (
    <AbsoluteFill style={{ opacity: shown * gone }}>
      <Keyhole
        cx={LOCK.x}
        cy={LOCK.y}
        s={24}
        color={B.colors.ink}
        plate={plate}
      />
      {frame >= at + 6 ? (
        <KeySvg
          x={LOCK.x}
          y={LOCK.y}
          size={160}
          color={B.colors.ink}
          hole={plate}
          insert={turn.insert}
          angle={turn.angle}
        />
      ) : null}
    </AbsoluteFill>
  );
};

export const KeyDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const iris1 = progress(frame, 36, 60, EASE.in);
  const iris2 = progress(frame, 100, 124, EASE.in);
  const door = progress(frame, 166, 200, EASE.glide);
  const behind = (
    <AbsoluteFill
      style={{
        justifyContent: "center",
        alignItems: "center",
        textAlign: "center",
        gap: 28,
      }}
    >
      <Paper color={B.colors.ground} />
      <div
        style={{
          fontFamily: B.fonts.display,
          fontStyle: "italic",
          fontSize: 92,
          color: B.colors.ink,
        }}
      >
        Pasá, es tuyo
      </div>
      <div
        style={{
          fontFamily: B.fonts.text,
          fontWeight: 600,
          fontSize: 44,
          color: B.colors.accent,
        }}
      >
        {CONTACT.whatsapp}
      </div>
    </AbsoluteFill>
  );
  return (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: B.colors.accent }} />
      <Lock at={4} irisAt={36} plate={B.colors.paper} />
      <KeyholeIris p={iris1} cx={LOCK.x} cy={LOCK.y}>
        {photo("photos/sample-1.jpg")}
      </KeyholeIris>
      {frame >= 60 ? (
        <Lock at={68} irisAt={100} plate={B.colors.paper} />
      ) : null}
      <KeyholeIris p={iris2} cx={LOCK.x} cy={LOCK.y}>
        <DoorSwing
          p={door}
          rect={{ x: 0, y: 0, w: 1080, h: 1920 }}
          color={B.colors.accent}
          face={photo("photos/sample-3.jpg")}
        >
          {behind}
        </DoorSwing>
      </KeyholeIris>
      {frame >= 124 ? (
        <Lock at={130} irisAt={166} plate={B.colors.paper} />
      ) : null}
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ WrittenPostcard
const LETTER =
  "Hola:\nla mañana en el taller,\nla tarde entre colores\ny un detalle al final.";
const CARD = { x: 540, y: 900, w: 980, h: 660 };
const WRITE_AT = 12;
const WRITE_CPS = 16;

export const WrittenPostcardDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const end = writingEnd(
    writeSchedule(LETTER, { start: WRITE_AT, fps, cps: WRITE_CPS }),
  );
  const stampAt = Math.round(end) + 6;
  const stamp = land(frame, fps, stampAt, { damping: 14, stiffness: 180 });
  const mark = progress(frame, stampAt + 14, stampAt + 20, EASE.snap);
  const flipAt = stampAt + 40;
  const angle = flipAngle(frame, fps, flipAt);
  const settle = progress(frame, flipAt + 10, flipAt + 50, EASE.glide);
  const sw = 170;
  const sh = 210;
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <Postcard
        {...CARD}
        angle={angle}
        tilt={-2 + 2 * settle}
        scale={1 + 0.08 * settle}
        paper={B.colors.paper}
        line={B.colors.line}
        back={
          <>
            <Handwriting
              text={LETTER}
              start={WRITE_AT}
              cps={WRITE_CPS}
              font={B.fonts.script ?? B.fonts.display}
              size={50}
              color={B.colors.ink}
              lineHeight={1.45}
              style={{ position: "absolute", left: 50, top: 120, width: 520 }}
            />
            {frame >= stampAt ? (
              <Stamp
                src={asset("photos/sample-1.jpg")}
                w={sw}
                h={sh}
                paper={B.colors.paper}
                ink={B.colors.accent}
                font={B.fonts.text}
                mark="Estudio · Ejemplo"
                markP={mark}
                style={{
                  left: CARD.w - sw - 46,
                  top: 44,
                  opacity: Math.min(1, stamp * 4),
                  transform: `scale(${1.5 - 0.5 * stamp}) rotate(${4 - 2 * stamp}deg)`,
                }}
              />
            ) : null}
          </>
        }
        front={
          <>
            {photo("photos/sample-1.jpg")}
            <div
              style={{
                position: "absolute",
                left: 48,
                bottom: 36,
                fontFamily: B.fonts.display,
                fontStyle: "italic",
                fontSize: 84,
                color: B.colors.paper,
                textShadow: "0 2px 16px rgba(0,0,0,0.35)",
              }}
            >
              El taller
            </div>
          </>
        }
      />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ LightFlood
const fullPhoto = (src: string) => (
  <AbsoluteFill>
    <Img
      src={asset(src)}
      style={{ width: "100%", height: "100%", objectFit: "cover" }}
    />
  </AbsoluteFill>
);

export const LightFloodDemo: React.FC = () => (
  <AbsoluteFill>
    <Paper color={B.colors.ground} />
    {fullPhoto("photos/sample-1.jpg")}
    <LightFlood
      trackId="flood"
      spec={{ at: 20, riseS: 0.4, holdS: 0.2, drainS: 1.1 }}
      center={{ x: 540, y: 1500 }}
      glow="#F2B160"
      tint="#F7DFA4"
    >
      {fullPhoto("photos/sample-3.jpg")}
    </LightFlood>
  </AbsoluteFill>
);

// ------------------------------------------------------------------ Belt
const BELT_PHOTOS = [
  "photos/sample-1.jpg",
  "photos/sample-2.jpg",
  "photos/sample-3.jpg",
  "photos/sample-4.jpg",
];
const BELT_SPACING = 820;

export const BeltDemo: React.FC = () => (
  <AbsoluteFill>
    <Paper color={B.colors.ground} />
    <Belt
      trackId="belt"
      spec={{
        at: 10,
        durS: 3.4,
        distance: 3 * BELT_SPACING,
        rampS: 0.6,
        brakeS: 1.1,
      }}
      spacing={BELT_SPACING}
      origin={{ x: 540, y: 960 }}
      items={BELT_PHOTOS.map((src) => (
        <div
          key={src}
          style={{
            width: 720,
            height: 960,
            borderRadius: 28,
            overflow: "hidden",
            boxShadow: "0 24px 60px rgba(0,0,0,0.22)",
          }}
        >
          {fullPhoto(src)}
        </div>
      ))}
    />
  </AbsoluteFill>
);

// ------------------------------------------------------------------ ObjectWipe
export const ObjectWipeDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const p = progress(frame, 20, 70, EASE.glide);
  return (
    <AbsoluteFill>
      <ObjectWipe
        p={p}
        dir="right"
        size={{ w: width, h: height }}
        thickness={440}
        from={fullPhoto("photos/sample-2.jpg")}
        to={fullPhoto("photos/sample-4.jpg")}
        object={
          <div
            style={{
              width: "100%",
              height: "100%",
              background: `repeating-linear-gradient(90deg, ${B.colors.paper} 0 56px, ${B.colors.accent2} 56px 76px)`,
              boxShadow: "inset 0 0 80px rgba(0,0,0,0.15)",
            }}
          />
        }
      />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Calendar
export const CalendarDemo: React.FC = () => (
  <AbsoluteFill>
    <Paper color={B.colors.ground} />
    <Calendar
      box={{ x: 140, y: 380, w: 800, h: 1100 }}
      header={B.colors.accent}
      paper={B.colors.paper}
      pages={[
        { tearAt: 30, content: fullPhoto("photos/sample-1.jpg") },
        { tearAt: 80, content: fullPhoto("photos/sample-2.jpg") },
        { tearAt: 130, content: fullPhoto("photos/sample-3.jpg") },
        {
          content: (
            <div
              style={{
                height: "100%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontFamily: B.fonts.display,
                fontSize: 92,
                color: B.colors.ink,
              }}
            >
              your dates
            </div>
          ),
        },
      ]}
    />
  </AbsoluteFill>
);

// ------------------------------------------------------------------ FilmStrip
export const FilmStripDemo: React.FC = () => (
  <AbsoluteFill>
    <Paper color={B.colors.ground} />
    <FilmStrip
      frames={["photos/sample-1.jpg", "photos/sample-2.jpg", "photos/sample-3.jpg", "photos/sample-4.jpg"].map(fullPhoto)}
      cell={{ w: 560, h: 760 }}
      y={960}
      x0={540}
      stops={[
        { at: 20, index: 1 },
        { at: 62, index: 2 },
        { at: 104, index: 3 },
      ]}
      grow={{ index: 3, at: 146, growS: 1, fill: { x: 0, y: 0, w: 1080, h: 1920 } }}
    />
  </AbsoluteFill>
);

// ------------------------------------------------------------------ Dominoes
export const DominoesDemo: React.FC = () => (
  <AbsoluteFill>
    <Paper color={B.colors.ground} />
    <AbsoluteFill style={{ top: 0 }}>{fullPhoto("photos/sample-6.jpg")}</AbsoluteFill>
    <Dominoes
      cards={["photos/sample-1.jpg", "photos/sample-2.jpg", "photos/sample-3.jpg", "photos/sample-4.jpg", "photos/sample-5.jpg"].map(fullPhoto)}
      card={{ w: 190, h: 720 }}
      x0={130}
      floorY={1500}
      spacing={200}
      first={18}
      opts={{ fallS: 0.8, contactDeg: 20 }}
    />
  </AbsoluteFill>
);

// ------------------------------------------------------------------ CauseEffect
export const CauseEffectDemo: React.FC = () => (
  <AbsoluteFill>
    <Paper color={B.colors.ground} />
    <CauseEffect
      spec={{ from: { x: 110, y: 760 }, to: { x: 262, y: 960 }, start: 10, hitAt: 44, rebound: 50 }}
      targetAt={{ x: 540, y: 960 }}
      cause={<div style={{ width: 110, height: 110, borderRadius: "50%", background: B.colors.accent }} />}
      target={<div style={{ width: 420, height: 560, borderRadius: 26, overflow: "hidden", position: "relative" }}>{fullPhoto("photos/sample-2.jpg")}</div>}
      effectFrames={30}
      effect={(p) => (
        <div
          style={{
            position: "absolute",
            left: -(150 + p * 520),
            top: -(150 + p * 520),
            width: 300 + p * 1040,
            height: 300 + p * 1040,
            borderRadius: "50%",
            border: `${Math.max(2, 22 * (1 - p))}px solid ${B.colors.accent}`,
            opacity: 1 - p,
          }}
        />
      )}
    />
  </AbsoluteFill>
);

// ------------------------------------------------------------------ Depth
const panel = (bg: string, w: number, h: number, round = 24) => (
  <div style={{ width: w, height: h, borderRadius: round, background: bg, boxShadow: "0 30px 60px -20px rgba(0,0,0,.4)" }} />
);

export const DepthDemo: React.FC = () => (
  <AbsoluteFill>
    <Paper color={B.colors.ground} />
    <DepthStage
      keys={[
        { f: 0, x: 0, y: 0, z: -300, focusZ: -400 },
        { f: 70, x: 60, y: 0, z: 100, focusZ: 300 },
        { f: 150, x: 140, y: -40, z: 700, focusZ: 1000 },
      ]}
      layers={[
        { z: 1800, x: 0, y: 0, id: "far", node: <div style={{ width: 4400, height: 6200, position: "relative", overflow: "hidden" }}>{fullPhoto("photos/sample-6.jpg")}</div> },
        { z: 1000, x: 90, y: -120, id: "mid-photo", node: <div style={{ width: 520, height: 700, borderRadius: 24, overflow: "hidden", position: "relative" }}>{fullPhoto("photos/sample-3.jpg")}</div> },
        { z: 300, x: -200, y: 160, id: "card", node: <div style={{ width: 460, height: 620, borderRadius: 24, overflow: "hidden", position: "relative" }}>{fullPhoto("photos/sample-2.jpg")}</div> },
        { z: -400, x: -380, y: -330, id: "near-a", node: panel(B.colors.accent, 260, 260, 130) },
        { z: -500, x: 420, y: 380, id: "near-b", node: panel(B.colors.accent2, 220, 220, 110) },
      ]}
    />
  </AbsoluteFill>
);

// ------------------------------------------------------------------ Entrances + Gather
const chip = (bg: string, size = 150) => (
  <div style={{ width: size, height: size, borderRadius: 28, background: bg, boxShadow: "0 18px 34px -14px rgba(0,0,0,.4)" }} />
);

export const GatherDemo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const kinds = ["rise", "drop", "slide", "pop", "swing"] as const;
  const colors = [B.colors.accent, B.colors.accent2, B.colors.ink, B.colors.soft, B.colors.accent];
  const homes = kinds.map((_, i) => ({ x: 190 + i * 175, y: 900 }));
  const target = { x: 540, y: 1300 };
  return (
    <AbsoluteFill>
      <Paper color={B.colors.ground} />
      <div style={{ position: "absolute", left: target.x - 90, top: target.y - 90, width: 180, height: 180, borderRadius: "50%", background: B.colors.paper, boxShadow: `0 0 0 6px ${B.colors.line}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
        <Img src={asset("logo.png")} style={{ width: 120 }} />
      </div>
      <Gather
        items={kinds.map((k, i) => {
          const p = entrancePose(frame, fps, 6 + i * 8, k);
          return (
            <div key={k} style={{ transform: `translate(${p.x}px, ${p.y}px) rotate(${p.r}deg) scale(${p.s * 1}, ${p.s}) scale(${p.sx}, ${p.sy})`, opacity: p.opacity }}>
              {chip(colors[i], 130)}
            </div>
          );
        })}
        spec={{ origins: homes, target, start: 70, stagger: 7, tripS: 0.7 }}
      />
    </AbsoluteFill>
  );
};

// ------------------------------------------------------------------ Silk
export const SilkDemo: React.FC = () => (
  <AbsoluteFill>
    <Paper color={B.colors.ground} />
    <Silk colors={[B.colors.accent, B.colors.accent2, B.colors.soft, B.colors.ink]} opacity={0.3} />
    <div style={{ position: "absolute", left: 140, top: 640, width: 800, height: 640, borderRadius: 30, overflow: "hidden" }}>{fullPhoto("photos/sample-2.jpg")}</div>
  </AbsoluteFill>
);
