/**
 * Shared pieces of the Termas Concordia reels: the photo cover, the closing card (logo, tagline, call to
 * action) and the brief-driven copy. Photos live in clients/termas-concordia/assets/photos (kept out of git).
 * The logo is clients/termas-concordia/assets/logo.png; until it exists the card shows the name as plain
 * type, so a missing file never breaks a render.
 */
import React, { useEffect, useState } from "react";
import { AbsoluteFill, Img, continueRender, delayRender } from "remotion";
import { Track } from "../../components/Track";
import { Copy, contactFrom } from "../../lib/brief";
import {
  CLIENT,
  CONTACT,
  TERMAS_CONCORDIA as T,
  asset,
} from "../../clients/termas-concordia/brand";

export { T, asset };

export const TERMAS_COPY: Copy = {
  headline: CLIENT.taglines[0],
  subtitle: "",
  lines: [],
  ctaText: "Reservá tu visita",
  contact: contactFrom(undefined, CONTACT),
};

export const PHOTOS = {
  sunrise: "photos/sunrise.jpg",
  steam: "photos/steam.jpg",
  indoor: "photos/indoor.jpg",
  sky: "photos/sky.jpg",
  aerial: "photos/aerial.jpg",
  sunset: "photos/sunset.jpg",
  stream: "photos/stream.jpg",
} as const;

/** A photo that covers its box; `focus` is the crop centre in % of the photo, `zoom` scales it about that point. */
export const Cover: React.FC<{
  src: string;
  focus?: [number, number];
  zoom?: number;
  style?: React.CSSProperties;
}> = ({ src, focus = [50, 50], zoom = 1, style }) => (
  <Img
    src={asset(src)}
    style={{
      position: "absolute",
      inset: 0,
      width: "100%",
      height: "100%",
      objectFit: "cover",
      objectPosition: `${focus[0]}% ${focus[1]}%`,
      transform: `scale(${zoom})`,
      transformOrigin: `${focus[0]}% ${focus[1]}%`,
      ...style,
    }}
  />
);

/** The brand mark: the client's logo, or the name in type while the logo file is missing. */
export const Logo: React.FC<{ width?: number }> = ({ width = 560 }) => {
  // look for the file first: an <Img> on a missing file would log a decode error on every frame
  const [state, setState] = useState<"checking" | "found" | "missing">(
    "checking",
  );
  const [handle] = useState(() => delayRender("looking for the logo"));
  useEffect(() => {
    fetch(asset("logo.png"), { method: "HEAD" })
      .then((r) =>
        setState(
          r.ok && (r.headers.get("content-type") ?? "").startsWith("image")
            ? "found"
            : "missing",
        ),
      )
      .catch(() => setState("missing"))
      .finally(() => continueRender(handle));
  }, [handle]);
  if (state === "checking") return null;
  if (state === "missing") {
    return (
      <div
        style={{
          fontFamily: T.fonts.display,
          fontSize: 96,
          color: "#fff",
          textAlign: "center",
          lineHeight: 1,
        }}
      >
        Termas <i>Concordia</i>
      </div>
    );
  }
  return <Img src={asset("logo.png")} style={{ width }} />;
};

/** The closing card over whatever is behind it: a scrim, the logo, the tagline and the call to action. */
export const EndCard: React.FC<{ p: number; copy: Copy }> = ({ p, copy }) => (
  <AbsoluteFill style={{ opacity: p }}>
    <AbsoluteFill
      style={{
        background: "linear-gradient(rgba(8,30,48,.38), rgba(8,30,48,.62))",
      }}
    />
    <Track id="logo" kind="logo">
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 780,
          display: "flex",
          justifyContent: "center",
        }}
      >
        <Logo />
      </div>
    </Track>
    <Track id="tagline" kind="text">
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 1010,
          textAlign: "center",
          color: "#fff",
          fontFamily: T.fonts.text,
          fontWeight: 500,
          fontSize: 32,
          letterSpacing: "0.3em",
          textTransform: "uppercase",
        }}
      >
        {copy.headline}
      </div>
    </Track>
    <Track id="cta" kind="text">
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 1110,
          textAlign: "center",
          color: "#FFD9B8",
          fontFamily: T.fonts.display,
          fontStyle: "italic",
          fontSize: 64,
        }}
      >
        {copy.ctaText}
        {copy.contact ? ` · ${copy.contact}` : ""}
      </div>
    </Track>
  </AbsoluteFill>
);
