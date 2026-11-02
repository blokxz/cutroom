import { describe, expect, it } from "vitest";
import {
  DAY_LIGHT,
  anchorPoint,
  arcPoint,
  archShape,
  buildPath,
  circleShape,
  coverLayout,
  doorAngle,
  dropPose,
  flipAngle,
  inkAt,
  keyTurn,
  keyTurns,
  keyholeCover,
  keyholeShape,
  gridCells,
  landingFrame,
  lightColor,
  mixShape,
  nearestLength,
  parsePath,
  pathFrame,
  postcardPose,
  rectShape,
  shapeRadius,
  squash,
  stackRest,
  windowFromPoint,
  writeSchedule,
  writingEnd,
} from "../src/moves";

const FPS = 30;
const range = (a: number, b: number) =>
  Array.from({ length: b - a + 1 }, (_, i) => a + i);

// ------------------------------------------------------------------ ArchWindow
describe("window shapes", () => {
  const arch = archShape(540, 900, 700, 980);
  const rect = rectShape(540, 960, 960, 720);
  const circle = circleShape(540, 900, 600);

  it("are centred where asked", () => {
    for (const [s, cx, cy] of [
      [arch, 540, 900],
      [rect, 540, 960],
      [circle, 540, 900],
    ] as const) {
      expect(s.x + s.w / 2).toBeCloseTo(cx, 9);
      expect(s.y + s.h / 2).toBeCloseTo(cy, 9);
    }
    expect(arch.rt).toBe(350);
    expect(circle.rt).toBe(circle.rb);
  });

  it("mixShape hits both ends and the midpoint", () => {
    expect(mixShape(arch, rect, 0)).toEqual(arch);
    expect(mixShape(arch, rect, 1)).toEqual(rect);
    const m = mixShape(arch, circle, 0.5);
    expect(m.w).toBeCloseTo((arch.w + circle.w) / 2, 9);
    expect(m.rt).toBeCloseTo((arch.rt + circle.rt) / 2, 9);
  });

  it("shapeRadius never exceeds half the box", () => {
    expect(shapeRadius({ x: 0, y: 0, w: 100, h: 40, rt: 90, rb: 5 })).toBe(
      "20px 20px 5px 5px",
    );
    expect(shapeRadius({ x: 0, y: 0, w: -4, h: 10, rt: 3, rb: 3 })).toBe(
      "0px 0px 0px 0px",
    );
  });

  it("windowFromPoint starts as a small arch on the point and ends on the target", () => {
    const pt = { x: 300, y: 700 };
    const s0 = windowFromPoint(pt, rect, 0);
    expect(s0.x + s0.w / 2).toBeCloseTo(300, 9);
    expect(s0.y + s0.h / 2).toBeCloseTo(700, 9);
    expect(s0.w).toBe(90);
    expect(s0.rt).toBe(45);
    expect(windowFromPoint(pt, rect, 1)).toEqual(rect);
    expect(windowFromPoint(pt, rect, 0, 0).w).toBe(0);
  });
});

describe("coverLayout", () => {
  const photo = { w: 730, h: 540 };
  const frame = { w: 700, h: 980 };

  it("covers the frame at zoom 1", () => {
    const L = coverLayout(photo, frame, [0.5, 0.5]);
    expect(L.ox).toBeLessThanOrEqual(1e-9);
    expect(L.oy).toBeLessThanOrEqual(1e-9);
    expect(L.ox + photo.w * L.s).toBeGreaterThanOrEqual(frame.w - 1e-9);
    expect(L.oy + photo.h * L.s).toBeGreaterThanOrEqual(frame.h - 1e-9);
  });

  it("never shows an edge, even with an extreme focus", () => {
    for (const f of [
      [0, 0],
      [1, 1],
      [0.1, 0.9],
    ] as [number, number][]) {
      const L = coverLayout(photo, frame, f);
      expect(L.ox).toBeLessThanOrEqual(1e-9);
      expect(L.ox + photo.w * L.s).toBeGreaterThanOrEqual(frame.w - 1e-9);
    }
  });

  it("keeps the anchor fixed while zooming", () => {
    const a = coverLayout(photo, frame, [0.4, 0.5], [0.7, 0.6], 1);
    for (const z of [1.2, 2, 3.5]) {
      const b = coverLayout(photo, frame, [0.4, 0.5], [0.7, 0.6], z);
      expect(b.ax).toBeCloseTo(a.ax, 9);
      expect(b.ay).toBeCloseTo(a.ay, 9);
      // the anchor's photo pixel lands on (ax, ay)
      expect(b.ox + 0.7 * photo.w * b.s).toBeCloseTo(a.ax, 9);
      expect(b.oy + 0.6 * photo.h * b.s).toBeCloseTo(a.ay, 9);
      expect(b.s).toBeCloseTo(a.s * z, 9);
    }
  });

  it("anchorPoint is the anchor in screen coordinates", () => {
    const shape = archShape(540, 900, 700, 980);
    const p = anchorPoint(shape, {
      src: "",
      ...photo,
      focus: [0.5, 0.5],
      anchor: [0.5, 0.5],
    });
    expect(p.x).toBeCloseTo(540, 6);
    expect(p.y).toBeCloseTo(900, 6);
  });
});

// ------------------------------------------------------------------ PostcardDrop
describe("postcards", () => {
  const table = { x: 540, y: 900 };

  it("stackRest is deterministic, scattered and alternates its tilt", () => {
    const rs = range(0, 7).map((k) => stackRest(k, table));
    expect(rs).toEqual(range(0, 7).map((k) => stackRest(k, table)));
    rs.forEach((r, k) => {
      expect(Math.abs(r.x - table.x)).toBeLessThanOrEqual(26);
      expect(Math.abs(r.y - table.y)).toBeLessThanOrEqual(18);
      expect(Math.sign(r.r)).toBe(k % 2 ? -1 : 1);
      expect(Math.abs(r.r)).toBeLessThanOrEqual(4.5);
    });
  });

  it("squash is neutral before impact and wobbles back to 1, keeping the area close", () => {
    expect(squash(9, FPS, 10)).toEqual({ sx: 1, sy: 1 });
    const at = squash(10, FPS, 10, 0.04);
    expect(at.sx).toBeCloseTo(1.04, 9);
    expect(at.sy).toBeCloseTo(0.96, 9);
    const late = squash(60, FPS, 10);
    expect(Math.abs(late.sx - 1)).toBeLessThan(1e-3);
  });

  it("dropPose falls from above, touches down, and settles on its rest", () => {
    const rest = stackRest(0, table);
    const start = 12;
    expect(dropPose(start - 1, FPS, start, rest).visible).toBe(false);
    const p0 = dropPose(start, FPS, start, rest);
    expect(p0.y).toBeCloseTo(-700, 6);
    const touch = start + landingFrame(FPS);
    expect(landingFrame(FPS)).toBeGreaterThan(3);
    expect(landingFrame(FPS)).toBeLessThan(30);
    const pt = dropPose(touch, FPS, start, rest);
    expect(pt.sx).toBeGreaterThan(1); // squashing on impact
    const end = dropPose(start + 90, FPS, start, rest);
    expect(end.x).toBeCloseTo(rest.x, 1);
    expect(end.y).toBeCloseTo(rest.y, 0);
    expect(end.r).toBeCloseTo(rest.r, 1);
  });

  it("gridCells stay inside the area and centre an incomplete last row", () => {
    const area = { x: 60, y: 300, w: 960, h: 720 };
    const cells = gridCells(5, area, 3, 20);
    expect(cells).toHaveLength(5);
    for (const c of cells) {
      expect(c.x - c.w / 2).toBeGreaterThanOrEqual(area.x - 1e-9);
      expect(c.x + c.w / 2).toBeLessThanOrEqual(area.x + area.w + 1e-9);
      expect(c.y - c.h / 2).toBeGreaterThanOrEqual(area.y - 1e-9);
      expect(c.y + c.h / 2).toBeLessThanOrEqual(area.y + area.h + 1e-9);
    }
    const lastRowMid = (cells[3].x + cells[4].x) / 2;
    expect(lastRowMid).toBeCloseTo(area.x + area.w / 2, 9);
  });

  it("postcardPose ends in its grid cell, upright and scaled to fit", () => {
    const starts = [0, 20, 40];
    const card = { w: 600, h: 760 };
    const cells = gridCells(3, { x: 60, y: 300, w: 960, h: 600 }, 3);
    for (const k of [0, 1, 2]) {
      const p = postcardPose(400, FPS, k, starts, {
        table,
        card,
        gridAt: 200,
        cells,
      });
      expect(p.x).toBeCloseTo(cells[k].x, 0);
      expect(p.y).toBeCloseTo(cells[k].y, 0);
      expect(Math.abs(p.r)).toBeLessThan(0.05);
      expect(p.s).toBeCloseTo(
        Math.min(cells[k].w / card.w, cells[k].h / card.h),
        2,
      );
    }
  });

  it("later cards nudge earlier ones", () => {
    const opts = { table, card: { w: 600, h: 760 } };
    const alone = postcardPose(150, FPS, 0, [0], opts);
    const nudged = postcardPose(150, FPS, 0, [0, 30], opts);
    expect(Math.abs(nudged.x - alone.x)).toBeGreaterThan(20);
  });
});

// ------------------------------------------------------------------ LightArc
describe("light arc", () => {
  const arc = { x0: 150, x1: 930, y: 640, lift: 300 };

  it("starts and ends on the baseline and peaks in the middle", () => {
    expect(arcPoint(arc, 0)).toEqual({ x: 150, y: 640 });
    const end = arcPoint(arc, 1);
    expect(end.x).toBe(930);
    expect(end.y).toBeCloseTo(640, 9);
    const mid = arcPoint(arc, 0.5);
    expect(mid.x).toBe(540);
    expect(mid.y).toBeCloseTo(340, 9);
    const ys = range(0, 50).map((i) => arcPoint(arc, i / 100).y);
    expect(ys.every((y, i) => i === 0 || y <= ys[i - 1] + 1e-9)).toBe(true);
  });

  it("lightColor passes through each stop", () => {
    const rgb = (h: string) =>
      `rgba(${[1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16)).join(", ")}, 1)`;
    DAY_LIGHT.forEach((c, i) => {
      expect(lightColor(i / (DAY_LIGHT.length - 1))).toBe(rgb(c));
    });
    expect(lightColor(-1)).toBe(lightColor(0));
    expect(lightColor(2)).toBe(lightColor(1));
    expect(lightColor(0.3, ["#112233"])).toBe("#112233");
  });
});

// ------------------------------------------------------------------ PathCamera
describe("path math", () => {
  it("parses absolute and relative commands into the same segments", () => {
    const a = parsePath("M 10 20 L 110 20 V 120 H 10 Z");
    const b = parsePath("m10,20 l100,0 v100 h-100 z");
    expect(a).toEqual(b);
    expect(a).toHaveLength(4);
  });

  it("rejects unsupported commands", () => {
    expect(() => parsePath("M0 0 A 5 5 0 0 1 10 10")).toThrow();
  });

  it("measures a polyline exactly", () => {
    const p = buildPath("M0 0 L300 0 L300 400");
    expect(p.length).toBeCloseTo(700, 9);
    expect(p.at(0)).toMatchObject({ x: 0, y: 0, angle: 0 });
    expect(p.at(150)).toMatchObject({ x: 150, y: 0 });
    expect(p.at(500)).toMatchObject({ x: 300, y: 200, angle: 90 });
    expect(p.at(9999)).toMatchObject({ x: 300, y: 400 });
    expect(p.at(-5)).toMatchObject({ x: 0, y: 0 });
  });

  it("measures curves close to their true length", () => {
    // a quarter circle approximated by a cubic: length ≈ π r / 2
    const r = 500;
    const k = 0.5522847498 * r;
    const p = buildPath(`M ${r} 0 C ${r} ${k} ${k} ${r} 0 ${r}`);
    expect(p.length).toBeCloseTo((Math.PI * r) / 2, 0);
    const end = p.at(p.length);
    expect(end.x).toBeCloseTo(0, 6);
    expect(end.y).toBeCloseTo(r, 6);
  });

  it("moves forward monotonically along the path", () => {
    const p = buildPath("M100 100 Q 600 0 500 500");
    const cum = range(0, 100).map((i) =>
      nearestLength(p, p.at((p.length * i) / 100)),
    );
    cum.forEach((c, i) => expect(c).toBeCloseTo((p.length * i) / 100, 0));
  });

  it("pathFrame puts the path point on the requested screen point", () => {
    const p = buildPath("M0 0 L1000 500");
    const f = pathFrame(p, p.length / 2, 1.5, { x: 540, y: 960 });
    expect(f.tx + f.point.x * f.z).toBeCloseTo(540, 9);
    expect(f.ty + f.point.y * f.z).toBeCloseTo(960, 9);
  });

  it("is deterministic", () => {
    const d = "M0 0 C 200 -100 400 300 600 100 Q 800 0 900 400";
    expect(buildPath(d).at(321)).toEqual(buildPath(d).at(321));
  });
});

// ------------------------------------------------------------------ Key
describe("key turn", () => {
  it("slides in, then turns a quarter and clicks", () => {
    const before = keyTurn(0, FPS, 10);
    expect(before.insert).toBe(0);
    expect(before.angle).toBe(0);
    const end = keyTurn(90, FPS, 10);
    expect(end.insert).toBeCloseTo(1, 2);
    expect(end.angle).toBeCloseTo(90, 0);
    expect(end.clicked).toBe(true);
  });

  it("overshoots a little before settling (the click)", () => {
    const peak = Math.max(
      ...range(10, 80).map((f) => keyTurn(f, FPS, 10).angle),
    );
    expect(peak).toBeGreaterThan(90);
    expect(peak).toBeLessThan(105);
  });

  it("adds up across several turns and reports the turn in progress", () => {
    const s = keyTurns(200, FPS, [0, 60, 120]);
    expect(s.angle).toBeCloseTo(270, 0);
    expect(s.k).toBe(2);
    expect(keyTurns(70, FPS, [0, 60, 120]).k).toBe(1);
    expect(keyTurns(-5, FPS, [0, 60]).k).toBe(-1);
  });
});

describe("keyhole", () => {
  it("is a closed path centred on its head", () => {
    const d = keyholeShape(540, 960, 20);
    expect(d.startsWith("M ")).toBe(true);
    expect(d.trim().endsWith("Z")).toBe(true);
    // the foot of the slot sits 2.2 head radii below the centre
    expect(d).toContain(`L ${540 + 14} ${960 + 44}`);
  });

  it("covers every corner of the frame at full size", () => {
    for (const [cx, cy] of [
      [540, 960],
      [100, 200],
      [1000, 1800],
    ]) {
      const r = keyholeCover(cx, cy, 1080, 1920);
      for (const [x, y] of [
        [0, 0],
        [1080, 0],
        [0, 1920],
        [1080, 1920],
      ])
        expect(Math.hypot(x - cx, y - cy)).toBeLessThanOrEqual(r);
    }
  });

  it("door angle is shut at 0 and open at 1", () => {
    expect(doorAngle(0)).toBe(0);
    expect(doorAngle(1)).toBe(105);
    expect(doorAngle(-1)).toBe(0);
  });
});

// ------------------------------------------------------------------ WrittenPostcard
describe("handwriting schedule", () => {
  const text = "Hola, ma:\nel mate";
  const s = writeSchedule(text, { start: 10, fps: FPS, cps: 10 });

  it("has one stroke per character, in order, starting on time", () => {
    expect(s.map((c) => c.ch).join("")).toBe(text);
    expect(s[0].start).toBe(10);
    for (let k = 1; k < s.length; k++)
      expect(s[k].start).toBeGreaterThanOrEqual(s[k - 1].start + s[k - 1].dur);
  });

  it("pauses after punctuation and moves to the next line on \\n", () => {
    const comma = s.findIndex((c) => c.ch === ",");
    expect(
      s[comma + 1].start - (s[comma].start + s[comma].dur),
    ).toBeGreaterThan(0);
    const nl = s.findIndex((c) => c.ch === "\n");
    expect(s[nl + 1].line).toBe(1);
    expect(s[0].line).toBe(0);
  });

  it("wide letters take longer than narrow ones", () => {
    const m = s.find((c) => c.ch === "m")!;
    const l = s.find((c) => c.ch === "l")!;
    expect(m.dur).toBeGreaterThan(l.dur);
  });

  it("ink goes 0 → 1 across each stroke and the end is the last stroke", () => {
    const k = 1;
    expect(inkAt(s[k].start - 1, s, k)).toBe(0);
    expect(inkAt(s[k].start + s[k].dur, s, k)).toBe(1);
    const end = writingEnd(s);
    expect(end).toBeCloseTo(s[s.length - 1].start + s[s.length - 1].dur, 5);
    expect(s.every((_, i) => inkAt(end, s, i) === 1)).toBe(true);
  });

  it("is faster at a higher rate", () => {
    const slow = writingEnd(writeSchedule(text, { cps: 8 }));
    const fast = writingEnd(writeSchedule(text, { cps: 16 }));
    expect(fast).toBeLessThan(slow);
  });
});

describe("postcard flip", () => {
  it("starts on the back and lands on the front", () => {
    expect(flipAngle(0, FPS, 10)).toBe(0);
    expect(flipAngle(10 + 3 * FPS, FPS, 10)).toBeCloseTo(180, 0);
  });
});
