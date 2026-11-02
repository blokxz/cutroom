// Output formats and the areas each platform's UI covers.
// Keep text, logos and contact data outside the `safe` margins.
//
// The margins are read from the verifier's specs (tools/quality/platforms/specs/*.json), so the
// SafeZones overlay in Studio and the verifier always agree. Edit the JSON, not this file.
import instagram from "../../../tools/quality/platforms/specs/instagram.json";
import tiktok from "../../../tools/quality/platforms/specs/tiktok.json";
import shorts from "../../../tools/quality/platforms/specs/youtube_shorts.json";

export type Margins = {
  top: number;
  bottom: number;
  left: number;
  right: number;
};

export type Format = {
  id: "story" | "reel" | "post" | "landscape" | "tiktok" | "short";
  platform: "instagram" | "tiktok" | "youtube_shorts" | "none";
  width: number;
  height: number;
  fps: number;
  safe: Margins;
};

/** specs store `ui` as [top, bottom, left, right] */
const margins = (ui: readonly number[]): Margins => ({
  top: ui[0],
  bottom: ui[1],
  left: ui[2],
  right: ui[3],
});

export const FORMATS: Record<Format["id"], Format> = {
  story: {
    id: "story",
    platform: "instagram",
    width: 1080,
    height: 1920,
    fps: 30,
    safe: margins(instagram.formats.story.ui),
  },
  reel: {
    id: "reel",
    platform: "instagram",
    width: 1080,
    height: 1920,
    fps: 30,
    safe: margins(instagram.formats.reel.ui),
  },
  post: {
    id: "post",
    platform: "instagram",
    width: 1080,
    height: 1350,
    fps: 30,
    safe: margins(instagram.formats.feed_video.ui),
  },
  tiktok: {
    id: "tiktok",
    platform: "tiktok",
    width: 1080,
    height: 1920,
    fps: 30,
    safe: margins(tiktok.formats.video.ui),
  },
  short: {
    id: "short",
    platform: "youtube_shorts",
    width: 1080,
    height: 1920,
    fps: 30,
    safe: margins(shorts.formats.short.ui),
  },
  landscape: {
    id: "landscape",
    platform: "none",
    width: 1920,
    height: 1080,
    fps: 30,
    safe: { top: 80, bottom: 80, left: 100, right: 100 },
  },
};

export const sec = (s: number, fps = 30) => Math.round(s * fps);
