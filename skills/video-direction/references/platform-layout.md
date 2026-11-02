# Platform layout [R-05 R-11 R-12]

Authoritative numbers: `tools/quality/platforms/specs/<platform>.json` (`reviewed` date; stale > 180 days ⇒ re-check `sources`). Values below at 1080×1920 / 1080×1350; `ui` = px covered by app UI [top, bottom, left, right] (text inside = FAIL). Studio reads the same specs via `FORMATS.<id>.safe`.

| Platform · format | Size | Duration (s) | ui [t, b, l, r] | min text px | End hold | Hook / loop |
|---|---|---|---|---|---|---|
| instagram · reel | 1080×1920 | 3–900 (rec 5–90) | 250, 400, 64, 140 | 36 | WARN | yes / yes |
| instagram · story | 1080×1920 | 3–60 (rec 5–15) | 250, 320, 64, 64 | 36 | FAIL | — |
| instagram · feed_video | 1080×1350 | 3–900 (rec 5–60) | 60, 60, 64, 64 | 28 | WARN | — |
| tiktok · video | 1080×1920 | 3–600 | 240, 480, 120, 120 | 36 | WARN | yes / yes |
| tiktok · ad | 1080×1920 | 3–600 | 240, 480, 120, 120 | 36 | FAIL | yes / no |
| youtube_shorts · short | 1080×1920 | 1–180 | 240, 480, 48, 192 | 36 | WARN | yes / yes |

Images (Instagram): JPEG, ≤ 8 MB, 320–1440 px wide, ratio 4:5–1.91:1, sRGB. Feed posts and reel covers also get the 3:4 profile-grid crop check.

## Type sizes at 1080 wide [R-12]

| Element | Min px |
|---|---|
| Headline | 84 |
| Supporting text | 44 |
| Phone number / CTA | 72 |
