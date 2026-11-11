import { describe, expect, it } from "vitest";
import { blurIn, splitCaption } from "../src/components/Caption";
import { timeOffset } from "../src/lib/shutter";

describe("splitCaption", () => {
  it("splits the small line, the large line and the boxed word", () => {
    expect(splitCaption("Imaginate despertar|entre {vapor}")).toEqual({
      small: "Imaginate despertar",
      before: "entre ",
      word: "vapor",
      after: "",
    });
    expect(splitCaption("Cortá con|la {rutina} hoy").after).toBe(" hoy");
  });
  it("has no box when no word is marked, and no large line when there is none", () => {
    expect(splitCaption("Tu lugar|para frenar")).toEqual({ small: "Tu lugar", before: "para frenar", word: "", after: "" });
    expect(splitCaption("Solo una línea").before).toBe("");
  });
});

describe("blurIn", () => {
  it("is hidden before it starts, sharp and in place once in, gone after it leaves", () => {
    expect(blurIn(0, 10, 100).opacity).toBe(0);
    const on = blurIn(40, 10, 100);
    expect(on.opacity).toBeCloseTo(1, 9);
    expect(on.filter).toBe("none");
    expect(on.translate).toBe("0px 0.0px");
    expect(blurIn(115, 10, 100).opacity).toBeCloseTo(0, 9);
  });
  it("is blurred and lower while it arrives", () => {
    const mid = blurIn(13, 10, 100);
    expect(mid.opacity).toBeGreaterThan(0);
    expect(mid.opacity).toBeLessThan(1);
    expect(mid.filter).toMatch(/^blur\(/);
    expect(parseFloat(mid.translate.split(" ")[1])).toBeGreaterThan(0);
  });
});

describe("timeOffset", () => {
  it("is 0 outside a render", () => {
    expect(timeOffset()).toBe(0);
  });
});
