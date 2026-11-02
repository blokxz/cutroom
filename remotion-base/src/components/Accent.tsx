import React from "react";
import { splitAccent } from "../lib/brief";

/**
 * Renders "Plain part / accent part": the part after " / " is italic in `color`.
 * `br` breaks the line before the accent instead of a space.
 */
export const Accent: React.FC<{
  text: string;
  color: string;
  br?: boolean;
}> = ({ text, color, br }) => {
  const [a, b] = splitAccent(text);
  return (
    <>
      {a}
      {b ? br ? <br /> : " " : null}
      {b ? <i style={{ color }}>{b}</i> : null}
    </>
  );
};
