<!-- validate:ignore-file -->
# ADAPTING TO OTHER GENERATORS
### What transfers, and what does not

*Landscape as of July 2026. This space moves fast  -  verify before committing a project.*

This skill is written for Google Flow. Most of it is generator-agnostic craft.

## Transfers unchanged

- The self-containment principle, and everything that follows from it
- Set anchors and environment splitting
- One beat per second, with numbers
- The final frame as generation target, QA check and next-prompt opening state
- Cut versus continuation classification
- Storyboard-first workflow
- The no-text instruction and avoiding label-shaped tokens
- The featured-or-recurring threshold for who needs a locked reference
- Positive description over negative commands
- Most of `FAILURE-MODES.md`

## Needs translation

**Reference binding.** Flow's Ingredients system is what this skill leans on hardest. Equivalents:

| Generator | Consistency mechanism | Notes |
|---|---|---|
| **Runway Gen-4.5** | Reference images, plus motion brush and camera controls | The strongest control surface for repeatable client work |
| **Kling 3.0** | Elements, plus a multi-shot mode that holds a character across several cuts in one generation | Strong on human motion; see below |
| **Luma Ray** | Keyframes and video-to-video | Best when you are starting from existing footage or controlled concept frames |
| **Seedance / Wan** | Reference images; Wan is open source | Wan is the option when you need to self-host |
| **Sora** |  -  | **Being discontinued.** The web and app experiences ended in April 2026 and the API is set to follow. Do not build new work on it; migrate existing pipelines |

Where there is no reference binding at all, compensate by making the physical description in each prompt longer and more precise, and by chaining start frames aggressively. Some teams generate more takes than needed and select for consistency.

**Multi-shot generation changes the calculus.** Kling 3.0 can define a series of shots in a single generation and hold character and lighting across the cuts automatically. Where that works for your project, it replaces some of the per-segment chaining discipline in this skill. The scripting craft  -  beats, final frames, set anchors  -  still applies; the continuity plumbing is partly handled for you.

**Audio.** Native audio is not universal. Some platforms generate it, some offer lip-sync and voice as separate tools, some have none. Check before writing audio direction into every prompt, and be ready to move the sound plan to post.

**Segment length.** Ranges vary widely, and some generators produce far longer single clips than Flow. Ask the user, set it to whatever the target produces cleanly, and keep the beat-per-second rule.

**Aspect ratio.** Support differs. Confirm before writing, since it changes composition and where you place critical action.

## Worth re-testing per generator

- How much verbosity helps before it starts to hurt
- Whether references or text descriptions win when they conflict
- Whether continuation handoffs hold, or whether every handoff must be treated as a cut
- Maximum reliable number of characters in one frame
- Whether audio arrives at all, and whether dialogue syncs

Run these on a throwaway scene before committing a full project.

## A note on choosing

No generator dominates. Prompt adherence, motion realism, character consistency, editing control and cost all rank differently, and the leader changes every few months. Pick for the specific job, keep a second option warm, and do not architect a pipeline that only one vendor can run.

---

*Part of the Google Flow Scripting & Prompting Skill  -  https://github.com/agbelemi/google-flow-scripting-skill*
