<!-- validate:ignore-file -->
# FAILURE MODES
### Faults, their causes, and the fix

**How each entry is known.** Every row carries an evidence tag, because the confidence behind them differs and you should be able to tell which is which:

| Tag | Means |
|---|---|
| **OBS** | Observed directly in a generation run, with the output inspected |
| **DOC** | Described in vendor documentation or official guidance |
| **INF** | Inferred from how the system works, and consistent with reports, but not directly verified here |

Treat OBS rows as established, DOC rows as authoritative-but-versioned, and INF rows as strong hypotheses. Cause-and-effect in generative systems is rarely provable from a handful of runs — a fix that works may be correlated with the cause rather than addressing it.

If you verify or disprove an INF row, please open an issue. That is the single most useful contribution to this repository.

| Symptom | Cause | Fix | Evidence |
|---|---|---|:--:|
| A character changes sex, age or face between clips | Described in words, no `@` handle | Promote to `@` handle with a reference sheet. Threshold is *featured OR recurring* | OBS |
| A character stands in the wrong part of a location | Environment too large, no anchor | Split the environment by station and add a set anchor stating where people stand | OBS |
| Text burned into the image, e.g. "3500K" or "(Market Lane)" | Colour temperature values, hex codes or bracketed set names in the prompt | Strip unintended tokens. Use plain-word lighting and colour. Put an explicit text policy at the **top** of every prompt | OBS |
| Set layout rearranges between shots | No set anchor | Repeat the fixed-layout paragraph in every prompt using that location | OBS |
| Wardrobe resets: wet clothes dry, fresh haircut vanishes, held item disappears | Prompt relies on the generator remembering | State physical state explicitly in the cast line of every prompt | INF |
| Clips will not cut together | No incoming state described | Write the previous final frame into the prompt in full and attach the exported image | INF |
| Camera freezes when it should move | Handoff mis-classified as a cut | Re-classify as a continuation | INF |
| Camera copies framing it should have left behind | Handoff mis-classified as a continuation | Re-classify as a cut and say so explicitly | INF |
| Background crowd churns distractingly | Recurring crowd left as plain text | Create a group plate asset and state "same people, same clothes, every time" | OBS |
| A running gesture looks different each time | No signature pose in the reference sheet | Add named signature poses to the character sheet and describe the gesture identically in every beat | INF |
| Generated clip runs long or short | Length not stated as a hard rule | State the exact duration twice: in the opening line and in the closing rules | INF |
| Faces drift subtly across a long scene | Prompts too verbose, identity instruction buried | Keep prompts tight. Put `@` handles and the "use these exact faces" line high in the prompt | INF |
| A character appears who should not be in the shot | Cast list written per scene instead of per segment | Write the cast list per segment and add "No other named characters appear" | INF |
| Storyboard stills never appear | A video prompt was asked to output stills | Storyboards are separate image generations. Never request stills inside a video prompt | DOC |
| Two shots of the same room look like different rooms | Wide and close coverage generated without a shared anchor | Add the full fixed-layout anchor to both, or split the environment | OBS |
| Clip comes out silent, or with unwanted sound | No audio direction in the prompt | For generated-audio workflows, add dialogue, SFX, ambience and exclusions. Use `AUDIO: Intentional silence.` when silence is deliberate; disable the audio check for post-audio workflows | DOC |
| Sound is muddy or generic | Too many audio elements, or vague wording | One dialogue line, one primary SFX, one ambient bed. Replace "spooky sounds" with the actual sounds | DOC |
| Character drifts despite a reference image | Prompt re-describes what the reference shows, and the two disagree | Let the reference carry appearance. Describe only state, action and held objects | DOC |
| Reference drags an unwanted background into the shot | Reference image had a busy background | Regenerate references on a plain or segmented background | DOC |
| Credits exhausted early | Every generation run at top quality | Draft on the fastest tier, commit only approved shots to the highest. Budget 3-5 attempts per segment | DOC |
| Script cannot be generated at all | Written in 10-second segments | Only 4, 6 and 8 seconds exist. Rebuild the structure on a supported length | DOC |
| Output is the wrong shape | Project planned for 1:1, 4:3 or 2.39:1 | Only 16:9 and 9:16 generate natively. Choose one and crop in post if you need another | DOC |
| Vertical version feels cropped and cramped | Horizontal master cropped to vertical | Generate hero shots natively vertical, with action in the centre band | DOC |
| Extended clip drifts away from the original | Extend compounds small errors across each continuation | Prefer separate segments with explicit final frames. Reserve Extend for actions that genuinely cannot cut | INF |
| Frames-to-Video transition looks unstable | Start and end frames too far apart | Keep the two frames compositionally close; large jumps in framing or colour destabilise the interpolation | DOC |
| Edits stop working on a clip | Some edit modes cannot be applied after extending | Do inserts and removals before extending, not after | DOC |

---

## The two most expensive mistakes

**1. Trusting words over handles.** Every character you describe rather than reference is a character that will change. When in doubt, make the handle. Assets are cheap and generated once.

**2. Skipping the storyboard gate.** A few still images cost a fraction of one video generation. Most faults in this table are visible in stills.

**3. Planning around specifications that do not exist.** Confirm segment length and aspect ratio against the generator before writing a single scene. A beautiful script in an unsupported format is worth nothing.

---

*Part of the Google Flow Scripting & Prompting Skill — https://github.com/agbelemi/google-flow-scripting-skill*
