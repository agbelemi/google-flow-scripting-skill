<!-- validate:ignore-file -->
# Worked example
### Hansel and Gretel — a 48-second opening, start to finish

A public-domain story known on every continent, small enough to follow end to end, and it happens to exercise every hard part of the skill: two children who must stay consistent, an environment that has to be split, a hero object, and a state anchor that changes across shots.

Substitute your own project. The shape does not change.

---

## 1. Intake (flow-orchestrator)

> **You:** Use flow-orchestrator — I want to make the opening of Hansel and Gretel in Flow.

| Question | Answer |
|---|---|
| What are you making? | A narrative short, the opening of a fairy tale |
| Visual format? | 3D animation |
| Segment length? | 8 seconds |
| Aspect ratio? | 16:9 |
| Runtime? | 48 seconds for this opening |
| Dialogue? | One line, near the end |
| Credit budget? | Modest — draft on the fast tier |
| Setting and cultural detail? | A generic northern European forest, no specific nation |

It computes and confirms:

> 8-second segments, 48 seconds, 16:9. Six segments. Storyboarding at three panels each is 18 stills, plus 6 video segments. At three to five attempts each, budget 18 to 30 video generations. Confirm before I build.

Then routes to `flow-3d-animation`.

---

## 2. Structure (flow-story-architect)

```
SCENE 1 — 48s, 6 segments
Locations: ForestPath, ForestClearing, GingerbreadHouse
Cast: Hansel, Gretel
Hook (first 2s): a small hand opens, and breadcrumbs fall onto dark earth
Beats: the trail is laid; the children walk deeper; they turn back and the
       trail is gone; they are lost; light appears through the trees; the
       house is revealed
Out-point: the house, impossible and inviting, filling the frame
State anchor: the breadcrumbs. Present in 1-2, gone in 3, and their
       absence is the whole turn of the scene
```

---

## 3. References (flow-asset-manager)

The appearance table decides what gets locked:

| Who or what | Segments | Featured? | Locked reference |
|---|---|---|---|
| Hansel | 1,2,3,4,5,6 | Yes | `Hansel` |
| Gretel | 2,3,4,5,6 | Yes | `Gretel` |
| Forest path | 1,2,3 | — | `ForestPath` |
| Forest clearing | 4,5 | — | `ForestClearing` |
| Gingerbread house | 6 | Yes — the hero object | `GingerbreadHouse` |

**Why the forest is split.** A path between close-crowded trunks and an open clearing with sky above share no anchor objects. One `Forest` reference would drift badly between them. Two references, two anchors.

**The three-reference limit bites in segment 6:** Hansel, Gretel and GingerbreadHouse is exactly three. There is no room for a fourth lock, so the scene was written not to need one.

Set anchor for the path:

> Location: ForestPath. A narrow track of dark earth winding between tall close-set pine trunks. Fixed elements: trunks crowding both sides within two metres of the path, a dense canopy overhead letting through only scattered shafts of light, roots crossing the track, deep leaf litter either side. No clearing, no sky visible.

---

## 4. Segment script (flow-3d-animation)

```
SEG 3 (0:16-0:24) — the trail is gone
LOCATION: ForestPath
REFERENCES TO ATTACH: Hansel, Gretel, ForestPath
CAMERA: MS on both children from behind, 50mm, then a slow 30cm push past
  them down the empty path.
BEATS:
  0-1s: Hansel stops walking; his shoulders lift
  1-2s: he turns his head to look back down the path
  2-3s: Gretel turns too, following his eyes
  3-4s: the push-in begins past them, down the track
  4-5s: the path behind is bare dark earth, no breadcrumbs anywhere
  5-6s: a single bird hops across the empty track and away
  6-7s: Gretel's hand finds Hansel's sleeve and closes on it
  7-8s: neither child moves; hold on the empty path beyond them
AUDIO:
  Dialogue: Gretel says, "They're gone." - small, flat, not yet frightened.
  SFX: a single wingbeat as the bird lifts away.
  Ambient: wind high in the canopy, nothing at ground level.
  Not heard: no music, no other birds.
FINAL FRAME: The two children small in the lower frame with their backs to
  camera, hands joined, facing away down a bare dark forest path that runs
  empty into shadow. No breadcrumbs anywhere on the ground.
HANDOFF FROM SEG 2: CUT — new camera setup.
```

Note what the cast line does **not** do: it does not re-describe the children's faces or clothes. Those are in the references. Describing them again would give the model two competing sources.

---

## 5. Storyboard (flow-storyboard-director)

An 8-second segment gets three panels: 0s, 4s, final. Panel C is the required final frame, worded identically to the script — that exact match is what lets it seed segment 4, or serve as an end frame if you supply one.

Check before generating video: both faces match their references, the path anchor holds, the breadcrumbs are genuinely absent, no text anywhere.

---

## 6. Audit

```bash
python scripts/validate.py hansel.md --segment-length 8
```

Mechanical checks first. Then `flow-continuity-auditor` reads for the judgement checks — and here it catches the one that matters most in this scene: **the breadcrumbs must be present in segments 1 and 2, and absent from segment 3 onward.** A stray crumb in segment 4 destroys the story.

---

## 7. Generate

1. All five references, on plain backgrounds, named exactly
2. 18 storyboard stills — check, reject, regenerate as needed
3. 6 videos on the fast tier, saving each final frame as an asset
4. Re-run approved shots on the quality tier
5. Assemble in Scenebuilder, then edit and finish

---

## What to notice

- **The environment split was decided by camera coverage**, not by geography. Same forest, two references.
- **The three-reference limit shaped the writing.** Segment 6 was designed around it rather than discovering it late.
- **The final frame is written once** and reused word for word in the storyboard panel and the next segment's opening state.
- **Audio was specified even for a near-silent shot** — including what should *not* be heard, which is what keeps invented music out.
- **The state anchor drove the audit.** Breadcrumbs present, then absent, is the scene's entire meaning, and it is exactly the kind of thing an independent generation cannot infer unless the state is carried explicitly.
