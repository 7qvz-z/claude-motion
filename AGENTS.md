# Agent guide

This repo is a motion design pipeline for coding agents, built on [Remotion](https://remotion.dev) (React → video). It ships one finished piece, `EffortVideo` (22 s, 1080×1080, 60 fps), as the reference implementation.

## Read first

The skills in `.claude/skills/` are the core of this repo. Claude Code and Cursor load them automatically; other agents should read them before touching a video.

- `motion-design/SKILL.md` — taste rules with numbers: easing, springs, timing, type, color, texture, transitions.
- `review-loop/SKILL.md` — how to look at your own renders and what to check. Mandatory before saying a video is done.
- `sound-design/SKILL.md` — timeline-synced procedural audio and mastering.

## Commands

| Command | What it does |
|---|---|
| `npm run studio` | live preview in the browser |
| `npm run draft` | fast half-res render → `out/draft.mp4` |
| `npm run sheet` | contact sheets at every timeline beat → `out/sheets/` |
| `npm run sfx` | regenerate audio from `timeline.json` → `public/sfx.wav` |
| `npm run wave` | waveform with beat markers + loudness check |
| `npm run build` | sfx + full render + mux → `out/effort.mp4` |
| `npm run gif` | README preview → `media/preview.gif` |
| `npm run cover` | 5:2 article cover (`ArticleCover` still) → `out/article-cover.png` |
| `npm run typecheck` | TypeScript check |

Requirements: Node 20+, Python 3, ffmpeg. If `/usr/bin/chromium` (or `$REMOTION_BROWSER`) exists it's used; otherwise Remotion downloads its own browser on first render.

## Layout

```
timeline.json            every beat, in seconds — single source of truth for picture and sound
src/lib.ts               palette (C), fonts (F), easings, prog/band/sp helpers, TL
src/Root.tsx             composition registration
src/EffortVideo.tsx      the piece: scene orchestration
src/ArticleCover.tsx     2000×800 still built from the same timeline and easing
src/scenes/              one file per scene
src/components/          reusable pieces (PromptBar, EffortSlider, primitives: Mask, Roll, Grain…)
scripts/sfx.py           procedural sound design
scripts/sheet.mjs        contact sheets for review
scripts/wave.mjs         waveform + loudness
examples/                gallery: prompt, process and result for each piece
```

## Making a new video

1. Agree on the message and a storyboard with the user first (what's on screen, in what order, what the one hero moment is).
2. Write the beats into a timeline JSON before any component code.
3. Add a `<Composition>` in `src/Root.tsx`, build scenes, reuse `src/components/` and `src/lib.ts`.
4. Loop with `review-loop` until a full pass is clean, then do sound with `sound-design`.
5. Add the piece to `examples/` with the prompt you were given.

## Conventions

- Animation is a pure function of `useCurrentFrame()`. No CSS animations, `Math.random()` or `Date`.
- No hardcoded start times in components; read them from the timeline.
- Colors only from `C`, fonts only from `F`.
- Match the existing code style: small helpers, inline styles, comments only for non-obvious constraints.
