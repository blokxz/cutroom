# Add-ons for the studio

Tools and skills that improve each step of a reel. Surveyed in October 2026; before any of them joins the catalog it gets pinned to a commit and tested with the sample brief.

## By reel stage

| Stage | What it improves | Add-on | Cost |
|---|---|---|---|
| Script | understand a reference or competitor video | claude-vision (Gemini) | free Gemini API |
| Footage | cut silences and dead time | auto-editor | free |
| Footage | free-license stock B-roll | Pexels MCP | free (API key) |
| Motion | React-based animation | Remotion Agent Skills | free for individuals |
| Motion | HTML + GSAP animation, ready-made flows | HyperFrames | free (Apache 2.0) |
| Motion | rhythm and transitions that don't feel like a slideshow | onetake, trama-reel-motion | own |
| Audio | voice, cloning, SFX, music | ElevenLabs MCP | 10k free credits/month |
| Captions | exact word-level timing (karaoke) | WhisperX | free; best with a GPU |
| Editing | direct ffmpeg | `video-edit` (heygen-com/skills) | free |
| Editing | finish by hand in a pro editor | auto-editor (XML export) or DaVinci Resolve MCP | free / Resolve Studio |
| QA | see the render and catch visual problems | frames via ffmpeg reviewed as images; claude-vision for the full video | free |

## Details

### HyperFrames — heygen-com/hyperframes
Open-source engine (Apache 2.0) that turns an HTML page into an MP4, frame by frame. Built for agents: HTML and GSAP are all over model training data, so the agent writes them fluently. The repo ships about 24 skills, including faceless explainer, talking-head recut, music-to-video and website-to-video flows. Requires Node 22+ and FFmpeg. Downsides: slower to render than Remotion in the cloud, and deterministic rendering is only reliable on Linux.

```bash
npx -y skills add heygen-com/hyperframes --skill hyperframes-read-first --agent claude-code
```

Fits well with `onetake`, which uses the same idea of an HTML composition where everything is a function of time.

### auto-editor — WyattBlue/auto-editor
CLI that cuts silences and motionless parts, with adjustable margins. Exports projects for Premiere, DaVinci Resolve, Final Cut, Shotcut and Kdenlive, so it also works for handing off a base cut to finish by hand. Public domain.

```bash
pip install auto-editor
```

### WhisperX — m-bain/whisperX
Whisper with exact word-level timestamps and speaker detection. The foundation for karaoke-style reel captions. BSD-2 license. Runs well on a GPU with under 8 GB; works on CPU, but slowly.

### ElevenLabs MCP (official)
About 24 tools: text-to-speech, speech-to-speech, voice isolation, cloning, sound effects, music composition and video-to-music. The server is MIT and free; you pay for API usage, with 10,000 free credits per month.

```bash
uvx elevenlabs-mcp   # with ELEVENLABS_API_KEY set
```

### Pexels MCP
Searches Pexels stock photos and videos for B-roll, under a free-use license. There are several implementations; pick a maintained one and pin it.

### claude-vision — mikefutia/claude-vision
Skill that uploads the video to Gemini (which understands video natively) and returns a report with scenes, transcript and key moments. Useful for analyzing references before writing the script, or for deeper QA of the render. Needs a free Google AI Studio API key.

### DaVinci Resolve MCP
Controls Resolve from Claude: timelines, tracks, markers, color and rendering. Useful for leaving the project assembled to finish by hand. Targets Resolve Studio (paid) and Python 3.10+.

### claude-code-video-toolkit — digitalsamba (MIT)
Not used as a whole (it's a workspace with Python and cloud GPUs), but its `ffmpeg` and `moviepy` skills are proven recipes to reuse with credit, and its `concept-explainer-short` template covers 100% AI-generated shorts.

## Sources

- HyperFrames: https://yuv.ai/blog/heygen-hyperframes-html-video · https://claudemarketplaces.com/skills/heygen-com/hyperframes/hyperframes-read-first
- auto-editor: https://pypi.org/project/auto-editor/
- WhisperX: https://www.forasoft.com/learn/ai-for-video-engineering/articles-ai/whisperx-diarization-word-level-timestamps
- ElevenLabs MCP: https://mcp.directory/blog/elevenlabs-mcp-complete-guide-2026
- Pexels MCP: https://github.com/developer-ishan/mcp-pexels
- claude-vision: https://github.com/mikefutia/claude-vision
- DaVinci Resolve MCP: https://playbooks.com/mcp/tooflex-davinci-resolve
- claude-code-video-toolkit: https://github.com/digitalsamba/claude-code-video-toolkit
