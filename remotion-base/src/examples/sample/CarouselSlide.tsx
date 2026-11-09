/**
 * One slide of a photo carousel (4:5 still): a full-bleed photo, a label, and a segmented progress
 * bar that shows where the slide sits in the swipe. Every slide shares the same layout so the
 * carousel reads as one object (the survivor is the bar). Photos come from public/<folder>/.
 * Render one still per slide: npx remotion still src/index.ts CarouselSlide out/1.png --props='{...}'
 */
import React from "react";
import { AbsoluteFill, Img, staticFile } from "remotion";
import { FORMATS } from "../../lib/formats";
import { SAMPLE as B } from "./brand";

export type CarouselSlideProps = {
  photo: string;
  label: string;
  index: number;
  total: number;
  /** focal point of the crop, % of the photo */
  focus?: [number, number];
};

export const CAROUSEL_DEFAULTS: CarouselSlideProps = {
  photo: "carousel/1.jpg",
  label: "Ambiente",
  index: 0,
  total: 5,
};

export const CarouselSlide: React.FC<CarouselSlideProps> = ({ photo, label, index, total, focus = [50, 50] }) => {
  const m = FORMATS.post.safe;
  return (
    <AbsoluteFill style={{ background: "#111" }}>
      <Img
        src={staticFile(photo)}
        style={{ width: "100%", height: "100%", objectFit: "cover", objectPosition: `${focus[0]}% ${focus[1]}%` }}
      />
      <AbsoluteFill style={{ background: "linear-gradient(to top, rgba(0,0,0,.62) 0%, rgba(0,0,0,0) 38%)" }} />
      <div style={{ position: "absolute", left: m.left + 20, bottom: m.bottom + 70, color: "#fff" }}>
        <div
          style={{
            fontFamily: B.fonts.text,
            fontWeight: 500,
            fontSize: 24,
            letterSpacing: "0.32em",
            textTransform: "uppercase",
            opacity: 0.85,
          }}
        >
          {String(index + 1).padStart(2, "0")} / {String(total).padStart(2, "0")}
        </div>
        <div style={{ fontFamily: B.fonts.display, fontStyle: "italic", fontSize: 92, lineHeight: 1.05, marginTop: 8 }}>
          {label}
        </div>
      </div>
      <div style={{ position: "absolute", left: m.left + 20, right: m.right + 20, bottom: m.bottom + 20, display: "flex", gap: 10 }}>
        {Array.from({ length: total }, (_, i) => (
          <div key={i} style={{ flex: 1, height: 6, borderRadius: 3, background: i === index ? "#fff" : "rgba(255,255,255,.35)" }} />
        ))}
      </div>
    </AbsoluteFill>
  );
};
