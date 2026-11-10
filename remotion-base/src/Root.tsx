import React from "react";
import { Composition, Folder } from "remotion";
import { FORMATS } from "./lib/formats";
import { SAMPLE_POST_FRAMES, SamplePost } from "./examples/sample/SamplePost";
import { TERMAS_ARROYO_FRAMES, TermasArroyo } from "./examples/termas/TermasArroyo";
import { TERMAS_CINTA_FRAMES, TermasCinta } from "./examples/termas/TermasCinta";
import { ESCAPADA_FRAMES, Escapada } from "./examples/termas/Escapada";
import { CAROUSEL_DEFAULTS, COVER_DEFAULTS, CarouselCover, CarouselSlide } from "./examples/sample/CarouselSlide";
import { SAMPLE_DATES_FRAMES, SampleDates } from "./examples/sample/SampleDates";
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
          component={SamplePost}
          width={FORMATS.post.width}
          height={FORMATS.post.height}
          fps={FORMATS.post.fps}
          durationInFrames={SAMPLE_POST_FRAMES}
          defaultProps={{ showSafeZones: false }}
        />
        <Composition
          id="CarouselSlide"
          component={CarouselSlide}
          width={FORMATS.post.width}
          height={FORMATS.post.height}
          fps={FORMATS.post.fps}
          durationInFrames={1}
          defaultProps={CAROUSEL_DEFAULTS}
        />
        <Composition
          id="CarouselCover"
          component={CarouselCover}
          width={FORMATS.post.width}
          height={FORMATS.post.height}
          fps={FORMATS.post.fps}
          durationInFrames={1}
          defaultProps={COVER_DEFAULTS}
        />
        <Composition
          id="TermasArroyo"
          component={TermasArroyo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={TERMAS_ARROYO_FRAMES}
          defaultProps={{ showSafeZones: false }}
        />
        <Composition
          id="TermasCinta"
          component={TermasCinta}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={TERMAS_CINTA_FRAMES}
          defaultProps={{ showSafeZones: false }}
        />
        <Composition
          id="Escapada"
          component={Escapada}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={ESCAPADA_FRAMES}
          defaultProps={{ showSafeZones: false }}
        />
        <Composition
          id="SampleDates"
          component={SampleDates}
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
        <Composition
          id="MovesDemo-FilmStrip"
          component={FilmStripDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.strip}
        />
        <Composition
          id="MovesDemo-Dominoes"
          component={DominoesDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.dominoes}
        />
        <Composition
          id="MovesDemo-CauseEffect"
          component={CauseEffectDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.cause}
        />
        <Composition
          id="MovesDemo-Depth"
          component={DepthDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.depth}
        />
        <Composition
          id="MovesDemo-Gather"
          component={GatherDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.gather}
        />
        <Composition
          id="MovesDemo-Silk"
          component={SilkDemo}
          width={FORMATS.reel.width}
          height={FORMATS.reel.height}
          fps={FORMATS.reel.fps}
          durationInFrames={MOVES_DEMO_FRAMES.silk}
        />
      </Folder>
    </>
  );
};
