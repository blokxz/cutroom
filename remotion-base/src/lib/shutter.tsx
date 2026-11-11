/**
 * Time offset for the whole-frame shutter: render.mjs renders a piece several times, each pass shifted by a
 * fraction of a frame (input prop `timeOffset`, in frames), and averages the passes in linear light. The same
 * mechanism renders 60 fps from a piece timed at 30: two passes, offsets 0 and 0.5, interleaved.
 *
 *   withTimeOffset(Component)   the component with every useCurrentFrame() inside shifted by `timeOffset`
 */
import React from "react";
import { Freeze, getInputProps, useCurrentFrame } from "remotion";

export const timeOffset = (): number => {
  try {
    const v = Number(
      (getInputProps() as { timeOffset?: number }).timeOffset ?? 0,
    );
    return Number.isFinite(v) ? v : 0;
  } catch {
    return 0;
  }
};

// one wrapper per component, so Root can call withTimeOffset inline without remounting anything
const cache = new WeakMap<object, React.FC<never>>();

export function withTimeOffset<P extends object>(
  Component: React.ComponentType<P>,
): React.FC<P> {
  const hit = cache.get(Component as object);
  if (hit) return hit as unknown as React.FC<P>;
  const Shifted: React.FC<P> = (props) => {
    const frame = useCurrentFrame();
    const off = timeOffset();
    if (!off) return <Component {...props} />;
    return (
      <Freeze frame={frame + off}>
        <Component {...props} />
      </Freeze>
    );
  };
  Shifted.displayName = `withTimeOffset(${Component.displayName ?? Component.name ?? "Component"})`;
  cache.set(Component as object, Shifted as unknown as React.FC<never>);
  return Shifted;
}
