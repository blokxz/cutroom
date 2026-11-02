import fs from "node:fs";
import path from "node:path";
import { describe, expect, it, vi } from "vitest";
import {
  Brief,
  Copy,
  contactFrom,
  copyFrom,
  splitAccent,
} from "../src/lib/brief";

// the generated client brand module loads fonts at import time (browser-only)
vi.mock("@remotion/fonts", () => ({ loadFont: () => Promise.resolve() }));

const DEFAULTS: Copy = {
  headline: "Default / headline",
  subtitle: "Default subtitle",
  lines: ["one", "two"],
  ctaText: "Write to us",
  contact: "+00 000",
};

describe("splitAccent", () => {
  it("splits at the first ' / '", () => {
    expect(splitAccent("We have something / for you")).toEqual([
      "We have something",
      "for you",
    ]);
    expect(splitAccent("a / b / c")).toEqual(["a", "b / c"]);
  });

  it("returns the whole text and no accent without a separator", () => {
    expect(splitAccent("Hot spring")).toEqual(["Hot spring", ""]);
    expect(splitAccent("")).toEqual(["", ""]);
  });

  it("needs spaces around the slash", () => {
    expect(splitAccent("24/7 open")).toEqual(["24/7 open", ""]);
  });
});

describe("contactFrom", () => {
  it("prefers the brief's contact", () => {
    expect(
      contactFrom({ cta: { contact: "+1 555" } }, { whatsapp: "+54 9" }),
    ).toBe("+1 555");
  });

  it("falls back to the client's WhatsApp, then to any contact", () => {
    expect(contactFrom(undefined, { instagram: "@x", whatsapp: "+54 9" })).toBe(
      "+54 9",
    );
    expect(contactFrom({ cta: { contact: "" } }, { whatsapp: "+54 9" })).toBe(
      "+54 9",
    );
    expect(contactFrom({}, { instagram: "@x" })).toBe("@x");
    expect(contactFrom({}, { whatsapp: undefined, email: "a@b.c" })).toBe(
      "a@b.c",
    );
    expect(contactFrom(undefined, {})).toBe("");
  });
});

describe("copyFrom", () => {
  it("returns the defaults without a brief (Studio)", () => {
    expect(copyFrom(undefined, DEFAULTS)).toEqual(DEFAULTS);
    expect(copyFrom({}, DEFAULTS)).toEqual(DEFAULTS);
  });

  it("overrides field by field", () => {
    const c = copyFrom(
      {
        copy: { headline: "New / head" },
        cta: { contact: "+1 555" },
      },
      DEFAULTS,
    );
    expect(c).toEqual({
      ...DEFAULTS,
      headline: "New / head",
      contact: "+1 555",
    });
  });

  it("treats empty strings as missing", () => {
    const c = copyFrom(
      {
        copy: { headline: "", subtitle: "", lines: ["", "B"] },
        cta: { text: "" },
      },
      DEFAULTS,
    );
    expect(c).toEqual({ ...DEFAULTS, lines: ["one", "B"] });
  });

  it("merges lines by position and keeps extra brief lines", () => {
    expect(copyFrom({ copy: { lines: ["A"] } }, DEFAULTS).lines).toEqual([
      "A",
      "two",
    ]);
    expect(
      copyFrom({ copy: { lines: ["A", "B", "C"] } }, DEFAULTS).lines,
    ).toEqual(["A", "B", "C"]);
  });

  it("does not mutate the defaults", () => {
    const before = JSON.stringify(DEFAULTS);
    copyFrom({ copy: { lines: ["x", "y", "z"] } }, DEFAULTS);
    expect(JSON.stringify(DEFAULTS)).toBe(before);
  });
});

// Rendering an example with its brief must give the same picture as Studio without one.
describe("example briefs match the example defaults", () => {
  const briefDir = path.resolve(__dirname, "../../clients/sample/briefs");
  const read = (id: string): Brief =>
    JSON.parse(fs.readFileSync(path.join(briefDir, `${id}.json`), "utf8"));

  it.each([["sample-post", "SamplePost", "SAMPLE_POST_COPY"]])(
    "%s",
    async (id, file, name) => {
      const mod = await import(`../src/examples/sample/${file}.tsx`);
      const defaults = mod[name] as Copy;
      expect(defaults).toBeDefined();
      expect(copyFrom(read(id), defaults)).toEqual(defaults);
    },
  );
});
