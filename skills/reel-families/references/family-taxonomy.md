# Family taxonomy [F-01 F-02 F-03 F-04 C-02]

Data: `families.json` (31 families; this table mirrors it — the JSON wins). Creative description of each family: `skills/video-direction/references/concept-families.md`.

| Axis | Values |
|---|---|
| `carry_kind` | object · camera · shape · light · text · surface |
| `boundary` | morph · iris · window · mask · wipe · flip · fall · camera · contact · match · none |
| `status` | `ready` (moves exist) · `needs-move` (propose only, F-02) |

Pick by material: photos → `kind: photo`; no photos → `generic`; clips → any `ready` family whose boundary can hold a `<Video>` (window, iris, mask, morph).

| id | kind | carry_kind | boundary | carry | moves | status |
|---|---|---|---|---|---|---|
| transforming_object | generic | object | morph | the object | Morph | ready |
| scale_camera | generic | camera | camera | the camera | pushThrough | ready |
| cause_effect | generic | object | contact | the cause | CauseEffect | ready |
| physical_metaphor | generic | object | morph | the prop | Morph | ready |
| typographic_system | generic | text | mask | the words | SplitText, Typewriter, MaskReveal | ready |
| window | photo | shape | window | window outline + opening point | ArchWindow | ready |
| postcards | photo | surface | fall | the pile | PostcardDrop | ready |
| day_arc | photo | light | iris | disc of light | LightArc, IrisOpen | ready |
| trail | photo | camera | camera | camera + trail | PathCamera, PathTrail | ready |
| living_map | photo | surface | iris | map + pins | Morph, IrisOpen | ready |
| coffee_to_evening | photo | light | morph | time of day | LightArc, Postcard | ready |
| entering | photo | camera | camera | the single camera move | pushThrough, PathCamera | ready |
| small_details | photo | surface | morph | the grid | Morph | ready |
| logbook | photo | surface | mask | page + ink line | Handwriting, MaskReveal | ready |
| key | photo | object | iris | key + rotation | KeySvg, KeyholeIris, DoorSwing | ready |
| written_postcard | photo | surface | flip | the card | Handwriting, Postcard, Stamp | ready |
| light_clock | photo | light | none | the frame | LightArc | ready |
| before_after_rest | photo | shape | mask | the seam | MaskReveal | ready |
| match_cut | photo | shape | match | matched shape + position | Morph | ready |
| object_wipe | photo | object | wipe | wiping object + direction | ObjectWipe | ready |
| film_strip | photo | surface | morph | the strip | FilmStrip | ready |
| scrapbook | photo | surface | fall | the page | PostcardDrop | ready |
| chain_reaction | photo | object | contact | the cause, always visible | Dominoes | ready |
| dive_through_scale | photo | camera | camera | anchor point | pushThrough | ready |
| calendar | photo | surface | wipe | calendar block | Calendar | ready |
| gather | photo | object | morph | the cast | Gather | ready |
| letters_as_windows | photo | text | window | letterforms | pushThrough, MaskReveal | ready |
| thread | photo | object | wipe | the thread | PathTrail | ready |
| depth | photo | camera | camera | camera + nearest plane | DepthStage | ready |
| light_flood | photo | light | iris | the field of light | LightFlood | ready |
| continuous_surface | photo | surface | camera | the belt | Belt | ready |

Set rule (F-04): 3 concepts ⇒ ≥ 2 distinct `carry_kind`, ≥ 2 distinct `boundary`, 3 distinct ids.
