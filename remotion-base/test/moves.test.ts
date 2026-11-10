import { describe, expect, it } from "vitest";
import {
  DAY_LIGHT,
  puffAt,
  steamPuffs,
  veilDensity,
  headTaper,
  ribbonSides,
  streamCenter,
  streamPoints,
  streamWidthAt,
  silkPath,
  silkY,
  entrancePose,
  gatherPose,
  approach,
  blurPx,
  cellRect,
  chainStarts,
  depthCameraAt,
  effectProgress,
  impactPose,
  layerOffset,
  layerScale,
  stripOffset,
  tipAngle,
  barRect,
  beltPose,
  floodAt,
  pageInPlace,
  revealInset,
  ringRadii,
  tearPose,
  wipeBar,
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

const nondec = (xs: number[]) =>
  xs.every((x, i) => i === 0 || x >= xs[i - 1] - 1e-9);
const frames = (a: number, b: number) =>
  Array.from({ length: b - a + 1 }, (_, i) => a + i);

describe("LightFlood", () => {
  const spec = { at: 30, riseS: 0.4, holdS: 0.2, drainS: 1 };
  it("is idle before the start and done after the drain", () => {
    expect(floodAt(10, FPS, spec)).toEqual({
      level: 0,
      drain: 0,
      phase: "idle",
    });
    expect(floodAt(500, FPS, spec)).toEqual({
      level: 1,
      drain: 1,
      phase: "done",
    });
  });
  it("rises to 1, holds, then drains 0 → 1, never going backwards", () => {
    const s = frames(0, 90).map((f) => floodAt(f, FPS, spec));
    expect(nondec(s.map((x) => x.level))).toBe(true);
    expect(nondec(s.map((x) => x.drain))).toBe(true);
    expect(
      s.some((x) => x.phase === "hold" && x.level === 1 && x.drain === 0),
    ).toBe(true);
    expect(s.every((x) => x.drain === 0 || x.level === 1)).toBe(true);
  });
  it("rings leave one point in order: ring 0 first and largest", () => {
    expect(ringRadii(0, 3, 1000)).toEqual([0, 0, 0]);
    for (const d of [0.2, 0.5, 0.8]) {
      const r = ringRadii(d, 3, 1000);
      expect(r[0]).toBeGreaterThanOrEqual(r[1]);
      expect(r[1]).toBeGreaterThanOrEqual(r[2]);
    }
    expect(ringRadii(1, 3, 1000)).toEqual([1000, 1000, 1000]);
    expect(
      nondec(frames(0, 20).map((i) => ringRadii(i / 20, 3, 1000)[2])),
    ).toBe(true);
  });
});

describe("Belt", () => {
  const spec = { at: 10, durS: 4, distance: 1800, rampS: 0.6, brakeS: 0.9 };
  const pose = (f: number) => beltPose(f, FPS, spec);
  it("starts at rest and stops exactly on the distance", () => {
    expect(pose(10)).toEqual({ x: 0, speed: 0, tau: 0 });
    expect(pose(10 + 4 * FPS).x).toBeCloseTo(1800, 6);
    expect(pose(10 + 4 * FPS).speed).toBeCloseTo(0, 6);
    expect(pose(999).tau).toBeCloseTo(1, 9);
  });
  it("never goes backwards, cruises at constant speed and slows with its own clock", () => {
    const xs = frames(0, 140).map((f) => pose(f).x);
    expect(nondec(xs)).toBe(true);
    const mid = [60, 61, 62].map((f) => pose(f).speed);
    expect(mid[0]).toBeCloseTo(mid[1], 9);
    expect(mid[1]).toBeCloseTo(mid[2], 9);
    const peak = Math.max(...frames(0, 140).map((f) => pose(f).speed));
    expect(peak).toBeCloseTo(mid[0], 9);
    expect(pose(10 + 4 * FPS - 3).speed).toBeLessThan(peak / 2);
  });
  it("lands on item k when distance = k * spacing", () => {
    const end = beltPose(999, FPS, { ...spec, distance: 3 * 600 });
    expect(end.x).toBe(1800);
  });
  it("refuses a profile that cannot fit in the duration", () => {
    expect(() => beltPose(0, FPS, { ...spec, durS: 1 })).toThrow();
  });
});

describe("ObjectWipe", () => {
  it("starts off-frame and ends off-frame with everything revealed", () => {
    const a = wipeBar(0, 1080, 360);
    expect(a.lead).toBe(0);
    expect(a.revealed).toBe(0);
    const z = wipeBar(1, 1080, 360);
    expect(z.trail).toBeCloseTo(1080, 6);
    expect(z.revealed).toBe(1080);
  });
  it("reveals only what the object has passed, monotonically", () => {
    const r = frames(0, 50).map((i) => wipeBar(i / 50, 1080, 360).revealed);
    expect(nondec(r)).toBe(true);
    const mid = wipeBar(0.5, 1080, 360);
    expect(mid.revealed).toBeLessThan(mid.lead);
  });
  it("places the bar and the clip for every direction", () => {
    expect(barRect("right", 400, 360, 1080, 1920)).toEqual({
      left: 40,
      top: 0,
      width: 360,
      height: 1920,
    });
    expect(barRect("left", 400, 360, 1080, 1920).left).toBe(680);
    expect(barRect("down", 400, 360, 1080, 1920).top).toBe(40);
    expect(barRect("up", 400, 360, 1080, 1920).top).toBe(1520);
    expect(revealInset("right", 300, 1080, 1920)).toBe(
      "inset(0px 780px 0px 0px)",
    );
    expect(revealInset("left", 300, 1080, 1920)).toBe(
      "inset(0px 0px 0px 780px)",
    );
    expect(revealInset("down", 300, 1080, 1920)).toBe(
      "inset(0px 0px 1620px 0px)",
    );
    expect(revealInset("up", 1920, 1080, 1920)).toBe("inset(0px 0px 0px 0px)");
  });
});

describe("Calendar", () => {
  it("keeps the page in place until it is torn", () => {
    expect(tearPose(20, FPS, 30)).toEqual({
      x: 0,
      y: 0,
      r: 0,
      opacity: 1,
      gone: false,
    });
  });
  it("lifts on its hinge, then falls and fades out", () => {
    const lift = tearPose(30 + 3, FPS, 30);
    expect(lift.r).toBeLessThan(0);
    expect(lift.opacity).toBe(1);
    const poses = frames(36, 80).map((f) => tearPose(f, FPS, 30));
    expect(nondec(poses.map((p) => p.y))).toBe(true); // falls
    expect(nondec(poses.map((p) => -p.opacity))).toBe(true); // fades
    expect(tearPose(30 + 3 * FPS, FPS, 30).gone).toBe(true);
  });
  it("tracks which page is in place", () => {
    const pages = [
      { tearAt: 30, content: null },
      { tearAt: 90, content: null },
      { content: null },
    ];
    expect(pageInPlace(0, FPS, pages)).toBe(0);
    expect(pageInPlace(60, FPS, pages)).toBe(1); // page 0 has fallen, page 1 not torn yet
    expect(pageInPlace(9999, FPS, pages)).toBe(2);
  });
});

// ------------------------------------------------------------------ FilmStrip
describe("FilmStrip", () => {
  const stops = [
    { at: 20, index: 2 },
    { at: 90, index: 3 },
  ];
  const off = (f: number) => stripOffset(f, FPS, stops, 500, 0.9);
  it("rests before the first roll and lands exactly on each cell", () => {
    expect(off(0)).toBe(0);
    expect(off(20)).toBe(0);
    expect(off(20 + 27)).toBeCloseTo(1000, 6);
    expect(off(89)).toBeCloseTo(1000, 6);
    expect(off(90 + 27)).toBeCloseTo(1500, 6);
  });
  it("never goes backwards on a forward roll and eases (slow ends, fast middle)", () => {
    expect(nondec(range(0, 130).map(off))).toBe(true);
    const v = (f: number) => off(f + 1) - off(f);
    expect(v(20)).toBeLessThan(v(33));
    expect(v(45)).toBeLessThan(v(33));
  });
  it("blends the growing frame between two rectangles", () => {
    const a = { x: 100, y: 200, w: 300, h: 400 };
    const b = { x: 0, y: 0, w: 1080, h: 1920 };
    expect(cellRect(0, a, b)).toEqual(a);
    expect(cellRect(1, a, b)).toEqual(b);
    expect(cellRect(2, a, b)).toEqual(b);
    expect(cellRect(0.5, a, b).w).toBeCloseTo(690, 9);
  });
});

// ------------------------------------------------------------------ Dominoes
describe("Dominoes", () => {
  it("stands upright, then falls flat with gravity", () => {
    expect(tipAngle(5, FPS, 10)).toBe(0);
    expect(tipAngle(10, FPS, 10)).toBe(0);
    expect(tipAngle(10 + 21, FPS, 10, { fallS: 0.7 })).toBeCloseTo(90, 9);
    expect(tipAngle(999, FPS, 10)).toBe(90);
    const mid = tipAngle(10 + 10.5, FPS, 10, { fallS: 0.7 });
    expect(mid).toBeCloseTo(22.5, 6); // half the time is a quarter of the angle
  });
  it("starts each card when the one before reaches the contact angle", () => {
    const s = chainStarts(5, 20, FPS, { fallS: 0.7, contactDeg: 22.5 });
    expect(s[0]).toBe(20);
    for (let k = 1; k < s.length; k++) {
      const a = tipAngle(s[k], FPS, s[k - 1], { fallS: 0.7 });
      expect(Math.abs(a - 22.5)).toBeLessThan(5); // within a frame of the contact
    }
    expect(nondec(s)).toBe(true);
    expect(new Set(s).size).toBe(5);
  });
  it("a harder contact angle waits longer", () => {
    const soft = chainStarts(3, 0, FPS, { contactDeg: 10 });
    const hard = chainStarts(3, 0, FPS, { contactDeg: 40 });
    expect(hard[1]).toBeGreaterThan(soft[1]);
  });
});

// ------------------------------------------------------------------ CauseEffect
describe("CauseEffect", () => {
  const spec = {
    from: { x: 0, y: 0 },
    to: { x: 400, y: 200 },
    start: 10,
    hitAt: 40,
    rebound: 40,
  };
  it("waits, accelerates into the contact and lands exactly on it", () => {
    expect(approach(0, spec)).toEqual(spec.from);
    expect(approach(40, spec)).toEqual(spec.to);
    const xs = range(10, 40).map((f) => approach(f, spec).x);
    expect(nondec(xs)).toBe(true);
    const d = (f: number) => approach(f + 1, spec).x - approach(f, spec).x;
    expect(d(35)).toBeGreaterThan(d(12)); // faster near the hit
  });
  it("rebounds a little after the contact and settles back on it", () => {
    const after = range(41, 70).map((f) => approach(f, spec).x);
    expect(Math.min(...after)).toBeLessThan(400);
    expect(Math.min(...after)).toBeGreaterThan(400 - 40);
    expect(approach(200, spec).x).toBeCloseTo(400, 6);
  });
  it("refuses a cause that hits before it starts", () => {
    expect(() => approach(0, { ...spec, hitAt: 5 })).toThrow();
  });
  it("squashes the target on the hit frame and settles", () => {
    expect(impactPose(39, FPS, 40)).toEqual({ sx: 1, sy: 1, recoil: 0 });
    const hit = impactPose(40, FPS, 40);
    expect(hit.sx).toBeGreaterThan(1);
    expect(hit.sy).toBeLessThan(1);
    expect(hit.sx * hit.sy).toBeLessThan(1.001); // volume roughly preserved
    const late = impactPose(40 + 3 * FPS, FPS, 40);
    expect(Math.abs(late.sx - 1)).toBeLessThan(0.002);
  });
  it("starts the effect on the hit frame", () => {
    expect(effectProgress(39, 40, 20)).toBe(0);
    expect(effectProgress(40, 40, 20)).toBe(0);
    expect(effectProgress(50, 40, 20)).toBeCloseTo(0.5, 9);
    expect(effectProgress(100, 40, 20)).toBe(1);
  });
});

// ------------------------------------------------------------------ Depth
describe("Depth", () => {
  it("is 1 at the focal distance, grows when nearer and shrinks when far", () => {
    expect(layerScale(0, 0)).toBe(1);
    expect(layerScale(-500, 0)).toBeCloseTo(2, 9);
    expect(layerScale(1000, 0)).toBeCloseTo(0.5, 9);
  });
  it("does not draw a layer at or behind the lens", () => {
    expect(layerScale(-900, 0)).toBe(0);
    expect(layerScale(-5000, 0)).toBe(0);
  });
  it("gives near layers more parallax than far ones for the same pan", () => {
    const near = Math.abs(layerOffset(0, 100, layerScale(-500, 0)));
    const far = Math.abs(layerOffset(0, 100, layerScale(1000, 0)));
    expect(near).toBeGreaterThan(far * 3.9);
  });
  it("blurs nothing at the focus and more the farther from it, up to a cap", () => {
    expect(blurPx(200, 0, 200)).toBe(0);
    expect(blurPx(600, 0, 200)).toBeGreaterThan(blurPx(400, 0, 200));
    expect(blurPx(9000, 0, 0, { max: 12 })).toBeLessThanOrEqual(12);
    expect(blurPx(-950, 0, 0)).toBe(0);
  });
  it("moves the camera between keys, eased, and holds the ends", () => {
    const keys = [
      { f: 10, x: 0, y: 0, z: 0, focusZ: 0 },
      { f: 70, x: 200, y: 0, z: 600, focusZ: 600 },
    ];
    expect(depthCameraAt(0, keys).z).toBe(0);
    expect(depthCameraAt(10, keys).z).toBe(0);
    expect(depthCameraAt(40, keys).z).toBeCloseTo(300, 6);
    expect(depthCameraAt(70, keys).x).toBe(200);
    expect(depthCameraAt(999, keys).focusZ).toBe(600);
    expect(() => depthCameraAt(0, [])).toThrow();
  });
});

// ------------------------------------------------------------------ Entrances
describe("Entrances", () => {
  const kinds = ["rise", "drop", "slide", "pop", "swing"] as const;
  it("are hidden before they start and exactly at rest once settled", () => {
    for (const k of kinds) {
      expect(entrancePose(5, FPS, 10, k).opacity).toBe(0);
      const end = entrancePose(10 + 4 * FPS, FPS, 10, k);
      expect(end.x).toBeCloseTo(0, 2);
      expect(end.y).toBeCloseTo(0, 2);
      expect(end.s).toBeCloseTo(1, 2);
      expect(end.r).toBeCloseTo(0, 2);
      expect(end.opacity).toBe(1);
      expect(end.sx).toBeCloseTo(1, 2);
    }
  });
  it("arrive from the side they name", () => {
    expect(entrancePose(11, FPS, 10, "rise").y).toBeGreaterThan(0);
    expect(entrancePose(11, FPS, 10, "drop").y).toBeLessThan(0);
    expect(entrancePose(11, FPS, 10, "slide", { dir: -1 }).x).toBeLessThan(0);
    expect(entrancePose(11, FPS, 10, "slide", { dir: 1 }).x).toBeGreaterThan(0);
  });
  it("a drop squashes where it lands and a pop starts from nothing", () => {
    const sq = range(10, 70).map((f) => entrancePose(f, FPS, 10, "drop").sx);
    expect(Math.max(...sq)).toBeGreaterThan(1.01);
    expect(entrancePose(10, FPS, 10, "pop").s).toBeLessThan(0.1);
  });
});

describe("gatherPose", () => {
  const spec = {
    origins: [
      { x: 0, y: 0 },
      { x: 1000, y: 0 },
      { x: 500, y: 1000 },
    ],
    target: { x: 500, y: 500 },
    start: 10,
    stagger: 6,
    tripS: 0.8,
  };
  it("starts on its origin, lands on the target, shrinking, one after another", () => {
    for (let i = 0; i < 3; i++) {
      const a = gatherPose(spec.start + i * spec.stagger, FPS, i, spec);
      expect(a.x).toBeCloseTo(spec.origins[i].x, 6);
      const z = gatherPose(999, FPS, i, spec);
      expect(z.x).toBeCloseTo(500, 6);
      expect(z.y).toBeCloseTo(500, 6);
      expect(z.s).toBeCloseTo(0.2, 9);
      expect(z.arrived).toBe(true);
    }
    expect(gatherPose(0, FPS, 0, spec).arrived).toBe(false);
    const arr = [0, 1, 2].map((i) => gatherPose(0, FPS, i, spec).arrivalFrame);
    expect(arr[1] - arr[0]).toBe(6);
    expect(arr[2] - arr[1]).toBe(6);
  });
  it("only gets closer to the target while travelling", () => {
    const d = range(10, 34).map((f) =>
      Math.hypot(
        gatherPose(f, FPS, 0, spec).x - 500,
        gatherPose(f, FPS, 0, spec).y - 500,
      ),
    );
    expect(d.every((v, i) => i === 0 || v <= d[i - 1] + 1e-9)).toBe(true);
  });
});

// ------------------------------------------------------------------ Silk
describe("Silk", () => {
  const opts = { loopFrames: 120 };
  it("is a pure function of the frame and loops exactly", () => {
    for (const x of [0, 0.25, 0.7, 1]) {
      expect(silkY(x, 1, 3, 17, opts)).toBe(silkY(x, 1, 3, 17, opts));
      expect(silkY(x, 1, 3, 17 + 120, opts)).toBeCloseTo(
        silkY(x, 1, 3, 17, opts),
        9,
      );
    }
  });
  it("stays near its band and never jumps between neighbouring frames", () => {
    for (let k = 0; k < 3; k++) {
      let prev = silkY(0.4, k, 3, 0, opts);
      for (let f = 1; f <= 120; f++) {
        const y = silkY(0.4, k, 3, f, opts);
        expect(Math.abs(y - (k + 1) / 4)).toBeLessThanOrEqual(0.0801);
        expect(Math.abs(y - prev)).toBeLessThan(0.02);
        prev = y;
      }
    }
  });
  it("keeps ribbons from crossing at the default amplitude", () => {
    for (let f = 0; f < 240; f += 7) {
      for (let k = 0; k < 2; k++)
        expect(silkY(0.3, k, 3, f)).toBeLessThan(silkY(0.3, k + 1, 3, f));
    }
  });
  it("draws a closed path from corner to corner", () => {
    const d = silkPath(1080, 1920, 0, 2, 5);
    expect(d.startsWith("M0,1920 L")).toBe(true);
    expect(d.endsWith("L1080,1920 Z")).toBe(true);
    expect(d.split("L").length).toBe(1 + 49 + 1);
  });
});

// ------------------------------------------------------------------ Stream
describe("Stream", () => {
  it("wanders: the centre line is deterministic, bounded and continuous", () => {
    const o = { cx: 540, amp: 300, wavelength: 1150 };
    for (let y = -500; y < 8000; y += 37) {
      expect(streamCenter(y, o)).toBe(streamCenter(y, o));
      expect(Math.abs(streamCenter(y, o) - 540)).toBeLessThanOrEqual(300.0001);
      expect(
        Math.abs(streamCenter(y + 1, o) - streamCenter(y, o)),
      ).toBeLessThan(2.5);
    }
  });
  it("really meanders: it crosses its own axis several times over a long course", () => {
    const pts = streamPoints(0, 6000, 40);
    let crossings = 0;
    for (let i = 1; i < pts.length; i++)
      if ((pts[i].x - 540) * (pts[i - 1].x - 540) < 0) crossings++;
    expect(crossings).toBeGreaterThanOrEqual(8);
  });
  it("samples from y0 to y1 inclusive, in order", () => {
    const pts = streamPoints(-100, 900, 40);
    expect(pts[0].y).toBe(-100);
    expect(pts[pts.length - 1].y).toBe(900);
    expect(pts.every((p, i) => i === 0 || p.y > pts[i - 1].y)).toBe(true);
  });
  it("varies in width between pools and riffles but never closes", () => {
    const ws = Array.from({ length: 400 }, (_, i) =>
      streamWidthAt(i * 20, 200),
    );
    expect(Math.max(...ws) / Math.min(...ws)).toBeGreaterThan(1.4);
    expect(Math.min(...ws)).toBeGreaterThan(80);
  });
  it("builds a ribbon whose edges stay half a width from the centre line", () => {
    const pts = [
      { x: 0, y: 0 },
      { x: 0, y: 100 },
      { x: 0, y: 200 },
    ];
    const { left, right } = ribbonSides(pts, () => 60);
    left.forEach((l, i) =>
      expect(Math.hypot(l.x - pts[i].x, l.y - pts[i].y)).toBeCloseTo(30, 9),
    );
    right.forEach((r, i) =>
      expect(Math.hypot(r.x - pts[i].x, r.y - pts[i].y)).toBeCloseTo(30, 9),
    );
    expect(left[1].x * right[1].x).toBeLessThan(0); // opposite sides
  });
  it("tapers the head to a point and is full width behind it", () => {
    expect(headTaper(0)).toBe(0);
    expect(headTaper(260)).toBe(1);
    expect(headTaper(5000)).toBe(1);
    expect(headTaper(130)).toBeCloseTo(0.5, 9);
  });
});

// ------------------------------------------------------------------ Steam
describe("Steam", () => {
  const area = { w: 1080, h: 1920 };
  it("makes the same puffs from the same seed", () => {
    expect(steamPuffs(8, "a", area)).toEqual(steamPuffs(8, "a", area));
    expect(steamPuffs(8, "a", area)).not.toEqual(steamPuffs(8, "b", area));
  });
  it("puffs rise, and wrap back below the frame instead of disappearing", () => {
    const [p] = steamPuffs(1, "rise", area);
    const a = puffAt(p, 0, 30, area);
    const b = puffAt(p, 3, 30, area);
    expect(b.y).toBeLessThan(a.y);
    for (let f = 0; f < 3000; f += 17) {
      const q = puffAt(p, f, 30, area);
      expect(q.y).toBeGreaterThanOrEqual(-p.r - 1e-6);
      expect(q.y).toBeLessThanOrEqual(area.h + p.r + 1e-6);
    }
  });
  it("the veil sits at its base and swells to its peak exactly on a change", () => {
    expect(veilDensity(0, [100])).toBeCloseTo(0.12, 9);
    expect(veilDensity(100, [100])).toBeCloseTo(0.92, 9);
    expect(veilDensity(95, [100])).toBeGreaterThan(veilDensity(90, [100]));
    expect(veilDensity(110, [100])).toBeGreaterThan(veilDensity(118, [100]));
    expect(veilDensity(130, [100])).toBeCloseTo(0.12, 9);
  });
  it("stays between base and peak with several changes", () => {
    for (let f = 0; f < 400; f++) {
      const d = veilDensity(f, [60, 120, 180], { base: 0.1, peak: 0.9 });
      expect(d).toBeGreaterThanOrEqual(0.1 - 1e-9);
      expect(d).toBeLessThanOrEqual(0.9 + 1e-9);
    }
  });
});
