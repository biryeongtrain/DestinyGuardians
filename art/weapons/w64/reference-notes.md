# W64 first-person hand-cannon references

**Ready: Duke Mk. 44 only**, for a reference-informed attached-cylinder-housing open → raise → load → close → return motion. Actual decoded gameplay frames were inspected directly. Inner load-unit details, exact pivots/angles, and Outlaw acceleration are not certified. Austringer is an inspected secondary reference and is outside the selected W64 implementation scope.

- [Duke selected gameplay frames](references/duke-selected-contact.jpg)
- [Austringer secondary selected frames](references/austringer-selected-contact.jpg)
- [Machine-readable observations](references/observations.json)
- [Video/model identity, frame timestamps and SHA-256 manifest](references/provenance.json)

## Exact source identity and reuse

| Target | Bungie item hash | Video actually inspected | Identity limits |
|---|---:|---|---|
| Duke Mk. 44 | `2112909414` | [Deleted Duke - Outlaw + Rampage, Keeping Duke - Rangefinder + Kill Clip](https://www.youtube.com/watch?v=-oS68Bu_sDs&t=25), Rin, uploaded 2018-11-12, selected source1280×720 at30fps | Inventory at48.000 explicitly says DUKE MK.44. Video pixels do not expose a Bungie hash; hash joins through existing W30/W46 evidence. Historical inventory says110RPM; this does not revise current repository120RPM data. |
| Austringer | `3055790362` | [Destiny 2 - All Menagerie Weapons - Animations & Sounds w/ Slow-Motion](https://www.youtube.com/watch?v=UnnN9RchNKQ&t=16), Ultraclocked, uploaded2021-01-08, selected source1280×720 at60fps | Austringer chapter0:00–0:38 and named inventory seen in private survey. Historical Menagerie appearance, not a different reissue hash or current-sandbox certification. |

Existing references inspected first: W30 manifest/catalog; W31 visual-source identities; W46 official-item/reload evidence; W47 gameplay references; W62/W63 timing/audio scope. W47 provides a **Beloved-only** observed reload, not hand-cannon evidence. Existing W62/W63 timings are server-authored/approximate and not a frame measurement of these clips.

The [user model folder](https://drive.google.com/drive/folders/14Ry-piQtH3j6MlfoVLfFfu98c4pcTJUb) resolves through existing W30 source identities:

- Duke: [archive source](https://drive.google.com/file/d/1Glp8xj7h7_zWY4xphG0pnZcLPla69_ax/view), catalog name `Duke Mk. 44 (ripped by Jloughlen).rar`; `DukeMk44.blend` / `DukeMk44.fbx`.
- Austringer: [archive source](https://drive.google.com/file/d/1oPpAAS_YIce29AOoRg77TdpZvaGWDKlp/view), catalog name `Austringer.7z`; `Austringer/Austringer.blend` / `.fbx`.

All four existing private cached model files were rehashed successfully against `art/weapons/w30/manifest.json`. No model redownload was needed. Source paths and full SHA-256 values are in provenance. Static model identity alone does not establish the reload mechanism or confirm that an animation exists in those files.

## Duke: direct observations to implement

All directions below are **player screen directions in unmirrored first-person footage**, not local model axes. The right hand retains the grip. The large cylindrical housing opens to the **left of the receiver on screen**, stays alongside the weapon, and exposes a receiver gap. The gun is raised nearly muzzle-up, then lowers/rolls while the left hand approaches the open cylinder area. The hands continue working after the ammunition HUD transfer, followed by closure and return forward.

This supports an attached swing-out cylinder housing. It does **not** establish full-cylinder removal/replacement or individual-cartridge loading. The dark/moving Duke footage does not resolve the possible inner load unit well enough to prescribe its geometry or ejection path. Do not import that detail from Austringer as an observed Duke fact.

| Absolute Duke source time | Directly visible evidence |
|---|---|
|25.400–25.600|Previous shot/recoil transitions into raised/rolled reload preparation; exact reload onset not measured.|
|25.900–26.100|Housing offset to screen left, with circular end visible.|
|26.300–26.700|Gun nearly muzzle-up; housing remains at screen left of receiver with open gap.|
|26.800–27.100|Gun lowers/rolls; left hand approaches loading area.|
|27.100|HUD still **7 / reserve107**.|
|27.200|HUD now **9 / reserve105**; weapon still low/in hands.|
|27.200–27.500|Hands remain at receiver after ammo is credited.|
|27.600–27.900|Closure/recovery; still visibly tilted at27.700, returning forward at27.900.|
|28.000–28.100|Subsequent shot is demonstrated; ammo becomes8. This does not establish the earliest allowed shot input.|

The HUD transfer is bracketed to **(27.100,27.200] seconds**, not claimed as a single exact engine event. Selected full frames: [open housing](references/duke-open-housing-26.500.jpg), [before ammo](references/duke-pre-ammo-27.100.jpg), [after ammo](references/duke-post-ammo-27.200.jpg). Preserve a distinct visual recovery tail after the ammo event; do not collapse ammo credit, housing closure, ready pose and firing eligibility into one endpoint based on this sample.

This is a **partial reload7→9**. The title mentions Outlaw, but selected gameplay shows **Kill Clip** and no active Outlaw HUD. Treat it as a no-Outlaw-observed sample, not a controlled base-stat benchmark. **No normal-versus-Outlaw frame comparison was verified.** Empty reload and current-sandbox durations were not established.

## Austringer: secondary mechanism audit

The regular-speed sequence is visible around16.5–19.65seconds. Its edited replay around20.0–25.95seconds visibly says **0.5x**; that is a playback label, not a perk or Outlaw evidence. These source-video times must not be used directly as real-time game durations.

The outer black cylindrical housing swings left and remains attached beside the receiver. At21.800 it is held muzzle-up. At**22.150** a separate inner cylindrical object with a brass/gold top is visibly below the retained outer housing; at22.500 the housing remains. At23.050 the housing end looks open, and at23.300 the left hand presents a brass-faced round unit at the loading area. This is consistent with exchanging an **inner ammunition unit inside an attached outer housing**; it is not evidence that the whole attached outer cylinder is thrown away. [Selected22.150 full frame](references/austringer-inner-drum-22.150.jpg).

The exact mechanical term, cartridge count and individual-cartridge insertion are not established. Showcase HUD is suppressed, so no Austringer ammo-credit event is assigned. These finer inner-unit observations are not a basis to assert the same inner mechanism for Duke.

## Implementation boundary and authored values

Main reported selecting Duke only, preserving232source cubes (211body+21cylinder) and adding2yoke links for234total. Reported pivot`[8,10.2,5.17]`, Z80° opening and approximately62/65° body tilt are **authored implementation choices**, not angles/pivots extracted from the footage. This reference task did not verify geometric partitioning, edit the generator/runtime or inspect the imported native project.

Keep the observed on-screen left opening when mapping to the model coordinate system. Numeric transforms, hand IK, per-tick interpolation, yoke geometry, exact normalized phase boundaries, and mapping to existing59/33tick server timings belong to main's implementation/validation. Neither source proves those values.

## Provenance, caches and audit scope

`references/provenance.json` pins source video/metadata SHA-256, original title/uploader/date, nominal fps and download format, inspected windows, selected frame times/nominal frame indices, per-image SHA-256, existing W30 inputs and model-cache verification. `references/observations.json` distinguishes observation, interpretation and unresolved details. Frame times identify actual selected decoded frames; they are not an original engine trace.

Private review copies remain outside the repo:

- Duke clip:`/tmp/destiny-w64-reference/-oS68Bu_sDs.mp4` (inspect25.4–28.4seconds).
- Austringer clip:`/tmp/destiny-w64-reference/UnnN9RchNKQ-austringer.mp4` (source0–38second section; timestamps remain source-relative).
- Detailed private crops:`/tmp/destiny-w64-reference/duke-cylinder.jpg` and `austringer-cylinder.jpg`.
- Private HUD survey:`/tmp/destiny-w64-reference/duke-timing.jpg`.

Only short selected stills/contact sheets and original research notes are stored here. No full video, full metadata/search dump, or copyrighted article export is included. No Gradle, native app/computer-use, Blender or Blockbench action was performed by this reference task. No runtime, animation-rip, exact hand-motion or current-game timing fidelity claim is made.
