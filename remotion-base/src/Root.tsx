import React from "react";
import { Composition, Folder } from "remotion";
import { FORMATS } from "./lib/formats";
import { SAMPLE_POST_FRAMES, SamplePost } from "./examples/sample/SamplePost";
import {
  BeltDemo,
  CalendarDemo,
  KeyDemo,
  LightArcDemo,
  LightFloodDemo,
  MOVES_DEMO_FRAMES,
  ObjectWipeDemo,
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
        <Composition
          id="MovesDemo-LightFlood"
          component={LightFloodDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.flood}
        />
        <Composition
          id="MovesDemo-Belt"
          component={BeltDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.belt}
        />
        <Composition
          id="MovesDemo-ObjectWipe"
          component={ObjectWipeDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.wipe}
        />
        <Composition
          id="MovesDemo-Calendar"
          component={CalendarDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.calendar}
        />
      </Folder>
    </>
  );
};
