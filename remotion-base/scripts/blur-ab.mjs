#!/usr/bin/env node
/**
 * A/B the two motion-blur engines on the same frames.
 *
 *   node scripts/blur-ab.mjs <CompositionId> <frame> [<frame>...] [--samples 12]
 *
 * Writes out/blur-ab/<id>-<frame>-camera.png and -canvas.png and prints the render time of each.
 * The canvas engine needs Chromium 149+ with HTML-in-canvas (Remotion's own headless shell).
 * Set CUTROOM_BLUR_ENGINE=canvas in .env once it looks right on your machine.
 */
import { bundle } from "@remotion/bundler";
import { openBrowser, renderStill, selectComposition } from "@remotion/renderer";
import fs from "node:fs";
import path from "node:path";
import { config, remotionRoot as root } from "./config.mjs";

const args = process.argv.slice(2);
const si = args.indexOf("--samples");
const samples = si >= 0 ? Number(args[si + 1]) : 12;
const [id, ...frames] = args.filter((a, i) => !a.startsWith("--") && i !== si + 1);
if (!id || !frames.length) {
  console.error("usage: node scripts/blur-ab.mjs <CompositionId> <frame> [<frame>...] [--samples 12]");
  process.exit(2);
}
const out = path.join(root, "out", "blur-ab");
fs.mkdirSync(out, { recursive: true });
const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts") });
const { browserExecutable } = config;
const browser = await openBrowser("chrome", { browserExecutable });
try {
  for (const engine of ["camera", "canvas"]) {
    const inputProps = { blurEngine: engine, blurSamples: samples };
    const composition = await selectComposition({ serveUrl, id, inputProps, browserExecutable, puppeteerInstance: browser });
    for (const f of frames) {
      const t = Date.now();
      try {
        await renderStill({ composition, serveUrl, frame: Number(f), output: path.join(out, `${id}-${f}-${engine}.png`), inputProps, browserExecutable, puppeteerInstance: browser });
        console.log(`${engine.padEnd(6)} frame ${f}: ${Date.now() - t} ms`);
      } catch (e) {
        console.log(`${engine.padEnd(6)} frame ${f}: failed — ${String(e.message ?? e).split("\n")[0]}`);
      }
    }
  }
} finally {
  await browser.close({ silent: true });
}
