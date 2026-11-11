import React from "react";
import { Composition, Folder } from "remotion";
import { FORMATS } from "./lib/formats";
import { SAMPLE_POST_FRAMES, SamplePost } from "./examples/sample/SamplePost";
import {
  TERMAS_ARROYO_FRAMES,
  TermasArroyo,
} from "./examples/termas/TermasArroyo";
import {
  TERMAS_CINTA_FRAMES,
  TermasCinta,
} from "./examples/termas/TermasCinta";
import { ESCAPADA_FRAMES, Escapada } from "./examples/termas/Escapada";
import { withTimeOffset } from "./lib/shutter";
import {
  CAROUSEL_DEFAULTS,
  COVER_DEFAULTS,
  CarouselCover,
  CarouselSlide,
} from "./examples/sample/CarouselSlide";
import {
  SAMPLE_DATES_FRAMES,
  SampleDates,
} from "./examples/sample/SampleDates";
import {
  BeltDemo,
  CalendarDemo,
  CauseEffectDemo,
  DepthDemo,
  DominoesDemo,
  FilmStripDemo,
  GatherDemo,
  SilkDemo,
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
          component={withTimeOffset(SamplePost)}
          width={FORMATS.post.width}
          height={FORMATS.post.height}
          fps={FORMATS.post.fps}
          durationInFrames={SAMPLE_POST_FRAMES}
          defaultProps={{ showSafeZones: false }}
        />
        <Composition
          id="CarouselSlide"
          component={withTimeOffset(CarouselSlide)}
          width={FORMATS.post.width}
          height={FORMATS.post.height}
          fps={FORMATS.post.fps}
          durationInFrames={1}
          defaultProps={CAROUSEL_DEFAULTS}
        />
        <Composition
          id="CarouselCover"
          component={withTimeOffset(CarouselCover)}
          width={FORMATS.post.width}
          height={FORMATS.post.height}
          fps={FORMATS.post.fps}
          durationInFrames={1}
          defaultProps={COVER_DEFAULTS}
        />
        <Composition
          id="TermasArroyo"
          component={withTimeOffset(TermasArroyo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={TERMAS_ARROYO_FRAMES}
          defaultProps={{ showSafeZones: false }}
        />
        <Composition
          id="TermasCinta"
          component={withTimeOffset(TermasCinta)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={TERMAS_CINTA_FRAMES}
          defaultProps={{ showSafeZones: false }}
        />
        <Composition
          id="Escapada"
          component={withTimeOffset(Escapada)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={ESCAPADA_FRAMES}
          defaultProps={{ showSafeZones: false }}
        />
        <Composition
          id="SampleDates"
          component={withTimeOffset(SampleDates)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={SAMPLE_DATES_FRAMES}
          defaultProps={{ showSafeZones: false }}
        />
      </Folder>
      {/* Studio-only: one move each, for judging and tuning (not pieces, no brief) */}
      <Folder name="moves">
        <Composition
          id="MovesDemo-PostcardDrop"
          component={withTimeOffset(PostcardDropDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.postcards}
        />
        <Composition
          id="MovesDemo-LightArc"
          component={withTimeOffset(LightArcDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.light}
        />
        <Composition
          id="MovesDemo-PathCamera"
          component={withTimeOffset(PathCameraDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.path}
        />
        <Composition
          id="MovesDemo-Key"
          component={withTimeOffset(KeyDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.key}
        />
        <Composition
          id="MovesDemo-WrittenPostcard"
          component={withTimeOffset(WrittenPostcardDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.written}
        />
        <Composition
          id="MovesDemo-LightFlood"
          component={withTimeOffset(LightFloodDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.flood}
        />
        <Composition
          id="MovesDemo-Belt"
          component={withTimeOffset(BeltDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.belt}
        />
        <Composition
          id="MovesDemo-ObjectWipe"
          component={withTimeOffset(ObjectWipeDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.wipe}
        />
        <Composition
          id="MovesDemo-Calendar"
          component={withTimeOffset(CalendarDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.calendar}
        />
        <Composition
          id="MovesDemo-FilmStrip"
          component={withTimeOffset(FilmStripDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.strip}
        />
        <Composition
          id="MovesDemo-Dominoes"
          component={withTimeOffset(DominoesDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.dominoes}
        />
        <Composition
          id="MovesDemo-CauseEffect"
          component={withTimeOffset(CauseEffectDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.cause}
        />
        <Composition
          id="MovesDemo-Depth"
          component={withTimeOffset(DepthDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.depth}
        />
        <Composition
          id="MovesDemo-Gather"
          component={withTimeOffset(GatherDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.gather}
        />
        <Composition
          id="MovesDemo-Silk"
          component={withTimeOffset(SilkDemo)}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.silk}
        />
      </Folder>
    </>
  );
};
