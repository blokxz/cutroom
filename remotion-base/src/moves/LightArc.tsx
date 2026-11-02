/**
 * LightArc — a disc of light that travels an arc across the frame while its
 * colour moves through the day (morning → afternoon → night). An iris can be
 * born from the disc, so the next scene opens out of the light itself.
 *
 *   arcPoint(arc, u)        position on the arc (u: 0 = start, 1 = end; apex at 0.5)
 *   lightColor(u, stops)    colour at u through evenly spaced stops (DAY_LIGHT by default)
 *   <LightArc>              renders the disc (+ soft halo) and, optionally, an iris from it
 *
 * The caller drives `u` with its own curve — usually a piecewise one that
 * reaches each stop as a scene opens and rests while the scene holds.
 */
import React from "react";
import { interpolateColors } from "remotion";
import { Track } from "../components/Track";
import { IrisOpen } from "./index";

export type Arc = {
  /** start and end x */
  x0: number;
  x1: number;
  /** baseline y at both ends */
  y: number;
  /** height of the apex above the baseline */
  lift: number;
};

export const arcPoint = (arc: Arc, u: number) => ({
  x: arc.x0 + (arc.x1 - arc.x0) * u,
  y: arc.y - arc.lift * Math.sin(Math.PI * Math.max(0, Math.min(1, u))),
});

/** Morning gold → warm afternoon → dusk rose → night blue. Override with brand-tinted stops. */
export const DAY_LIGHT = ["#F7DFA4", "#F2B160", "#D9826E", "#7F8DBF"];

export const lightColor = (u: number, stops: string[] = DAY_LIGHT) => {
  if (stops.length === 1) return stops[0];
  const at = stops.map((_, i) => i / (stops.length - 1));
  return interpolateColors(Math.max(0, Math.min(1, u)), at, stops);
};

export const LightArc: React.FC<{
  arc: Arc;
  u: number;
  size?: number;
  colors?: string[];
  /** overall opacity (born / leaving) */
  opacity?: number;
  /** extra scale of the disc (a pop on arrival) */
  scale?: number;
  /** halo pulse 0–1 (drive it with the frame for a slow breath; 0 = no halo) */
  halo?: number;
  trackId?: string;
  blurred?: boolean;
  /** an iris opening out of the disc: progress + what it reveals */
  iris?: { p: number; trackId?: string; children: React.ReactNode };
}> = ({
  arc,
  u,
  size = 64,
  colors = DAY_LIGHT,
  opacity = 1,
  scale = 1,
  halo = 0,
  trackId,
  blurred = false,
  iris,
}) => {
  const p = arcPoint(arc, u);
  const col = lightColor(u, colors);
  const d = size * scale;
  const disc = (
    <div
      style={{
        position: "absolute",
        left: p.x - d / 2,
        top: p.y - d / 2,
        width: d,
        height: d,
        borderRadius: "50%",
        opacity,
        background: `radial-gradient(circle at 38% 34%, rgba(255,255,255,0.6), ${col} 64%)`,
        boxShadow: `0 0 ${size * 0.6}px ${size * 0.15}px ${col}`,
      }}
    />
  );
  return (
    <>
      {halo > 0 ? (
        <div
          style={{
            position: "absolute",
            left: p.x - d,
            top: p.y - d,
            width: 2 * d,
            height: 2 * d,
            borderRadius: "50%",
            border: `2px solid ${col}`,
            opacity: opacity * (1 - halo) * 0.5,
            transform: `scale(${0.5 + halo * 0.8})`,
          }}
        />
      ) : null}
      {trackId ? (
        <Track id={trackId} kind="shape" blurred={blurred}>
          {disc}
        </Track>
      ) : (
        disc
      )}
      {iris ? (
        <IrisOpen
          p={iris.p}
          cx={p.x}
          cy={p.y}
          trackId={iris.trackId}
          blurred={blurred}
        >
          {iris.children}
        </IrisOpen>
      ) : null}
    </>
  );
};
