/**
 * PostcardDrop — postcards that fall onto a table, land with a squash and a
 * settle, stack with a slight rotation (each new card nudges the ones below),
 * and can resolve into a tidy grid.
 *
 * Pure, frame-driven pieces (the caller picks the start frames):
 *   stackRest(k, table)         resting place of card k on the pile (seeded scatter)
 *   squash(frame, fps, at)      landing squash: a quick decaying wobble of scale x/y
 *   landingFrame(fps, opts)     frames from the drop start to the first touch
 *   dropPose(frame, fps, start, rest)     one card falling onto its rest
 *   gridCells(n, area, cols, gap)         centred cells for the final grid
 *   postcardPose(frame, fps, k, starts, opts)  full pose: drop + nudges + grid
 *   <PostcardDrop>              renders a set of cards with the brand's paper and type
 */
import React from "react";
import { Img, random, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { Brand } from "../lib/brand";
import { Track } from "../components/Track";

export type CardRest = { x: number; y: number; r: number };
export type CardPose = {
  x: number;
  y: number;
  r: number;
  sx: number;
  sy: number;
  /** extra uniform scale (1 on the pile, < 1 in the grid) */
  s: number;
  visible: boolean;
};

/** Resting place of card k on a pile centred on `table`: alternating tilt, seeded scatter. */
export const stackRest = (
  k: number,
  table: { x: number; y: number },
  seed = "stack",
  spread = { x: 26, y: 18, r: 4.5 },
): CardRest => {
  const dir = k % 2 ? -1 : 1;
  return {
    x: table.x + (random(`${seed}x${k}`) * 2 - 1) * spread.x,
    y: table.y + (random(`${seed}y${k}`) * 2 - 1) * spread.y,
    r: dir * (spread.r * (0.45 + 0.55 * random(`${seed}r${k}`))),
  };
};

/** Landing squash after an impact at frame `at`: wider and shorter, wobbling back to 1. */
export const squash = (
  frame: number,
  fps: number,
  at: number,
  amount = 0.04,
  decay = 9,
  omega = 26,
) => {
  if (frame < at) return { sx: 1, sy: 1 };
  const t = (frame - at) / fps;
  const k = amount * Math.exp(-decay * t) * Math.cos(omega * t);
  return { sx: 1 + k, sy: 1 - k };
};

const DROP = { damping: 15, stiffness: 140, mass: 0.8 };

const fall = (frame: number, fps: number, start: number) =>
  spring({ frame: frame - start, fps, config: DROP });

/** Frames from the drop start until the card first touches its rest (spring reaches 1). */
export const landingFrame = (fps: number, maxFrames = 90) => {
  for (let f = 0; f <= maxFrames; f++) if (fall(f, fps, 0) >= 1) return f;
  return maxFrames;
};

/** One card falling from above onto `rest`, swinging in from the side, squashing on impact. */
export const dropPose = (
  frame: number,
  fps: number,
  start: number,
  rest: CardRest,
  opts: { fromY?: number; swing?: number; dir?: 1 | -1 } = {},
): CardPose => {
  const { fromY = -700, swing = 16, dir = 1 } = opts;
  const f = fall(frame, fps, start);
  const sq = squash(frame, fps, start + landingFrame(fps));
  return {
    x: rest.x + dir * 40 * (1 - f),
    y: fromY + (rest.y - fromY) * f,
    r: rest.r + dir * swing * (1 - f),
    sx: sq.sx,
    sy: sq.sy,
    s: 1,
    visible: frame >= start,
  };
};

export type Cell = { x: number; y: number; w: number; h: number };

/** n cells (centres + size) filling `area` in `cols` columns; an incomplete last row is centred. */
export const gridCells = (
  n: number,
  area: { x: number; y: number; w: number; h: number },
  cols: number,
  gap = 22,
): Cell[] => {
  const rows = Math.max(1, Math.ceil(n / cols));
  const w = (area.w - (cols - 1) * gap) / cols;
  const h = (area.h - (rows - 1) * gap) / rows;
  return Array.from({ length: n }, (_, k) => {
    const row = Math.floor(k / cols);
    const inRow = Math.min(cols, n - row * cols);
    const off = ((cols - inRow) * (w + gap)) / 2;
    return {
      x: area.x + off + (k % cols) * (w + gap) + w / 2,
      y: area.y + row * (h + gap) + h / 2,
      w,
      h,
    };
  });
};

/**
 * Pose of card k: it drops at starts[k] onto its pile rest, later cards nudge it
 * aside a little, and from `gridAt` (staggered per card) it springs into its cell,
 * scaled to fit `card` into the cell.
 */
export const postcardPose = (
  frame: number,
  fps: number,
  k: number,
  starts: number[],
  opts: {
    table: { x: number; y: number };
    card: { w: number; h: number };
    gridAt?: number;
    cells?: Cell[];
    nudge?: number;
    seed?: string;
  },
): CardPose => {
  const dir = k % 2 ? -1 : 1;
  const rest = stackRest(k, opts.table, opts.seed);
  const p = dropPose(frame, fps, starts[k], rest, { dir });
  const nudge = opts.nudge ?? 30;
  for (let j = k + 1; j < starts.length; j++) {
    const n = spring({
      frame: frame - starts[j] - landingFrame(fps),
      fps,
      config: { damping: 13, stiffness: 120 },
    });
    const dj = j % 2 ? -1 : 1;
    p.x += dj * nudge * n;
    p.y -= nudge * 0.33 * n;
    p.r += dj * 1.1 * n;
  }
  if (opts.gridAt !== undefined && opts.cells && frame >= opts.gridAt) {
    const c = opts.cells[k];
    const u = spring({
      frame: frame - opts.gridAt - 2 * k,
      fps,
      config: { damping: 14, stiffness: 120 },
    });
    const fit = Math.min(c.w / opts.card.w, c.h / opts.card.h);
    p.x += (c.x - p.x) * u;
    p.y += (c.y - p.y) * u;
    p.r *= 1 - Math.min(1, u);
    p.s = 1 + (fit - 1) * u;
  }
  return p;
};

export type PostcardSpec = {
  src: string;
  /** frame the card starts falling */
  at: number;
  caption?: string;
  /** object-position of the photo, 0–1 */
  focus?: [number, number];
};

export const PostcardDrop: React.FC<{
  cards: PostcardSpec[];
  brand: Brand;
  table: { x: number; y: number };
  card?: { w: number; h: number; pad: number; foot: number };
  gridAt?: number;
  grid?: {
    area: { x: number; y: number; w: number; h: number };
    cols: number;
    gap?: number;
  };
  /** track each card as `${trackPrefix}-${k}` */
  trackPrefix?: string;
  blurred?: boolean;
}> = ({
  cards,
  brand,
  table,
  card = { w: 620, h: 780, pad: 28, foot: 120 },
  gridAt,
  grid,
  trackPrefix,
  blurred = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const starts = cards.map((c) => c.at);
  const cells = grid
    ? gridCells(cards.length, grid.area, grid.cols, grid.gap)
    : undefined;
  return (
    <>
      {cards.map((c, k) => {
        const p = postcardPose(frame, fps, k, starts, {
          table,
          card,
          gridAt,
          cells,
        });
        if (!p.visible) return null;
        const capOp = gridAt !== undefined && frame >= gridAt ? 0 : 1;
        const node = (
          <div
            style={{
              position: "absolute",
              left: p.x - card.w / 2,
              top: p.y - card.h / 2,
              width: card.w,
              height: card.h,
              background: brand.colors.paper,
              boxShadow: "0 22px 40px -18px rgba(50, 40, 30, 0.45)",
              transform: `rotate(${p.r}deg) scale(${p.sx * p.s}, ${p.sy * p.s})`,
            }}
          >
            <Img
              src={c.src}
              style={{
                position: "absolute",
                left: card.pad,
                top: card.pad,
                width: card.w - 2 * card.pad,
                height: card.h - card.pad - card.foot,
                objectFit: "cover",
                objectPosition: c.focus
                  ? `${c.focus[0] * 100}% ${c.focus[1] * 100}%`
                  : "center",
              }}
            />
            {c.caption ? (
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  bottom: card.foot * 0.28,
                  textAlign: "center",
                  fontFamily: brand.fonts.display,
                  fontStyle: "italic",
                  fontSize: 52,
                  color: brand.colors.ink,
                  opacity: capOp,
                }}
              >
                {c.caption}
              </div>
            ) : null}
          </div>
        );
        return trackPrefix ? (
          <Track
            key={k}
            id={`${trackPrefix}-${k}`}
            kind="image"
            blurred={blurred}
          >
            {node}
          </Track>
        ) : (
          <React.Fragment key={k}>{node}</React.Fragment>
        );
      })}
    </>
  );
};
