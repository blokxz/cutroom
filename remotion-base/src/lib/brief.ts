// The part of a brief (schemas/brief.schema.json) a composition reads.
// scripts/render.mjs --brief passes the whole brief as the `brief` input prop.
import React, { createContext, useContext } from "react";

export type Brief = {
  id: string;
  client: string;
  format: string;
  duration_s?: number;
  goal?: string;
  cta?: { text?: string; contact?: string };
  copy?: { headline?: string; subtitle?: string; lines?: string[] };
};

/** "Plain part / accent part" → [plain, accent]. The slash marks where the accent (italic, colour) starts. */
export const splitAccent = (text: string): [string, string] => {
  const i = text.indexOf(" / ");
  return i < 0 ? [text, ""] : [text.slice(0, i), text.slice(i + 3)];
};

/**
 * Every brief-driven text a composition shows. Each composition declares its own
 * defaults (what Studio shows without a brief); a brief overrides them field by field.
 */
export type Copy = {
  headline: string;
  subtitle: string;
  /** extra lines, by position (labels, words, a CTA line…) — the composition decides what each one is */
  lines: string[];
  /** brief.cta.text: what the viewer must do */
  ctaText: string;
  /** brief.cta.contact, or the client's contact */
  contact: string;
};

/** The client's contact (CONTACT in src/clients/<slug>/brand.ts) — WhatsApp first. */
export type ClientContact = Readonly<Record<string, string | undefined>>;

/** Contact shown on screen: the brief's cta.contact, else the client's WhatsApp, else its first contact. */
export const contactFrom = (
  brief: Pick<Brief, "cta"> | undefined,
  contact: ClientContact,
): string =>
  brief?.cta?.contact ||
  contact.whatsapp ||
  Object.values(contact).find((v): v is string => Boolean(v)) ||
  "";

/**
 * Merge a brief over a composition's defaults. Empty strings count as missing.
 * Lines merge by position: brief line i replaces default line i; extra brief lines are kept.
 */
export const copyFrom = (
  brief: Pick<Brief, "copy" | "cta"> | undefined,
  defaults: Copy,
): Copy => {
  const lines = brief?.copy?.lines ?? [];
  const n = Math.max(lines.length, defaults.lines.length);
  return {
    headline: brief?.copy?.headline || defaults.headline,
    subtitle: brief?.copy?.subtitle || defaults.subtitle,
    lines: Array.from(
      { length: n },
      (_, i) => lines[i] || defaults.lines[i] || "",
    ),
    ctaText: brief?.cta?.text || defaults.ctaText,
    contact: brief?.cta?.contact || defaults.contact,
  };
};

const EMPTY: Copy = {
  headline: "",
  subtitle: "",
  lines: [],
  ctaText: "",
  contact: "",
};
const CopyCtx = createContext<Copy>(EMPTY);

/** Put at the root of a composition: `<CopyProvider brief={brief} defaults={DEFAULT_COPY}>`. */
export const CopyProvider: React.FC<{
  brief?: Brief;
  defaults: Copy;
  children: React.ReactNode;
}> = ({ brief, defaults, children }) =>
  React.createElement(
    CopyCtx.Provider,
    { value: copyFrom(brief, defaults) },
    children,
  );

/** The merged copy, anywhere under <CopyProvider>. */
export const useCopy = (): Copy => useContext(CopyCtx);
