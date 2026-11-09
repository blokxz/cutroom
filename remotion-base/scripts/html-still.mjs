/**
 * Screenshot an HTML/SVG page at a fixed size, for covers and other designs that are not video.
 *
 *   node scripts/html-still.mjs <page.html> <out.jpg|png> [--width 1080] [--height 1350] [--query "a=b&c=d"]
 *
 * Runs the same headless Chrome as render.mjs (config.browserExecutable) from the command line; the
 * virtual time budget gives fonts and images time to load. JPEG output is converted from the PNG
 * with Pillow (already a requirement of the Python tools).
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import url from "node:url";
import { spawnSync } from "node:child_process";
import { config } from "./config.mjs";

const args = process.argv.slice(2);
const opt = (name, def) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : def;
};
const pos = args.filter((a, i) => !a.startsWith("--") && !(i > 0 && args[i - 1].startsWith("--")));
if (pos.length < 2) {
  console.error("usage: html-still.mjs <page.html> <out.jpg|png> [--width N] [--height N] [--query a=b]");
  process.exit(2);
}
const [page, out] = pos;
const width = Number(opt("width", 1080));
const height = Number(opt("height", 1350));
const query = opt("query", "");
const target = url.pathToFileURL(path.resolve(page)).href + (query ? `?${query}` : "");
if (!config.browserExecutable) {
  console.error("no browser found: set CUTROOM_BROWSER (see .env.example) or run python3 tools/setup.py");
  process.exit(1);
}

const wantJpeg = !out.toLowerCase().endsWith(".png");
const png = wantJpeg ? path.join(fs.mkdtempSync(path.join(os.tmpdir(), "cutroom-still-")), "shot.png") : path.resolve(out);
const r = spawnSync(
  config.browserExecutable,
  ["--headless", "--no-sandbox", "--hide-scrollbars", "--allow-file-access-from-files", "--force-device-scale-factor=1",
   `--window-size=${width},${height}`, "--virtual-time-budget=4000", `--screenshot=${png}`, target],
  { encoding: "utf8" },
);
if (r.status !== 0 || !fs.existsSync(png)) {
  console.error(r.stderr || "the browser did not write a screenshot");
  process.exit(1);
}
if (wantJpeg) {
  const py = process.env.CUTROOM_PYTHON || (process.platform === "win32" ? "python" : "python3");
  const c = spawnSync(py, ["-c", "import sys;from PIL import Image;Image.open(sys.argv[1]).convert('RGB').save(sys.argv[2],quality=92)", png, path.resolve(out)], { encoding: "utf8" });
  if (c.status !== 0) {
    console.error(c.stderr);
    process.exit(1);
  }
}
console.log("wrote", out);
