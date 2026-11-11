# Move library

Every move in `remotion-base/src/moves/` (and the camera and caption components) has one Studio demo, one
final-quality clip and one sheet here: a contact strip over a speed graph measured from the pixels (optical
flow), with the 80 px/frame blur limit marked. The demos use the fictional sample client only.

Open a demo in Studio (`cd remotion-base && npx remotion studio`, folder `moves`), or render it:

```bash
cd remotion-base && node scripts/render.mjs MovesDemo-Squash --final --out out/moves
```

```bash
python3 tools/move_sheet.py remotion-base/out/moves/MovesDemo-Squash.mp4 --out docs/moves/Squash.png
```

| Move | Demo | What it shows | Families | Sheet |
|---|---|---|---|---|
| **Entrances** | | | | |
| `SplitText` | `MovesDemo-SplitText` | a line arrives word by word, a name letter by letter | typographic_system | [SplitText](SplitText.png) |
| `MaskReveal` | `MovesDemo-MaskReveal` | lines rise from behind their masks, then a photo is uncovered | typographic_system, logbook, before_after_rest, letters_as_windows | [MaskReveal](MaskReveal.png) |
| `Typewriter` | `MovesDemo-Typewriter` | a message typed on a card with a caret | typographic_system | [Typewriter](Typewriter.png) |
| `Caption` | `MovesDemo-Caption` | small sans line, serif italic out of a blur, one boxed word; gone before the change | any | [Caption](Caption.png) |
| `WrittenPostcard` | `MovesDemo-WrittenPostcard` | handwriting, a stamp that lands, the card flips | written_postcard, logbook | [WrittenPostcard](WrittenPostcard.png) |
| `PostcardDrop` | `MovesDemo-PostcardDrop` | cards fall, squash, stack, resolve into a grid | postcards, scrapbook | [PostcardDrop](PostcardDrop.png) |
| `Bouncer` + squash/stretch | `MovesDemo-Squash` | a ball stretches in flight and squashes on each contact; three entrances stretch along their travel | any (`entrancePose`) | [Squash](Squash.png) |
| **Carries** | | | | |
| `Gather` | `MovesDemo-Gather` | five entrances, then the cast flies into one target | gather | [Gather](Gather.png) |
| `Morph` | `MovesDemo-Morph` | a pressed button becomes the card it opens | transforming_object, physical_metaphor, small_details, match_cut, living_map | [Morph](Morph.png) |
| `IrisOpen` | `MovesDemo-IrisOpen` | the next place opens out of a point of the photo before | day_arc, living_map | [IrisOpen](IrisOpen.png) |
| `ArchWindow` | `MovesDemo-ArchWindow` | one window: arch, rectangle, circle | window | [ArchWindow](ArchWindow.png) |
| `Belt` | `MovesDemo-Belt` | places on a belt that starts, cruises and brakes on one | continuous_surface | [Belt](Belt.png) |
| `ObjectWipe` | `MovesDemo-ObjectWipe` | an object crosses the lens and uncovers the next place | object_wipe | [ObjectWipe](ObjectWipe.png) |
| `LightFlood` | `MovesDemo-LightFlood` | light floods the frame and drains in rings onto the next place | light_flood | [LightFlood](LightFlood.png) |
| `FilmStrip` | `MovesDemo-FilmStrip` | a strip rolls, one frame grows to fill the screen | film_strip | [FilmStrip](FilmStrip.png) |
| `Calendar` | `MovesDemo-Calendar` | pages tear off and leave a place each | calendar | [Calendar](Calendar.png) |
| `Key` | `MovesDemo-Key` | a key turns; the next place opens out of the keyhole | key | [Key](Key.png) |
| `Steam` | `MovesDemo-Steam` | a change of place through a veil of steam | — | [Steam](Steam.png) |
| **Contact** | | | | |
| `CauseEffect` | `MovesDemo-CauseEffect` | a ball hits a card: squash and a ring on the hit frame | cause_effect | [CauseEffect](CauseEffect.png) |
| `Dominoes` | `MovesDemo-Dominoes` | cards tip over one after another, each on contact | chain_reaction | [Dominoes](Dominoes.png) |
| **Camera** | | | | |
| `Camera` | `MovesDemo-Camera` | drift that stops in the holds, a whip to each photo, a shake on landing | any | [Camera](Camera.png) |
| `pushThrough` | `MovesDemo-PushThrough` | the camera pushes into one card of a wall until it is the frame | scale_camera, entering, dive_through_scale, letters_as_windows | [PushThrough](PushThrough.png) |
| `DepthStage` | `MovesDemo-Depth` | one camera through layers: parallax and a focus pull | depth | [Depth](Depth.png) |
| `PathCamera` | `MovesDemo-PathCamera` | the camera walks a drawn trail across placed photos | trail, entering | [PathCamera](PathCamera.png) |
| **Grounds** | | | | |
| `LightArc` | `MovesDemo-LightArc` | a disc of light crosses the day; an iris opens at dusk | light_clock, day_arc, coffee_to_evening | [LightArc](LightArc.png) |
| `Silk` | `MovesDemo-Silk` | translucent ribbons that loop exactly | any | [Silk](Silk.png) |
| `StreamRibbon` | `MovesDemo-Stream` | a stream drawing its course down the frame | trail, thread | [Stream](Stream.png) |
