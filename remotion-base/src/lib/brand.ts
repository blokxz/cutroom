// Brand tokens. Each client's src/clients/<slug>/brand.ts is generated from
// clients/<slug>/client.json (python3 tools/brief.py client ts <slug>) — never invent a brand.
import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

export type Brand = {
  name: string;
  colors: {
    ground: string;
    paper: string;
    ink: string;
    soft: string;
    accent: string;
    accent2: string;
    line: string;
  };
  fonts: { display: string; text: string; script?: string };
};

export type FontFile = {
  family: string;
  file: string;
  weight?: string;
  style?: "normal" | "italic";
};

/**
 * Load a client's font files. Fonts live only in clients/<slug>/assets/fonts;
 * scripts/sync-clients.mjs copies them to public/clients/<slug>/fonts, so `dir`
 * is "clients/<slug>/fonts". Remotion waits for them before rendering.
 */
export const loadFonts = (files: FontFile[], dir: string) =>
  Promise.all(
    files.map((f) =>
      loadFont({
        family: f.family,
        url: staticFile(`${dir}/${f.file}`),
        weight: f.weight ?? "400",
        style: f.style ?? "normal",
      }),
    ),
  );
