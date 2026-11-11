#!/usr/bin/env node
/**
 * Render a composition, collect tracking data, export key stills and run the verifier.
 *
 *   node scripts/render.mjs <CompositionId> [--final] [--format story|reel|feed_video] [--platform instagram]
 *                                           [--out out] [--scale 2] [--concurrency 4] [--force] [--no-verify]
 *   node scripts/render.mjs --brief ../clients/<slug>/briefs/<id>.json [--final]
 *
 * --brief        takes the composition id, platform, format and reference from the brief, passes the
 *                brief to the composition as the `brief` prop (copy, CTA, contact) and writes to out/<brief id>/.
 * --final        high-quality encode (crf 14) from PNG frames + audio mastering to -16 LUFS / -1.5 dBTP, with a
 *                whole-frame shutter: the stretches that move are rendered again at fractions of a frame and
 *                averaged in linear light (tools/shutter.py). --shutter N sets the samples (default 4; 1 = off).
 * --fps60        (with --final) also write <id>-60.mp4 at 60 fps from the same piece (passes at +0.5 frame,
 *                interleaved). Verification runs on the 30 fps file.
 * --master-4k    a 2160x3840 (scale 2) final master for clients who ask for one, written as <id>-4k.mp4.
 *                Not verified against platform limits (it's above their 1920 px upload maximum): publish the 1080 final.
 * --preview      quick look while iterating: half size, no stills, no mastering, no verification; written as
 *                <id>-preview.mp4 and never counted by the pipeline gates.
 * --concurrency  frames rendered in parallel (number or "50%"); default CUTROOM_CONCURRENCY or Remotion's choice.
 * --force        render even if nothing changed since the last render (see cache below).
 * --print-key    print the cache key for the current inputs and exit (tools/pipeline.py uses it to spot stale renders).
 *
 * Cache: a render is skipped when the composition source, client assets, brief and options are identical
 * to the last render into the same folder (hash stored in out/<dir>/.render-cache.json). The verifier
 * still runs on the existing file.
 *
 * Machine-specific settings (browser, Python, concurrency) come from scripts/config.mjs (.env / env / auto).
 */
import { bundle } from "@remotion/bundler";
import { openBrowser, renderMedia, renderStill, selectComposition } from "@remotion/renderer";
import { spawnSync } from "node:child_process";
import crypto from "node:crypto";
import os from "node:os";
import fs from "node:fs";
import path from "node:path";
import { config, remotionRoot as root, repoRoot, runTool, toolsDir } from "./config.mjs";
import { syncClients } from "./sync-clients.mjs";

const args = process.argv.slice(2);
const flag = (n) => args.includes(`--${n}`);
const opt = (n, d) => {
  const i = args.indexOf(`--${n}`);
  return i >= 0 ? args[i + 1] : d;
};
const VALUED = ["--format", "--platform", "--out", "--scale", "--brief", "--concurrency", "--shutter"];
const valued = new Set(VALUED.filter((o) => args.includes(o)).flatMap((o) => [o, args[args.indexOf(o) + 1]]));
const briefPath = opt("brief") ? path.resolve(process.cwd(), opt("brief")) : null;
const brief = briefPath ? JSON.parse(fs.readFileSync(briefPath, "utf8")) : null;
const id = brief?.composition ?? args.find((a) => !a.startsWith("--") && !valued.has(a));
if (!id) {
  console.error(
    brief
      ? `brief ${briefPath} has no "composition" yet — build the composition, register it in Root.tsx and put its id in the brief`
      : "usage: node scripts/render.mjs <CompositionId> | --brief <brief.json>  [--final] [--format story] [--out out] [--scale 2] [--force] [--no-verify]",
  );
  process.exit(2);
}

const t0 = Date.now();
const secs = () => `${((Date.now() - t0) / 1000).toFixed(0)} s`;

// sync client assets: clients/<slug>/assets/** → public/clients/<slug>/**
const clientsDir = syncClients();

const master4k = flag("master-4k");
const final = flag("final") || master4k;
const preview = flag("preview") && !final;
const outDir = path.resolve(root, opt("out", brief ? `out/${brief.id}` : "out"));
const scale = preview ? 0.5 : master4k ? 2 : Number(opt("scale", "1"));
const concurrency = opt("concurrency") ? (/%$/.test(opt("concurrency")) ? opt("concurrency") : Number(opt("concurrency"))) : config.concurrency;
fs.mkdirSync(outDir, { recursive: true });
const { browserExecutable } = config;
// motion blur: engine from .env, samples by profile (finals get a smoother shutter than drafts)
const blurEngine = brief?.render?.blur_engine ?? config.blurEngine;
const blurSamples = final ? 12 : preview ? 3 : undefined;
// whole-frame shutter: finals render the moving stretches again at fractions of a frame and average the passes in
// linear light (tools/shutter.py); the in-DOM <MotionBlur> steps aside so nothing is blurred twice
const shutter = Math.max(1, Math.round(Number(opt("shutter", final && !preview ? "4" : "1"))));
const fps60 = flag("fps60") && final;
const multipass = shutter > 1 || fps60;
const blurProps = { blurEngine, ...(blurSamples ? { blurSamples } : {}), ...(multipass ? { shutterPasses: shutter } : {}) };
const inputProps = brief ? { track: true, brief, ...blurProps } : { track: true, ...blurProps };

const suffix = master4k ? "-4k" : final ? "" : preview ? "-preview" : "-draft";
const video = path.join(outDir, `${id}${suffix}.mp4`);
const trackFile = path.join(outDir, `${id}${suffix}.track.json`);

// ---------- cache key ----------
const walk = (dir, out = []) => {
  if (!fs.existsSync(dir)) return out;
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) walk(p, out);
    else out.push(p);
  }
  return out;
};
const cacheKey = () => {
  const h = crypto.createHash("sha256");
  // workflow fields of the brief (status, decisions, notes) don't change the picture
  // (delivery only steers the package; material is already reflected in assets)
  const { status, decisions, notes, delivery, material, ...picture } = brief ?? {};
  h.update(JSON.stringify({ id, final, scale, blurEngine, blurSamples, shutter, fps60, format: opt("format"), platform: opt("platform"), brief: picture }));
  // composition code: hash contents (small); assets: size + mtime (large)
  for (const f of [...walk(path.join(root, "src")), path.join(root, "package-lock.json")].sort()) {
    if (fs.existsSync(f)) h.update(f.slice(root.length)).update(fs.readFileSync(f));
  }
  for (const f of walk(path.join(root, "public")).sort()) {
    const s = fs.statSync(f);
    h.update(`${f.slice(root.length)}:${s.size}:${Math.floor(s.mtimeMs)}`);
  }
  return h.digest("hex");
};
const cacheFile = path.join(outDir, ".render-cache.json");
const readCache = () => {
  try {
    return JSON.parse(fs.readFileSync(cacheFile, "utf8"));
  } catch {
    return {};
  }
};
const key = cacheKey();
if (flag("print-key")) {
  console.log(key);
  process.exit(0);
}
const cache = readCache();
const cached = !flag("force") && cache[video]?.key === key && fs.existsSync(video) && fs.existsSync(trackFile);

let fmt = opt("format") ?? brief?.format ?? cache[video]?.format;
const platform = opt("platform") ?? brief?.platform ?? "instagram";
let mastered = cache[video]?.mastered;

if (cached) {
  console.log(`unchanged since last render — reusing ${path.relative(root, video)} (use --force to re-render)`);
} else {
  console.log(`bundling…`);
  const serveUrl = await bundle({ entryPoint: path.join(root, "src/index.ts") });
  // one browser for the whole run: composition selection, video and every still
  const browser = await openBrowser("chrome", { browserExecutable });
  try {
    const composition = await selectComposition({ serveUrl, id, inputProps, browserExecutable, puppeteerInstance: browser });
    const vertical = composition.width * 16 === composition.height * 9;
    // Instagram format names; other platforms let the verifier detect the format
    fmt ??= platform !== "instagram" ? "auto" : vertical ? (/reel/i.test(id) ? "reel" : "story") : "feed_video";

    const track = new Map();
    let beats = [];
    const onBrowserLog = ({ text }) => {
      if (text.startsWith("__TRACK__")) {
        const r = JSON.parse(text.slice(9));
        // boxes are measured in composition (CSS) pixels; the video is `scale` times larger
        for (const p of ["x", "y", "w", "h"]) r[p] = Math.round(r[p] * scale);
        const k = `${r.f}:${r.id}`;
        const prev = track.get(k);
        if (!prev || r.lf >= prev.lf) track.set(k, r); // with motion blur, keep the present sample
      } else if (text.startsWith("__BEATS__")) beats = JSON.parse(text.slice(9));
    };

    let last = -1;
    const tmp = multipass ? fs.mkdtempSync(path.join(os.tmpdir(), "cutroom-passes-")) : null;
    // the passes are large: remove them however the run ends
    if (tmp) process.on("exit", () => fs.rmSync(tmp, { recursive: true, force: true }));
    const pass0 = multipass ? path.join(tmp, "pass-0-0.mp4") : video;
    await renderMedia({
      composition,
      serveUrl,
      codec: "h264",
      crf: multipass ? 1 : final ? 14 : preview ? 26 : 20,
      // frames are captured as PNG for finals (Remotion's default JPEG at quality 80 compresses every frame once
      // before the encoder compresses it again: blocks in gradients and steam); drafts keep JPEG, at a higher quality
      imageFormat: final ? "png" : "jpeg",
      ...(final ? {} : { jpegQuality: 92 }),
      scale,
      outputLocation: pass0,
      inputProps,
      browserExecutable,
      puppeteerInstance: browser,
      concurrency,
      onBrowserLog,
      // limited-range 4:2:0 and a keyframe every 2 s: what social platforms process most predictably
      // (a multi-pass render keeps a near-lossless 4:4:4 intermediate; the blend writes the 4:2:0 file)
      pixelFormat: multipass ? "yuv444p" : "yuv420p",
      colorSpace: "bt709",
      gopSize: composition.fps * 2,
      onProgress: ({ progress }) => {
        const p = Math.floor(progress * 10);
        if (p !== last) {
          last = p;
          process.stdout.write(`\rrender ${p * 10}%`);
        }
      },
    });
    console.log(`\nwrote ${path.relative(root, pass0)} (${secs()})`);

    if (multipass) {
      const plan = spawnSync(config.python, [path.join(toolsDir, "shutter.py"), "plan", pass0], { encoding: "utf8" });
      if (plan.status !== 0) throw new Error(`shutter plan failed: ${plan.stderr}`);
      const { frames, ranges, moving } = JSON.parse(plan.stdout);
      const offs = [];
      for (let m = 0; m < (fps60 ? 2 : 1); m++)
        for (let j = 0; j < shutter; j++) offs.push({ m, j, offset: m / (fps60 ? 2 : 1) + (0.5 / (fps60 ? 2 : 1)) * (j / shutter) });
      const passes = [{ m: 0, j: 0, start: 0, end: frames - 1, path: pass0 }];
      for (const o of offs) {
        if (o.m === 0 && o.j === 0) continue;
        // a sub-frame's first sample covers the whole piece; the other samples only where something moves
        const spans = o.j === 0 ? [[0, frames - 1]] : ranges;
        for (const [a, b] of spans) {
          const file = path.join(tmp, `pass-${o.m}-${o.j}-${a}.mp4`);
          await renderMedia({
            composition, serveUrl, codec: "h264", crf: 1, pixelFormat: "yuv444p", imageFormat: "png", scale,
            frameRange: [a, b], outputLocation: file, muted: true, browserExecutable, puppeteerInstance: browser, concurrency,
            inputProps: { ...inputProps, track: false, timeOffset: o.offset },
          });
          passes.push({ m: o.m, j: o.j, start: a, end: b, path: file });
        }
      }
      console.log(`shutter: ${shutter} samples, ${moving}/${frames} frames moving, ${passes.length} passes (${secs()})`);
      const blend = (mult, out) => {
        const pass = passes.filter((p) => p.m < mult).flatMap((p) => ["--pass", `${p.m}:${p.j}:${p.start}:${p.end}:${p.path}`]);
        const r = spawnSync(config.python, [path.join(toolsDir, "shutter.py"), "blend", "--frames", String(frames), "--fps", String(composition.fps),
          "--mult", String(mult), "--out", out, "--audio", pass0, "--crf", "14", ...pass], { stdio: "inherit" });
        if (r.status !== 0) throw new Error("shutter blend failed");
      };
      // fps60 needs every sub-frame 1 pass; the 30 fps file uses sub-frame 0 only
      blend(1, video);
      if (fps60) blend(2, video.replace(/\.mp4$/, "-60.mp4"));
      fs.rmSync(tmp, { recursive: true, force: true });
      console.log(`wrote ${path.relative(root, video)}${fps60 ? " and the 60 fps copy" : ""} (${secs()})`);
    }

    fs.writeFileSync(
      trackFile,
      JSON.stringify({ width: composition.width * scale, height: composition.height * scale, fps: composition.fps, scale, shutter, beats, records: [...track.values()] }),
    );
    console.log(`wrote ${path.relative(root, trackFile)} (${track.size} records, ${beats.length} beats)`);

    // stills: the settled middle of each beat, plus the final frame (for the client / thumbnails)
    const ends = [...beats.map((b) => b.f), composition.durationInFrames];
    const stillFrames = preview ? [] : [...new Set([...beats.map((b, i) => Math.floor((b.f + ends[i + 1]) / 2)), composition.durationInFrames - 1])];
    for (const f of stillFrames) {
      const file = path.join(outDir, `${id}${suffix}-f${String(f).padStart(4, "0")}.png`);
      await renderStill({ composition, serveUrl, frame: f, output: file, inputProps: brief ? { brief, ...blurProps } : { ...blurProps }, browserExecutable, puppeteerInstance: browser, scale });
    }
    console.log(`wrote ${stillFrames.length} stills (${secs()})`);
  } finally {
    await browser.close({ silent: true });
  }

  // audio mastered to -16 LUFS / -1.5 dBTP on drafts too, so the draft's loudness verdict matches the final's
  const m = preview ? { status: 0 } : runTool("master.py", [video, "--out", video]);
  const v60 = video.replace(/\.mp4$/, "-60.mp4");
  if (fps60 && fs.existsSync(v60)) runTool("master.py", [v60, "--out", v60]);
  mastered = !preview && m.status === 0;
  if (!mastered && !preview) console.warn("mastering failed — keeping the unmastered file (the pipeline will not deliver it)");
  fs.writeFileSync(cacheFile, JSON.stringify({ ...readCache(), [video]: { key, format: fmt, mastered, at: new Date().toISOString() } }, null, 2));
}

if (master4k) console.log("4K master: not verified against platform limits (above their 1920 px upload maximum) — publish the 1080 final");
if (!flag("no-verify") && !preview && !master4k) {
  const r = runTool("verify.py", [
    video,
    "--platform", platform,
    "--format", fmt ?? "auto",
    "--track", trackFile,
    "--sheet", video.replace(/\.mp4$/, "-sheet.png"),
    ...(brief?.reference ? ["--ref", path.join(clientsDir, brief.client, brief.reference)] : []),
  ]);
  // record the verdict next to the cache entry: the pipeline (tools/pipeline.py) gates review/delivery on it
  const c = readCache();
  if (c[video]) fs.writeFileSync(cacheFile, JSON.stringify({ ...c, [video]: { ...c[video], verify: r.status === 0 ? "pass" : "fail", verified_at: new Date().toISOString() } }, null, 2));
  console.log(`done in ${secs()}`);
  process.exit(r.status ?? 1);
}
console.log(`done in ${secs()} (repo: ${path.relative(process.cwd(), repoRoot) || "."})`);
