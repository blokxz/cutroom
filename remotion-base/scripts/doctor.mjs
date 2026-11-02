#!/usr/bin/env node
/**
 * Render one frame of an example to prove the Remotion side works; prints JSON for tools/doctor.py.
 *   node scripts/doctor.mjs [CompositionId] [frame]
 */
import { bundle } from "@remotion/bundler";
import { openBrowser, renderStill, selectComposition } from "@remotion/renderer";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { config, remotionRoot as root } from "./config.mjs";
import { syncClients } from "./sync-clients.mjs";

const [id = "SamplePost", frame = "100"] = process.argv.slice(2);
const result = { composition: id, frame: Number(frame), browser: config.browserExecutable ?? "remotion-managed", ok: false };
const t0 = Date.now();
try {
  syncClients();
  const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts") });
  result.bundle_s = (Date.now() - t0) / 1000;
  const browser = await openBrowser("chrome", { browserExecutable: config.browserExecutable });
  try {
    const composition = await selectComposition({ serveUrl, id, inputProps: {}, browserExecutable: config.browserExecutable, puppeteerInstance: browser });
    const out = path.join(os.tmpdir(), `cutroom-doctor-${Date.now()}.png`);
    const t1 = Date.now();
    await renderStill({ composition, serveUrl, frame: Number(frame), output: out, browserExecutable: config.browserExecutable, puppeteerInstance: browser });
    result.still_s = (Date.now() - t1) / 1000;
    result.still = out;
    result.size = `${composition.width}x${composition.height}`;
    result.ok = fs.existsSync(out) && fs.statSync(out).size > 0;
  } finally {
    await browser.close({ silent: true });
  }
} catch (e) {
  result.error = String(e?.message ?? e).split("\n")[0];
}
result.total_s = (Date.now() - t0) / 1000;
console.log("__DOCTOR__" + JSON.stringify(result));
