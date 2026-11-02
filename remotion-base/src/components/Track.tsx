/**
 * Tracking for the verifier.
 *
 * Wrap the element that matters in <Track id="…"> (one child: the element that
 * carries the position/transform; it is what gets measured). When the composition is
 * rendered with the input prop `track: true` (scripts/render.mjs does this),
 * every frame logs each tracked element's on-screen box and effective opacity.
 * tools/verify.py uses that to check continuity between scenes, framing,
 * safe zones for text, and whether fast elements have motion blur.
 *
 * Each frame logs one `__TRACK__` + JSON record per tracked element:
 * `{ f, lf, id, k, x, y, w, h, o, inFrame, blurred }` — absolute and local frame,
 * id, kind, on-screen box (composition pixels, measured from <TrackRoot>'s origin),
 * effective opacity and the two flags. Records of kind
 * "text" also carry `t`: the element's text as laid out (innerText, so line
 * breaks and block children become spaces; whitespace collapsed and trimmed),
 * which the verifier uses to check reading time.
 *
 * <Beats> declares the scene boundaries of the beat sheet. Each beat is
 * `{ f, name, kind }`: `f` is the frame the beat starts on, `name` is the
 * beat-sheet label, and `kind` says what the verifier should expect in it:
 *   "move"  something travels; the beat must carry a survivor into the next one
 *   "rest"  a short breather after a move (drift only, nothing new arrives)
 *   "hold"  the picture stays put so it can be read (a labelled place, the CTA)
 *   "cut"   a deliberate hard cut: the continuity check is skipped at this boundary
 * Always set `kind`. The beats are logged once (frame 0) as `__BEATS__` + a JSON
 * array; tools/verify.py reads `kind` and only falls back to matching the name
 * (rest / hold / cut) when it is missing.
 */
import React, {
  createContext,
  useContext,
  useLayoutEffect,
  useRef,
} from "react";
import {
  getInputProps,
  getRemotionEnvironment,
  useCurrentFrame,
} from "remotion";

const AbsFrame = createContext<number | null>(null);
// a zero-size marker at the composition's origin: boxes are measured relative to it, so they are
// in composition pixels even when the renderer keeps the page off-screen (it does on frame 0)
const Origin = createContext<React.RefObject<HTMLDivElement | null> | null>(
  null,
);
const enabled = () => {
  try {
    return (
      getRemotionEnvironment().isRendering &&
      Boolean((getInputProps() as { track?: boolean }).track)
    );
  } catch {
    return false;
  }
};

/** Put once at the root of a composition, outside any Sequence or blur. */
export const TrackRoot: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const frame = useCurrentFrame();
  const origin = useRef<HTMLDivElement>(null);
  return (
    <AbsFrame.Provider value={frame}>
      <Origin.Provider value={origin}>
        <div
          ref={origin}
          style={{
            position: "absolute",
            left: 0,
            top: 0,
            width: 0,
            height: 0,
            pointerEvents: "none",
          }}
        />
        {children}
      </Origin.Provider>
    </AbsFrame.Provider>
  );
};

export type TrackKind = "subject" | "text" | "logo" | "image" | "shape";

const effectiveOpacity = (el: HTMLElement | null) => {
  let o = 1;
  while (el) {
    const s = getComputedStyle(el);
    o *= parseFloat(s.opacity || "1");
    if (s.visibility === "hidden" || s.display === "none") return 0;
    el = el.parentElement;
  }
  return o;
};

export const Track: React.FC<{
  id: string;
  kind?: TrackKind;
  /** must stay fully inside the frame whenever visible */
  inFrame?: boolean;
  /** rendered inside <MotionBlur> — fast moves are covered */
  blurred?: boolean;
  style?: React.CSSProperties;
  children: React.ReactNode;
}> = ({
  id,
  kind = "subject",
  inFrame = false,
  blurred = false,
  style,
  children,
}) => {
  const ref = useRef<HTMLDivElement>(null);
  const local = useCurrentFrame();
  const abs = useContext(AbsFrame);
  const origin = useContext(Origin);
  useLayoutEffect(() => {
    if (!enabled() || !ref.current) return;
    // measure the first child: that is the element carrying the transforms
    const el =
      (ref.current.firstElementChild as HTMLElement | null) ?? ref.current;
    let r = el.getBoundingClientRect();
    if (kind === "text") {
      // text blocks are often full-width containers: measure the glyphs instead
      const walker = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
      let x0 = Infinity,
        y0 = Infinity,
        x1 = -Infinity,
        y1 = -Infinity;
      for (let n = walker.nextNode(); n; n = walker.nextNode()) {
        if (!n.textContent?.trim()) continue;
        const range = document.createRange();
        range.selectNodeContents(n);
        for (const q of Array.from(range.getClientRects())) {
          x0 = Math.min(x0, q.left);
          y0 = Math.min(y0, q.top);
          x1 = Math.max(x1, q.right);
          y1 = Math.max(y1, q.bottom);
        }
      }
      if (x1 > x0 && y1 > y0) r = new DOMRect(x0, y0, x1 - x0, y1 - y0);
    }
    const o0 = origin?.current?.getBoundingClientRect();
    const dx = o0 ? o0.left : 0;
    const dy = o0 ? o0.top : 0;
    const rec = {
      f: abs ?? local,
      lf: local,
      id,
      k: kind,
      x: Math.round(r.x - dx),
      y: Math.round(r.y - dy),
      w: Math.round(r.width),
      h: Math.round(r.height),
      o: +effectiveOpacity(el).toFixed(2),
      inFrame,
      blurred,
      ...(kind === "text"
        ? {
            // innerText follows the layout: <br> and block children become line breaks
            // (→ spaces), while words split into inline spans stay whole
            t: (el.innerText || el.textContent || "")
              .replace(/\s+/g, " ")
              .trim(),
          }
        : {}),
    };
    console.log("__TRACK__" + JSON.stringify(rec));
  });
  return (
    <div ref={ref} style={{ position: "absolute", inset: 0, ...style }}>
      {children}
    </div>
  );
};

export type BeatKind = "move" | "rest" | "hold" | "cut";
export type Beat = { f: number; name: string; kind?: BeatKind };

export const Beats: React.FC<{ beats: Beat[] }> = ({ beats }) => {
  const frame = useCurrentFrame();
  useLayoutEffect(() => {
    if (enabled() && frame === 0)
      console.log("__BEATS__" + JSON.stringify(beats));
  });
  return null;
};
