/**
 * Shared pieces of the Bungalows Concordia reels: the photo cover, the closing card (logo, tagline, call to
 * action) and the brief-driven copy. Photos live in clients/bungalows-concordia/assets/photos (kept out of git).
 * The logo is clients/bungalows-concordia/assets/logo.png; until it exists the card shows the name as plain
 * type, so a missing file never breaks a render.
 */
import React, { useEffect, useState } from "react";
import { AbsoluteFill, Img, continueRender, delayRender } from "remotion";
import { Track } from "../../components/Track";
import { Copy, contactFrom } from "../../lib/brief";
import {
  CLIENT,
  CONTACT,
  BUNGALOWS_CONCORDIA as T,
  asset,
} from "../../clients/bungalows-concordia/brand";

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

/** The brand mark: the client's logo (dark green on transparent), or the name in type while the file is missing. */
export const Logo: React.FC<{ width?: number }> = ({ width = 700 }) => {
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
          color: T.colors.ink,
          textAlign: "center",
          lineHeight: 1,
        }}
      >
        {CLIENT.name}
      </div>
    );
  }
  return <Img src={asset("logo.png")} style={{ width }} />;
};

/**
 * The closing card: a cream panel over whatever is behind it, the logo in its own colours (it carries the
 * name and the tagline), the call to action and the contact.
 */
export const EndCard: React.FC<{ p: number; copy: Copy }> = ({ p, copy }) => (
  <AbsoluteFill style={{ opacity: p }}>
    <AbsoluteFill style={{ background: T.colors.ground }} />
    <Track id="logo" kind="logo">
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 400,
          display: "flex",
          justifyContent: "center",
        }}
      >
        <Logo />
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
          color: "#7D4F55",
          fontFamily: T.fonts.display,
          fontStyle: "italic",
          fontSize: 68,
        }}
      >
        {copy.ctaText}
      </div>
    </Track>
    <Track id="contact" kind="text">
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 1220,
          textAlign: "center",
          color: T.colors.ink,
          fontFamily: T.fonts.text,
          fontWeight: 500,
          fontSize: 38,
          letterSpacing: "0.12em",
        }}
      >
        {copy.contact}
      </div>
    </Track>
  </AbsoluteFill>
);
