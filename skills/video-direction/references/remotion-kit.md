# Remotion kit (`remotion-base/src/`) [C-05 G-04 G-08 R-06 R-08 R-09 R-10 R-15]

## Layout

| Path | Holds |
|---|---|
| `lib/` | `formats` (FORMATS + safe zones), `motion` (`EASE`, `tween`, `land`, `drift`), `brief.ts` (`useCopy`, `CopyProvider`) |
| `moves/` | carry moves (below); pure math exported + unit-tested |
| `components/` | `Camera`, `MotionBlur`, `Track`/`Beats`/`TrackRoot`, `SafeZones`, `Music`, `Accent`, `Paper` |
| `clients/<slug>/` | generated `brand.ts` (`CLIENT`, `CONTACT`, `asset()`) + compositions |
| `examples/` | `sample/SamplePost.tsx` (tests/CI only, G-09), `moves/MovesDemo.tsx` (Studio demos `MovesDemo-*`) |
| `Root.tsx` | composition registry |

## Moves (take a progress value; you choose the curve)

| Move | Exports | Use |
|---|---|---|
| core | `Morph`, `IrisOpen` (`trackId`), `MaskReveal`, `SplitText`, `Typewriter`, `pushThrough` | box → box; open from a point; camera keyed into a rect |
| `ArchWindow` | `archShape rectShape circleShape mixShape windowFromPoint anchorPoint coverLayout` | window outline morph; next scene born on prior photo's anchor |
| `PostcardDrop` | `postcardPose dropPose squash stackRest gridCells` | fall + landing squash, seeded tilt stack, spring to grid |
| `LightArc` | `arcPoint lightColor DAY_LIGHT`, prop `iris` | disc on a day arc; iris out of the disc |
| `PathCamera` / `PathTrail` | `buildPath nearestLength pathFrame` | camera along SVG path (M L H V C Q Z), deterministic arc length |
| `Key` | `KeySvg keyTurn keyTurns Keyhole KeyholeIris keyholeShape DoorSwing` | key turn with click overshoot; open from keyhole; door in perspective |
| `LightFlood` | `floodAt ringRadii` | light floods the frame, drains in rings; next scene inside the last ring |
| `Belt` | `beltPose` | places on a belt: ramp, cruise, exact brake on item k (`distance = k * spacing`); `tau` clock |
| `ObjectWipe` | `wipeBar barRect revealInset` | an object crosses the lens and uncovers the next scene |
| `Calendar` | `tearPose pageInPlace` | pages tear off on a hinge, fall and fade; last page stays |
| `FilmStrip` | `stripOffset cellRect` | a strip of frames rolls and stops on a cell; that frame grows to fill the screen |
| `Dominoes` | `tipAngle chainStarts` | cards tip with gravity; card k+1 starts when card k reaches the contact angle |
| `CauseEffect` | `approach impactPose effectProgress` | a cause accelerates into a target; squash, recoil and the effect start on the hit frame |
| `Entrances` / `Gather` | `entrancePose gatherPose` | five entrances (rise, drop with squash, slide, pop, swing) that settle exactly at rest; a cast flying into one target, one after another, and absorbed there |
| `Silk` | `silkY silkPath` | translucent ribbons for a living background; a pure function of the frame that loops exactly |
| `Caption` (component) | `splitCaption blurIn` | two-line caption: small sans, serif italic out of a blur, one boxed word; leaves before the next change [R-18] |
| `Steam` | `steamPuffs puffAt veilDensity` | rising vapour puffs; a veil that swells around each scene change so the change happens through the steam; tracked lead puff |
| `Stream` | `streamCenter streamWidthAt ribbonSides headTaper` | a meandering stream from above (pools, riffles, banks, deep channel, glints, pebbles), windowed around the camera |
| `DepthStage` | `layerScale layerOffset blurPx depthCameraAt` | one camera through supplied layers: parallax, dolly and a focus pull (blur by distance) |
| `WrittenPostcard` | `Handwriting writeSchedule inkAt writingEnd Stamp Postcard flipAngle` | letter-by-letter ink (brand `script` font), photo stamp, card flip |

## Motion rules

| Intent | Tool | Rule |
|---|---|---|
| Landing / arrival | `spring`, low damping | R-08 |
| Snap / whip | `EASE.snap` | R-08 |
| Camera / drift | `EASE.glide`, `drift()` | R-08 R-09 |
| Camera | `<Camera>`: `leadKeys(keys, n)` keys ahead of the subject; `whipKeys(from, to, landFrame)` waits then whips; `holds` = frame ranges with zero drift; `shakes` = decaying seeded shake per landing; `<Lattice>` = far dots for an empty ground; `EASE.whip` | R-09 |
| Fast travel > ~60 px/frame | `<MotionBlur travel={px}>` (optional: fewer samples on slow stretches, none under 1 px; `samplesFor`); drafts few samples, final 12; `CUTROOM_BLUR_ENGINE=canvas` only after `scripts/blur-ab.mjs` passes | R-10 |
| Determinism | `useCurrentFrame()` + `interpolate()`/`spring()`; `random(seed)` | G-08 |

## Clips

- Prepare: `python3 tools/material.py clip <video> --start S --dur S --out clients/<slug>/assets/videos/<name>.mp4` (cut, 30 fps, H.264, no audio, HDR → SDR).
- Play: `<Video src={asset("videos/<name>.mp4")} muted>` from `@remotion/media` inside `<Sequence>`; `trimBefore` (frames) + `playbackRate` props. Not `<OffthreadVideo>` / `<Html5Video>` / CSS / DOM video.
- A clip fits inside any move (window, card, iris).

## Tracking [R-15]

`<TrackRoot>` at root · `<Beats>` with `kind` · `<Track id kind>` on subject (`inFrame`), each text block, logo · `blurred` inside `<MotionBlur>`.
