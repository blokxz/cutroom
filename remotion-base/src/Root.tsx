import React from "react";
import { Composition, Folder } from "remotion";
import { FORMATS } from "./lib/formats";
import { SAMPLE_POST_FRAMES, SamplePost } from "./examples/sample/SamplePost";
import {
  KeyDemo,
  LightArcDemo,
  MOVES_DEMO_FRAMES,
  PathCameraDemo,
  PostcardDropDemo,
  WrittenPostcardDemo,
} from "./examples/moves/MovesDemo";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Folder name="examples">
        <Composition
          id="SamplePost"
          component={SamplePost}
          width={FORMATS.post.width}
          height={FORMATS.post.height}
          fps={FORMATS.post.fps}
          durationInFrames={SAMPLE_POST_FRAMES}
          defaultProps={{ showSafeZones: false }}
        />
      </Folder>
      {/* Studio-only: one move each, for judging and tuning (not pieces, no brief) */}
      <Folder name="moves">
        <Composition
          id="MovesDemo-PostcardDrop"
          component={PostcardDropDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.postcards}
        />
        <Composition
          id="MovesDemo-LightArc"
          component={LightArcDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.light}
        />
        <Composition
          id="MovesDemo-PathCamera"
          component={PathCameraDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.path}
        />
        <Composition
          id="MovesDemo-Key"
          component={KeyDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.key}
        />
        <Composition
          id="MovesDemo-WrittenPostcard"
          component={WrittenPostcardDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.written}
        />
      </Folder>
    </>
  );
};
