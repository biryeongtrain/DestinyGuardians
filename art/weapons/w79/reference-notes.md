# W79 visual reference handoff

Research: 2026-10-24, Asia/Seoul. Scope: ground-wave appearance for parent-owned per-lane Polymer itemdisplays. No runtime/model implementation in this handoff. Read W78 notes only for identity and historical-size context; no mechanics research repeated.

## What the inspected pixels support

**Dimensional Hypotrochoid: blue-white icy needles and angular fragments over a low blue-violet ribbon, with a soft mist plume.** A smooth curling blue ribbon captures only part of the appearance. The strongest frame is [front view, 1.50s](references/hypotrochoid-artist-stasis-wave-front-1.50s.jpg): uneven thin spikes rise from a pale cracked/webbed ground band; blue faceted chips and white streaks scatter above it. The flat ground layer reads darker indigo under the white/cool-blue highlights. The earlier [1.00s frame](references/hypotrochoid-artist-stasis-wave-front-1.00s.jpg) shows a low curved advancing lip. This is an icy, irregular surface effect with a local crest, rather than evidence for a large continuous smooth wall. Mist can extend higher than the solid-looking spikes.

**Deafening Whisper: lavender-white/lilac energy with purple fringe; coarse pixels suggest an uneven ridge or tuft, but cannot establish fine flame morphology.** The inspected [00:22 and 00:23 storyboard cells](references/whisper-storyboard-selected-contact-sheet.jpg) show bright ground-level energy and an upright bright patch. Combat effects overlap the view. Confidence is moderate for the general color and low for the detailed silhouette. The white diagonal lines in the 00:23 cell include foreground weapon fire; do not trace those as the wave. These cells do not justify a clean sheet, an exact rolling flame, or a full turbulent wall. A flame-like treatment remains an interpretation pending better Void footage.

## Specific sources and local evidence

### H1: artist-authored Stasis presentation, strongest source

[Ben Platnick, Destiny 2: Lightfall: Dimensional Hypotrochoid VFX](https://fx.s3pirion.com/projects/8bWOL6). Page date: February 12, 2023. The artist identifies himself as the creator/implementer of the weapon projectile and firing VFX. This is a primary artist portfolio showing Bungie/Destiny-watermarked in-engine presentation, not an October 2026 gameplay measurement or a Bungie news article. Both page text and actual extracted video pixels were inspected.

Downloaded only these three short media files, about 9.6 MB combined:

| Clip and source URL | Saved file | Useful presentation timestamps |
| --- | --- | --- |
| [Front/oblique wave demonstration](https://cdn.artstation.com/p/video_sources/001/239/551/stasis-wave-front.mp4) | `references/hypotrochoid-artist-stasis-wave-front.mp4` | 0.50s contact plume; 1.00s low leading lip; 1.50s spikes/cracks/shards; 2.50s fading ribbon; 3.50s sparse residual glow |
| [Third-person firing](https://cdn.artstation.com/p/video_sources/001/239/542/stasis-wave-firing-3rd.mp4) | `references/hypotrochoid-artist-stasis-wave-firing-3rd.mp4` | 1.25s impact/spike burst; 1.75s advancing icy ridge and separate mist/dust; 2.75s ground remnant |
| [First-person firing](https://cdn.artstation.com/p/video_sources/001/239/534/stasis-wave-firing-1st.mp4) | `references/hypotrochoid-artist-firing-1st.mp4` | 0.75s first ground eruption; later shots overlap, so unsuitable for single-shot lifetime |

[Front contact sheet](references/hypotrochoid-artist-stasis-wave-front-contact-sheet.jpg) and [third-person contact sheet](references/hypotrochoid-artist-stasis-wave-firing-3rd-contact-sheet.jpg) show 0.25s sampling. The first-person contact sheet also runs in chronological order. Original clips remain available for review. Nine selected full-size JPEG frames retain the watermarks. AVFoundation extracted them locally with zero requested time tolerance; timestamps are requested source-video times, not recovered simulation clocks.

In H1 front view, the strong moving structure develops around 0.50–1.50s of the clip. By 2.50s it has mostly collapsed to a dark trace, sparks, and a few fragments; around 3.50s only sparse points remain. The contact sheet approaches an empty floor toward 5s. This supports a fast visible crest followed by a longer cosmetic tail. It does not establish exact gameplay duration, damage persistence, speed, or a comparative Void/Stasis lifetime ratio. No time-warp/playback-rate audit was performed.

### V1: older Deafening Whisper gameplay, limited visual evidence

[Bodacious Steve, The Deafening Whisper Grenade Launcher is NASTY (How to get)](https://www.youtube.com/watch?v=KIwDTS6Exe8). Revisit [00:22](https://www.youtube.com/watch?v=KIwDTS6Exe8&t=22s) and [00:23](https://www.youtube.com/watch?v=KIwDTS6Exe8&t=23s). A search result indexed this as older Beyond Light-era footage; an exact upload date was not established in this pass.

The browser opened and played the actual watch page. The paused 00:59 view showed a bright impact close to the camera, not a clean ground crest, and was not used to classify the silhouette. The text web reader could not fetch the watch page. Public YouTube player HTML exposed two downloadable storyboard sheets, saved in `references/whisper-youtube-storyboard-0.jpg` and `-1.jpg`. Those are actual inspected images, not search snippets. Each cell is only 160×90, sampled about once per second. Cell timestamps derive from the supplied storyboard grid metadata, so treat them as approximate locators. Selected cells at 22s, 23s, and 30s are saved at native resolution; a 3× nearest-neighbor contact sheet makes them easier to inspect without inventing detail. The 30s cell contains combat overlap and is not a clean crest reference. No full-resolution Void video frames were saved. Exact texture, crest cross-section, and visual lifetime remain unresolved.

## Geometry and texture guidance for the parent

These are authored approximations based on the evidence, not recovered Destiny meshes or an exact match:

- Stasis: keep the floor-contact portion shallow and irregular. Use short, uneven, tapered shard/needle silhouettes and a broken pale crack network over an indigo/blue-violet base. Concentrate white/cool-blue highlights near the active ridge. Separate the airborne fragments and soft mist from the ground geometry when possible. A uniform blue flame or smooth tall sheet would omit the clearest H1 cues.
- Let each lane carry its own local crest segment and brief fading remnant. The 6/10-lane count and wall/gap stopping are parent design choices, not observations from these images. Avoid a single large cross-lane wall that visibly bridges stopped lanes. No tracker or HunterVfx pool assumption is needed.
- Void: lavender-white highlights and a violet fringe have some pixel support. An uneven low ridge is a cautious starting point. Keep a curled flame/ribbon candidate labeled approximate; the inspected low-resolution cells cannot validate a precise fold, curl direction, flame texture, or solid wall.
- Do not infer freeze, persistent damage, collision dimensions, or numerical lifetimes from the cosmetic ice and lingering glow. No evidence here supports a claim that Stasis is taller/wider/longer-lived than Void in the current sandbox.

## Evidence boundaries and file inventory

Search snippets and item stat pages only helped locate sources; none establish crest geometry. W78 identifies the selected weapons as Void Wave Frame and Stasis Compressed Wave Frame, but its text descriptions do not establish their appearance. The artist frames supply strong Stasis pixel evidence; Void remains limited by resolution and combat overlap. No Drive VFX source/archive was identified or downloaded in this pass. No generated imagery or redrawn reconstruction is presented as reference evidence.

Only `art/weapons/w79/reference-notes.md` and files under `art/weapons/w79/references/` were written. No reset, commit, runtime/test/config edit, Blockbench interaction, game client, or game build. Temporary extraction frames/cache inside the owned reference directory were removed; the originals, selected evidence, contact sheets and indexes remain. [file-inventory.json](references/file-inventory.json) lists retained files, byte lengths and SHA-256 digests; these establish local integrity, not source authenticity or runtime validation.
