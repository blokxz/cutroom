/**
 * Environment config for the render pipeline.
 *
 * Values come from (first match wins): the process environment, then `.env` at the
 * repo root (see `.env.example`), then auto-detection. Nothing machine-specific is
 * hardcoded, so the same kit runs in a container, on macOS, Linux or Windows.
 *
 *   REMOTION_BROWSER      path to a Chromium / headless_shell binary. Unset → Remotion
 *                         downloads and manages its own headless shell (first render only).
 *   CUTROOM_PYTHON        Python interpreter for tools/ (default: python3, or python on Windows)
 *   CUTROOM_CONCURRENCY   frames rendered in parallel (number or "50%"; default: Remotion's choice)
 *   FFMPEG / FFPROBE      used by the Python tools (default: whatever is on PATH)
 *   CUTROOM_BLUR_ENGINE   "camera" (default) or "canvas" (HTML-in-canvas, needs Chromium 149+;
 *                         check with scripts/blur-ab.mjs first)
 */
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
export const remotionRoot = path.resolve(here, "..");
export const repoRoot = path.resolve(remotionRoot, "..");
export const toolsDir = path.join(repoRoot, "tools");

const parseEnvFile = (file) => {
  const out = {};
  if (!fs.existsSync(file)) return out;
  for (const line of fs.readFileSync(file, "utf8").split(/\r?\n/)) {
    const m = line.match(/^\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$/);
    if (!m || line.trim().startsWith("#")) continue;
    out[m[1]] = m[2].replace(/^(['"])(.*)\1$/, "$2");
  }
  return out;
};

const fileEnv = parseEnvFile(path.join(repoRoot, ".env"));
const get = (k) => process.env[k] || fileEnv[k] || "";

// export .env values so child processes (python tools → ffmpeg) see them too
for (const [k, v] of Object.entries(fileEnv)) if (!process.env[k]) process.env[k] = v;

const findBrowser = () => {
  const explicit = get("REMOTION_BROWSER");
  if (explicit) {
    if (!fs.existsSync(explicit)) throw new Error(`REMOTION_BROWSER points to a missing file: ${explicit}`);
    return explicit;
  }
  // a Playwright-managed headless shell, if one is installed (containers, CI)
  const roots = [process.env.PLAYWRIGHT_BROWSERS_PATH, "/opt/pw-browsers", path.join(os.homedir(), ".cache/ms-playwright")].filter(Boolean);
  for (const r of roots) {
    if (!fs.existsSync(r)) continue;
    for (const d of fs.readdirSync(r).filter((n) => n.startsWith("chromium_headless_shell")).sort().reverse()) {
      for (const sub of ["chrome-linux/headless_shell", "chrome-headless-shell-linux64/chrome-headless-shell"]) {
        const p = path.join(r, d, sub);
        if (fs.existsSync(p)) return p;
      }
    }
  }
  return null; // let Remotion download its own
};

const findPython = () => {
  const explicit = get("CUTROOM_PYTHON");
  if (explicit) return explicit;
  for (const cand of process.platform === "win32" ? ["python", "py", "python3"] : ["python3", "python"]) {
    const r = spawnSync(cand, ["--version"], { encoding: "utf8" });
    if (r.status === 0) return cand;
  }
  throw new Error("Python 3 not found — install it or set CUTROOM_PYTHON in .env");
};

const parseConcurrency = (v) => (!v ? null : /%$/.test(v) ? v : Number(v));

export const config = {
  browserExecutable: findBrowser(),
  python: findPython(),
  concurrency: parseConcurrency(get("CUTROOM_CONCURRENCY")),
  blurEngine: get("CUTROOM_BLUR_ENGINE") === "canvas" ? "canvas" : "camera",
};

/** Run a tool from tools/ with the configured Python. */
export const runTool = (script, args, opts = {}) =>
  spawnSync(config.python, [path.join(toolsDir, script), ...args], { stdio: "inherit", ...opts });
