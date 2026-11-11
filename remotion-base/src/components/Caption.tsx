/**
 * Caption — the two-line caption of a scene: a small sans line, then a large serif italic line that comes in out
 * of a blur, rising a little; a {word} of the large line sits on a box that grows from its left edge. Both lines
 * leave the same way, before the scene changes, so no caption ghosts through a transition.
 *
 *   splitCaption("small|large {word}")   → { small, before, word, after }
 *   blurIn(frame, inAt, outAt, len)       → { opacity, filter, translate } for one line
 *   <Caption text at out …/>              the caption, tracked as text for the verifier
 */
import React from "react";
import { useCurrentFrame } from "remotion";
import { EASE, tween } from "../lib/motion";
import { Track } from "./Track";

export type CaptionParts = {
  small: string;
  before: string;
  word: string;
  after: string;
};

export const splitCaption = (text: string): CaptionParts => {
  const [small, big = ""] = text.split("|");
  const m = big.match(/^(.*?)\{(.+?)\}(.*)$/);
  return m
    ? { small, before: m[1], word: m[2], after: m[3] }
    : { small, before: big, word: "", after: "" };
};

/** In over `len` frames (out of a blur, rising), out over 10 frames from `outAt`. */
export const blurIn = (
  frame: number,
  inAt: number,
  outAt: number,
  len = 12,
  blurPx = 14,
  rise = 18,
) => {
  const i = tween(frame, [inAt, inAt + len], [0, 1], EASE.out);
  const o = tween(frame, [outAt, outAt + 10], [0, 1], EASE.in);
  const v = i * (1 - o);
  return {
    opacity: v,
    filter: v >= 0.999 ? "none" : `blur(${((1 - v) * blurPx).toFixed(2)}px)`,
    translate: `0px ${((1 - i) * rise).toFixed(1)}px`,
  };
};

export const Caption: React.FC<{
  /** "small line|large line", a {word} in the large line goes on the box */
  text: string;
  /** frame the scene starts; the caption comes in a little after */
  at: number;
  /** frame the caption starts to leave (keep it ≥ 10 frames before the next change) */
  out: number;
  id: string;
  fonts: { display: string; text: string };
  box: string;
  /** y of the small line's top; the large line sits under it */
  top?: number;
  size?: number;
  color?: string;
}> = ({
  text,
  at,
  out,
  id,
  fonts,
  box,
  top = 830,
  size = 112,
  color = "#fff",
}) => {
  const frame = useCurrentFrame();
  const p = splitCaption(text);
  const grow =
    tween(frame, [at + 18, at + 30], [0, 1], EASE.snap) *
    (1 - tween(frame, [out, out + 10], [0, 1]));
  const big: React.CSSProperties = {
    fontFamily: fonts.display,
    fontStyle: "italic",
    fontWeight: 400,
    fontSize: size,
    lineHeight: 1.05,
    letterSpacing: "-0.01em",
    color,
    textShadow: "0 4px 26px rgba(0,0,0,.32)",
  };
  return (
    <>
      <Track id={`${id}-a`} kind="text">
        <div
          style={{
            position: "absolute",
            left: 140,
            right: 140,
            top,
            textAlign: "center",
            ...blurIn(frame, at + 6, out),
          }}
        >
          <span
            style={{
              fontFamily: fonts.text,
              fontWeight: 400,
              fontSize: 40,
              letterSpacing: "0.01em",
              color,
              textShadow: "0 2px 16px rgba(0,0,0,.45)",
            }}
          >
            {p.small}
          </span>
        </div>
      </Track>
      <Track id={`${id}-b`} kind="text">
        <div
          style={{
            position: "absolute",
            left: 110,
            right: 110,
            top: top + 54,
            textAlign: "center",
            ...blurIn(frame, at + 10, out),
          }}
        >
          <span style={big}>
            {p.before}
            {p.word && (
              <span style={{ position: "relative", padding: "0 16px" }}>
                <span
                  style={{
                    position: "absolute",
                    inset: `${size * 0.16}px 0 ${size * 0.04}px 0`,
                    background: box,
                    opacity: 0.9,
                    transformOrigin: "0 50%",
                    scale: `${grow} 1`,
                  }}
                />
                <span style={{ position: "relative" }}>{p.word}</span>
              </span>
            )}
            {p.after}
          </span>
        </div>
      </Track>
    </>
  );
};
