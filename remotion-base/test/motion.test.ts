import { describe, expect, it } from "vitest";
import {
  CamKey,
  EASE,
  cameraAt,
  drift,
  holdFactor,
  land,
  latticePoints,
  leadKeys,
  settle,
  shake,
  tween,
  whipKeys,
} from "../src/lib/motion";
import { progress } from "../src/moves";

const FPS = 30;
const range = (a: number, b: number) =>
  Array.from({ length: b - a + 1 }, (_, i) => a + i);
const nonDecreasing = (xs: number[]) =>
  xs.every((x, i) => i === 0 || x >= xs[i - 1] - 1e-9);

describe("EASE", () => {
  it.each(Object.entries(EASE))("%s maps 0→0, 1→1 and is monotonic", (_, e) => {
    expect(e(0)).toBeCloseTo(0, 6);
    expect(e(1)).toBeCloseTo(1, 6);
    expect(nonDecreasing(range(0, 100).map((i) => e(i / 100)))).toBe(true);
  });

  it("snap does most of the move early, in does it late", () => {
    expect(EASE.snap(0.3)).toBeGreaterThan(0.6);
    expect(EASE.in(0.3)).toBeLessThan(0.1);
  });
});

describe("tween", () => {
  it("hits both ends and clamps outside the range", () => {
    expect(tween(10, [10, 20], [0, 100])).toBe(0);
    expect(tween(20, [10, 20], [0, 100])).toBe(100);
    expect(tween(-50, [10, 20], [0, 100])).toBe(0);
    expect(tween(500, [10, 20], [0, 100])).toBe(100);
  });

  it.each(Object.entries(EASE))(
    "stays in range and is monotonic with %s",
    (_, e) => {
      const vs = range(0, 30).map((f) => tween(f, [5, 25], [3, 9], e));
      expect(Math.min(...vs)).toBeGreaterThanOrEqual(3);
      expect(Math.max(...vs)).toBeLessThanOrEqual(9);
      expect(nonDecreasing(vs)).toBe(true);
    },
  );

  it("works for decreasing values", () => {
    const vs = range(0, 20).map((f) => tween(f, [0, 20], [1, 0]));
    expect(vs[0]).toBe(1);
    expect(vs[20]).toBe(0);
    expect(nonDecreasing(vs.map((v) => -v))).toBe(true);
  });

  it("defaults to EASE.out", () => {
    expect(tween(5, [0, 10], [0, 1])).toBeCloseTo(EASE.out(0.5), 9);
  });
});

describe("land", () => {
  const vs = range(0, 120).map((f) => land(f, FPS, 10));

  it("is 0 before it starts and settles at 1", () => {
    expect(vs.slice(0, 11).every((v) => v === 0)).toBe(true);
    expect(vs[120]).toBeCloseTo(1, 2);
  });

  it("overshoots a little, but not much", () => {
    const peak = Math.max(...vs);
    expect(peak).toBeGreaterThan(1);
    expect(peak).toBeLessThan(1.25);
  });

  it("overshoots less with more damping", () => {
    const peak = (damping: number) =>
      Math.max(...range(0, 120).map((f) => land(f, FPS, 0, { damping })));
    expect(peak(20)).toBeLessThan(peak(8));
  });
});

describe("settle", () => {
  const vs = range(0, 120).map((f) => settle(f, FPS, 10));

  it("goes 0 → 1 without bouncing", () => {
    expect(vs[0]).toBe(0);
    expect(vs[10]).toBe(0);
    expect(vs[120]).toBeCloseTo(1, 2);
    expect(Math.max(...vs)).toBeLessThanOrEqual(1 + 1e-6);
    expect(nonDecreasing(vs)).toBe(true);
  });
});

describe("drift", () => {
  it("is deterministic and bounded by its amplitude", () => {
    for (const f of range(0, 300)) {
      const d = drift(f, FPS, 6);
      expect(d).toEqual(drift(f, FPS, 6));
      expect(Math.abs(d.x)).toBeLessThanOrEqual(6 + 1e-9);
      expect(Math.abs(d.y)).toBeLessThanOrEqual(6 + 1e-9);
      expect(Math.abs(d.r)).toBeLessThanOrEqual(6 / 20 + 1e-9);
    }
  });

  it("is still with zero amplitude", () => {
    expect(drift(42, FPS, 0)).toEqual({ x: 0, y: 0, r: 0 });
  });

  it("differs between seeds", () => {
    expect(drift(42, FPS, 6, "a")).not.toEqual(drift(42, FPS, 6, "b"));
  });
});

describe("cameraAt", () => {
  const linear = (t: number) => t;
  const keys: CamKey[] = [
    { f: 10, fx: 100, fy: 200, z: 1 },
    { f: 30, fx: 300, fy: 200, z: 4, ease: linear },
    { f: 60, fx: 300, fy: 500, z: 2, rot: 10 },
  ];

  it("holds the first key before it and the last key after it", () => {
    expect(cameraAt(0, keys)).toMatchObject({ fx: 100, fy: 200, z: 1 });
    expect(cameraAt(10, keys)).toMatchObject({ fx: 100, fy: 200, z: 1 });
    expect(cameraAt(100, keys)).toMatchObject({ fx: 300, fy: 500, z: 2 });
  });

  it("passes through every key", () => {
    for (const k of keys) {
      const c = cameraAt(k.f, keys);
      expect(c.fx).toBeCloseTo(k.fx, 9);
      expect(c.fy).toBeCloseTo(k.fy, 9);
      expect(c.z).toBeCloseTo(k.z, 9);
    }
  });

  it("uses the arriving key's easing; zoom interpolates multiplicatively", () => {
    const mid = cameraAt(20, keys);
    expect(mid.fx).toBeCloseTo(200, 9); // linear
    expect(mid.z).toBeCloseTo(2, 9); // geometric mean of 1 and 4
  });

  it("moves monotonically between two keys and stays within them", () => {
    const seg = range(30, 60).map((f) => cameraAt(f, keys));
    expect(nonDecreasing(seg.map((c) => c.fy))).toBe(true);
    expect(nonDecreasing(seg.map((c) => -c.z))).toBe(true);
    expect(nonDecreasing(seg.map((c) => c.rot ?? 0))).toBe(true);
    for (const c of seg) {
      expect(c.z).toBeGreaterThanOrEqual(2 - 1e-9);
      expect(c.z).toBeLessThanOrEqual(4 + 1e-9);
    }
  });

  it("defaults the easing to EASE.glide", () => {
    const c = cameraAt(45, keys); // halfway through the 30 → 60 segment
    expect(c.fy).toBeCloseTo(200 + 300 * EASE.glide(0.5), 9);
  });
});

describe("progress (moves)", () => {
  it("is a clamped, monotonic 0 → 1 over the stretch", () => {
    const vs = range(0, 40).map((f) => progress(f, 10, 30));
    expect(vs[0]).toBe(0);
    expect(vs[10]).toBe(0);
    expect(vs[30]).toBe(1);
    expect(vs[40]).toBe(1);
    expect(nonDecreasing(vs)).toBe(true);
  });

  it("matches tween with the same easing", () => {
    for (const f of range(0, 40))
      expect(progress(f, 10, 30, EASE.snap)).toBeCloseTo(
        tween(f, [10, 30], [0, 1], EASE.snap),
        12,
      );
  });
});

describe("operated-camera helpers", () => {
  const keys: CamKey[] = [
    { f: 0, fx: 0, fy: 0, z: 1 },
    { f: 60, fx: 100, fy: 0, z: 1.2 },
    { f: 120, fx: 200, fy: 50, z: 1 },
  ];

  it("leadKeys moves keys earlier, keeps the first and stays strictly increasing", () => {
    const l = leadKeys(keys, 3);
    expect(l.map((k) => k.f)).toEqual([0, 57, 117]);
    expect(leadKeys(keys, 0).map((k) => k.f)).toEqual([0, 60, 120]);
    const tight = leadKeys(
      [
        { f: 0, fx: 0, fy: 0, z: 1 },
        { f: 2, fx: 1, fy: 0, z: 1 },
        { f: 3, fx: 2, fy: 0, z: 1 },
      ],
      10,
    ).map((k) => k.f);
    expect(tight.every((f, i) => i === 0 || f > tight[i - 1])).toBe(true);
  });

  it("whipKeys waits, then reaches the target exactly at the landing frame", () => {
    const from: CamKey = { f: 10, fx: 0, fy: 0, z: 1 };
    const ks = whipKeys(from, { fx: 500, fy: 80, z: 1.5 }, 100, 6);
    expect(cameraAt(90, ks).fx).toBe(0); // still waiting
    expect(cameraAt(100, ks).fx).toBeCloseTo(500, 6);
    expect(cameraAt(97, ks).fx).toBeGreaterThan(0);
    expect(cameraAt(97, ks).fx).toBeLessThan(500);
    expect(nonDecreasing(ks.map((k) => k.f))).toBe(true);
  });

  it("shake is zero before the hit, deterministic, and decays", () => {
    expect(shake(9, FPS, 10)).toEqual({ x: 0, y: 0, r: 0 });
    expect(shake(14, FPS, 10, { seed: "a" })).toEqual(
      shake(14, FPS, 10, { seed: "a" }),
    );
    const mag = (f: number) => {
      const s = shake(f, FPS, 10, { amp: 20, seed: "a" });
      return Math.hypot(s.x, s.y);
    };
    const early = Math.max(...range(10, 16).map(mag));
    const late = Math.max(...range(60, 66).map(mag));
    expect(early).toBeGreaterThan(5);
    expect(late).toBeLessThan(early / 10);
  });

  it("holdFactor is 1 outside holds, 0 inside, and ramps smoothly", () => {
    const holds: [number, number][] = [[100, 150]];
    expect(holdFactor(0, FPS, holds)).toBe(1);
    expect(holdFactor(120, FPS, holds)).toBe(0);
    const edge = holdFactor(95, FPS, holds);
    expect(edge).toBeGreaterThan(0);
    expect(edge).toBeLessThan(1);
    expect(holdFactor(500, FPS, [])).toBe(1);
  });

  it("latticePoints are aligned to the spacing and inside the bounds", () => {
    const p = latticePoints({ x0: -50, y0: 0, x1: 250, y1: 100 }, 100);
    expect(p.length).toBe(3 * 2); // x: 0, 100, 200 · y: 0, 100
    for (const q of p) {
      expect(q.x % 100).toBe(0);
      expect(q.y % 100).toBe(0);
      expect(q.x).toBeGreaterThanOrEqual(-50);
      expect(q.x).toBeLessThanOrEqual(250);
    }
  });
});

// ------------------------------------------------------------------ squash and stretch
import {
  contactSquash,
  stretchAxes,
  stretchFromVelocity,
  stretchTransform,
  velocityOf,
} from "../src/lib/motion";

describe("stretchFromVelocity", () => {
  it("is no stretch at rest", () => {
    expect(stretchFromVelocity(0, 0)).toEqual({
      along: 1,
      across: 1,
      angle: 0,
    });
    expect(stretchTransform(stretchFromVelocity(0, 0))).toBe("");
  });
  it("keeps the area and grows with speed, under its cap", () => {
    let prev = 1;
    for (const v of [5, 20, 60, 150, 400, 5000]) {
      const s = stretchFromVelocity(v, 0, { max: 0.3 });
      expect(s.along * s.across).toBeCloseTo(1, 9);
      expect(s.along).toBeGreaterThan(prev);
      expect(s.along).toBeLessThanOrEqual(1.3 + 1e-9);
      prev = s.along;
    }
  });
  it("points along the travel", () => {
    expect(stretchFromVelocity(10, 0).angle).toBeCloseTo(0, 9);
    expect(stretchFromVelocity(0, 10).angle).toBeCloseTo(90, 9); // y down: falling
    expect(stretchFromVelocity(-10, 0).angle).toBeCloseTo(180, 9);
    expect(stretchAxes(stretchFromVelocity(0, 50)).sy).toBeGreaterThan(1);
    expect(stretchAxes(stretchFromVelocity(50, 0)).sx).toBeGreaterThan(1);
  });
  it("max 0 turns it off", () => {
    expect(stretchFromVelocity(100, 0, { max: 0 }).along).toBe(1);
  });
});

describe("velocityOf", () => {
  it("differentiates a position function and never reads before `from`", () => {
    const v = velocityOf((f) => ({ x: 3 * f, y: f * f }), 10);
    expect(v.vx).toBeCloseTo(3, 9);
    expect(v.vy).toBeCloseTo(20, 9);
    const seen: number[] = [];
    velocityOf((f) => (seen.push(f), { x: f, y: 0 }), 10, 0.5, 10);
    expect(Math.min(...seen)).toBeGreaterThanOrEqual(10);
  });
});

describe("contactSquash", () => {
  it("is nothing before the contact, flat on it, back to rest after", () => {
    expect(contactSquash(9, FPS, 10).along).toBe(1);
    const hit = contactSquash(10, FPS, 10, { amount: 0.25 });
    expect(hit.along).toBeCloseTo(0.75, 9);
    expect(hit.along * hit.across).toBeCloseTo(1, 9);
    expect(hit.angle).toBe(90);
    expect(Math.abs(contactSquash(10 + FPS, FPS, 10).along - 1)).toBeLessThan(
      1e-3,
    );
  });
});
