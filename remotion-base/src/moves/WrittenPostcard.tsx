/**
 * WrittenPostcard — the back of a postcard fills with handwriting, a photo lands
 * as the stamp, and the card flips over to show the place.
 *
 * Pure, frame-driven pieces (the caller picks the start frames):
 *   writeSchedule(text, opts)        when each character is written: start + duration
 *                                    in frames, weighted by letter width, pausing
 *                                    between words, after punctuation and at line ends
 *   inkAt(frame, schedule, k)        how much of character k is written (0 → 1)
 *   writingEnd(schedule)             frame the last stroke ends
 *   flipAngle(frame, fps, start)     0 → 180 degrees with a soft landing
 *   <Handwriting>   text that writes itself left to right, letter by letter
 *   <Stamp>         a photo with perforated edges and an optional postmark
 *   <Postcard>      a two-sided card (back: writing + stamp + address lines;
 *                   front: the photo) turned by a flip angle
 */
import React from "react";
import { Img, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Track } from "../components/Track";

export type Stroke = { ch: string; start: number; dur: number; line: number };

/** Rough relative widths of script letters (1 = an average lowercase letter). */
const width = (ch: string) => {
  if (/\s/.test(ch)) return 0;
  if (/[il.,'’:;!|]/.test(ch)) return 0.45;
  if (/[mwMW]/.test(ch)) return 1.5;
  if (/[A-ZÁÉÍÓÚÑ]/.test(ch)) return 1.35;
  return 1;
};

/**
 * Schedule each character of `text` (lines split on "\n"), starting at `start`.
 *   cps        average lowercase letters per second
 *   wordGap    frames of pause between words
 *   punctGap   extra frames after , . ! ? :
 *   lineGap    frames to lift the pen and move to the next line
 */
export const writeSchedule = (
  text: string,
  opts: {
    start?: number;
    fps?: number;
    cps?: number;
    wordGap?: number;
    punctGap?: number;
    lineGap?: number;
  } = {},
): Stroke[] => {
  const {
    start = 0,
    fps = 30,
    cps = 11,
    wordGap = 3,
    punctGap = 6,
    lineGap = 8,
  } = opts;
  const unit = fps / cps;
  const out: Stroke[] = [];
  let t = start;
  let line = 0;
  for (const ch of Array.from(text)) {
    if (ch === "\n") {
      out.push({ ch, start: t, dur: 0, line });
      t += lineGap;
      line++;
      continue;
    }
    if (/\s/.test(ch)) {
      out.push({ ch, start: t, dur: 0, line });
      t += wordGap;
      continue;
    }
    const dur = width(ch) * unit;
    out.push({ ch, start: t, dur, line });
    t += dur;
    if (/[,.!?:;]/.test(ch)) t += punctGap;
  }
  return out;
};

export const writingEnd = (s: Stroke[]) =>
  s.length ? Math.max(...s.map((c) => c.start + c.dur)) : 0;

export const inkAt = (frame: number, s: Stroke[], k: number) => {
  const c = s[k];
  if (!c) return 0;
  if (c.dur <= 0) return frame >= c.start ? 1 : 0;
  return Math.max(0, Math.min(1, (frame - c.start) / c.dur));
};

/** Flip angle 0 → 180 starting at `start`; a firm spring with a hint of overshoot. */
export const flipAngle = (frame: number, fps: number, start: number) =>
  180 *
  spring({
    frame: frame - start,
    fps,
    config: { damping: 16, stiffness: 90, mass: 1 },
  });

// ------------------------------------------------------------------ Handwriting
/**
 * Text that writes itself. Each character is wiped in left → right with a soft
 * edge (the ink front), so connected script letters read as one stroke. The
 * glyph box is padded so swashes are never clipped.
 */
export const Handwriting: React.FC<{
  text: string;
  start: number;
  font: string;
  size: number;
  color: string;
  cps?: number;
  lineHeight?: number;
  style?: React.CSSProperties;
  trackId?: string;
  blurred?: boolean;
}> = ({
  text,
  start,
  font,
  size,
  color,
  cps,
  lineHeight = 1.25,
  style,
  trackId,
  blurred = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const sched = writeSchedule(text, { start, fps, cps });
  const soft = 35; // % of the glyph box taken by the soft ink front
  const node = (
    <div
      style={{
        fontFamily: font,
        fontSize: size,
        lineHeight,
        color,
        whiteSpace: "pre-wrap",
        ...style,
      }}
    >
      {sched.map((c, k) => {
        if (c.ch === "\n") return <br key={k} />;
        if (/\s/.test(c.ch)) return <span key={k}>{c.ch}</span>;
        const p = inkAt(frame, sched, k);
        const edge = -soft + p * (100 + soft);
        return (
          <span
            key={k}
            style={{
              padding: "0.45em 0.3em",
              margin: "-0.45em -0.3em",
              color: "transparent",
              backgroundImage: `linear-gradient(90deg, ${color} ${edge}%, transparent ${edge + soft}%)`,
              WebkitBackgroundClip: "text",
              backgroundClip: "text",
            }}
          >
            {c.ch}
          </span>
        );
      })}
    </div>
  );
  return trackId ? (
    <Track id={trackId} kind="text" blurred={blurred}>
      {node}
    </Track>
  ) : (
    node
  );
};

// ------------------------------------------------------------------ Stamp
/** Perforated-edge mask: a row of round bites along every side. */
const perforation = (tooth: number) => {
  const r = tooth / 2;
  const bite = `radial-gradient(circle at center, transparent ${r * 0.62}px, #000 ${r * 0.66}px)`;
  return {
    WebkitMaskImage: `${bite}, linear-gradient(#000, #000)`,
    WebkitMaskSize: `${tooth}px ${tooth}px, calc(100% - ${tooth}px) calc(100% - ${tooth}px)`,
    WebkitMaskPosition: `${-r}px ${-r}px, center`,
    WebkitMaskRepeat: "repeat, no-repeat",
    WebkitMaskComposite: "source-over",
    maskImage: `${bite}, linear-gradient(#000, #000)`,
    maskSize: `${tooth}px ${tooth}px, calc(100% - ${tooth}px) calc(100% - ${tooth}px)`,
    maskPosition: `${-r}px ${-r}px, center`,
    maskRepeat: "repeat, no-repeat",
    maskComposite: "add",
  } as React.CSSProperties;
};

/**
 * A photo stamp: paper border with perforated edges, the photo inside, and an
 * optional circular postmark (`mark`, e.g. the town) overlapping its corner.
 */
export const Stamp: React.FC<{
  src: string;
  w: number;
  h: number;
  paper: string;
  ink: string;
  font?: string;
  mark?: string;
  /** 0 → 1: postmark inked */
  markP?: number;
  focus?: [number, number];
  style?: React.CSSProperties;
}> = ({ src, w, h, paper, ink, font, mark, markP = 1, focus, style }) => {
  const tooth = Math.max(10, Math.round(w / 11));
  const pad = tooth * 0.9;
  const R = w * 0.42;
  return (
    <div
      style={{
        position: "absolute",
        width: w,
        height: h,
        filter: "drop-shadow(0 4px 6px rgba(50,40,30,0.25))",
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 0,
          background: paper,
          ...perforation(tooth),
        }}
      >
        <Img
          src={src}
          style={{
            position: "absolute",
            left: pad,
            top: pad,
            width: w - 2 * pad,
            height: h - 2 * pad,
            objectFit: "cover",
            objectPosition: focus
              ? `${focus[0] * 100}% ${focus[1] * 100}%`
              : "center",
          }}
        />
      </div>
      {mark ? (
        <svg
          width={2 * R}
          height={2 * R}
          viewBox={`0 0 ${2 * R} ${2 * R}`}
          style={{
            position: "absolute",
            left: -R * 0.9,
            top: h - R * 1.1,
            opacity: 0.8 * Math.max(0, Math.min(1, markP)),
            transform: `rotate(-14deg) scale(${1.15 - 0.15 * markP})`,
            overflow: "visible",
          }}
        >
          <defs>
            <path
              id={`pm-${mark}`}
              d={`M ${R * 0.28} ${R} A ${R * 0.72} ${R * 0.72} 0 1 1 ${R * 1.72} ${R}`}
            />
          </defs>
          <circle
            cx={R}
            cy={R}
            r={R * 0.92}
            fill="none"
            stroke={ink}
            strokeWidth={R * 0.05}
          />
          <circle
            cx={R}
            cy={R}
            r={R * 0.55}
            fill="none"
            stroke={ink}
            strokeWidth={R * 0.035}
          />
          <text
            fill={ink}
            fontFamily={font}
            fontSize={R * 0.2}
            letterSpacing={R * 0.03}
          >
            <textPath
              href={`#pm-${mark}`}
              startOffset="50%"
              textAnchor="middle"
            >
              {mark.toUpperCase()}
            </textPath>
          </text>
          {[0, 1, 2].map((i) => (
            <path
              key={i}
              d={`M ${R * 1.9} ${R * (0.7 + i * 0.3)} q ${R * 0.35} ${-R * 0.12} ${R * 0.7} 0 t ${R * 0.7} 0`}
              fill="none"
              stroke={ink}
              strokeWidth={R * 0.035}
            />
          ))}
        </svg>
      ) : null}
    </div>
  );
};

// ------------------------------------------------------------------ Postcard
/**
 * A two-sided postcard centred on (x, y). `angle` (0 → 180) turns it about its
 * vertical axis: 0 shows the back (`back`), 180 the front (`front`). The back
 * gets the classic layout for free: a divider and address lines on the right.
 */
export const Postcard: React.FC<{
  x: number;
  y: number;
  w: number;
  h: number;
  angle: number;
  paper: string;
  line: string;
  /** extra in-plane tilt, degrees */
  tilt?: number;
  scale?: number;
  back?: React.ReactNode;
  front?: React.ReactNode;
  /** draw the divider and address lines on the back */
  layout?: boolean;
  trackId?: string;
  blurred?: boolean;
}> = ({
  x,
  y,
  w,
  h,
  angle,
  paper,
  line,
  tilt = 0,
  scale = 1,
  back,
  front,
  layout = true,
  trackId,
  blurred = false,
}) => {
  const lift = Math.sin((Math.min(180, Math.max(0, angle)) * Math.PI) / 180);
  const face: React.CSSProperties = {
    position: "absolute",
    inset: 0,
    backfaceVisibility: "hidden",
    WebkitBackfaceVisibility: "hidden",
    background: paper,
    overflow: "hidden",
    // a filter on the turning parent would flatten the 3D, so each face casts its own shadow
    boxShadow: `0 ${22 + 30 * lift}px ${44 + 20 * lift}px -18px rgba(50,40,30,${0.45 - 0.1 * lift})`,
  };
  const node = (
    <div
      style={{
        position: "absolute",
        left: x - w / 2,
        top: y - h / 2,
        width: w,
        height: h,
        transformStyle: "preserve-3d",
        transform: `perspective(${w * 3}px) rotate(${tilt}deg) scale(${scale * (1 + 0.06 * lift)}) rotateY(${angle}deg)`,
      }}
    >
      <div style={face}>
        {layout ? (
          <>
            <div
              style={{
                position: "absolute",
                left: w * 0.56,
                top: h * 0.12,
                width: 2,
                height: h * 0.76,
                background: line,
              }}
            />
            {[0.52, 0.64, 0.76].map((t) => (
              <div
                key={t}
                style={{
                  position: "absolute",
                  left: w * 0.61,
                  width: w * 0.33,
                  top: h * t,
                  height: 2,
                  background: line,
                }}
              />
            ))}
          </>
        ) : null}
        {back}
      </div>
      <div style={{ ...face, transform: "rotateY(180deg)" }}>{front}</div>
    </div>
  );
  return trackId ? (
    <Track id={trackId} kind="image" blurred={blurred}>
      {node}
    </Track>
  ) : (
    node
  );
};
