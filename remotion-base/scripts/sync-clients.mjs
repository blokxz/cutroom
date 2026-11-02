#!/usr/bin/env node
// Mirror every clients/<slug>/assets/** into public/clients/<slug>/**.
// A file is copied when its size or modification time differs from the copy (so a replaced
// photo with an older timestamp is still picked up); files removed from assets/ are removed
// from public/ too. Runs before each render (render.mjs) and before Studio (npm run dev).
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

const mirror = (src, dst) => {
  fs.mkdirSync(dst, { recursive: true });
  const wanted = new Set();
  for (const e of fs.readdirSync(src, { withFileTypes: true })) {
    wanted.add(e.name);
    const s = path.join(src, e.name);
    const d = path.join(dst, e.name);
    if (e.isDirectory()) {
      mirror(s, d);
      continue;
    }
    const ss = fs.statSync(s);
    const ds = fs.existsSync(d) ? fs.statSync(d) : null;
    if (!ds || ds.size !== ss.size || Math.floor(ds.mtimeMs) !== Math.floor(ss.mtimeMs)) {
      fs.copyFileSync(s, d);
      fs.utimesSync(d, ss.atime, ss.mtime); // keep the source timestamp: next comparison is exact
    }
  }
  for (const name of fs.readdirSync(dst)) {
    if (!wanted.has(name)) fs.rmSync(path.join(dst, name), { recursive: true, force: true });
  }
};

export const syncClients = () => {
  const clientsDir = path.resolve(root, "../clients");
  const publicClients = path.join(root, "public/clients");
  if (!fs.existsSync(clientsDir)) return clientsDir;
  const slugs = fs.readdirSync(clientsDir).filter((slug) => fs.existsSync(path.join(clientsDir, slug, "assets")));
  for (const slug of slugs) mirror(path.join(clientsDir, slug, "assets"), path.join(publicClients, slug));
  if (fs.existsSync(publicClients)) {
    for (const name of fs.readdirSync(publicClients)) {
      if (!slugs.includes(name)) fs.rmSync(path.join(publicClients, name), { recursive: true, force: true });
    }
  }
  return clientsDir;
};

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  syncClients();
  console.log("client assets synced into public/clients/");
}
