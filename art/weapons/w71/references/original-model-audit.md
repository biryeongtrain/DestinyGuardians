# W71 Long Arm original-model audit

The original has a verified mechanical rig and separable source lever, but **no stored reload animation**. W30 has 256 static volume cubes and has merged lever/body boundaries. Preserve all geometry and texture and use main-authored initial/loop/return body poses. Do not treat the whole receiver or an incomplete lever subset as a complete moving part.

## Scope and integrity

- Repository: `/Users/qf/IdeaProjects/DestinyGuardians`; observed branch `feat/hunter`.
- Exact extracted folder: `/tmp/destiny-weapons-w30/raw/long_arm/extracted/Long Arm`.
- **31/31 SHA-256 and byte-length pins match before/after**, including all **23 files** in the raw Long Arm tree and archive. Raw inventory unchanged. Full pins are in JSON.
- Only the two requested reports were written in the repository. No original geometry/texture changes, Gradle, network, git commit, app UI automation, game launch, new ammo cubes or removed detail.
- Background Blender 5.4.0 Alpha factory processes read the saved original with UI/scripts disabled and never save. An initial library-append read crashed; direct background reads succeeded. Existing Blockbench PID 48104 and Blender PID 58116 were observed alive afterward, never controlled or killed.
- Content preservation uses exact hashes and sizes. Initial nanosecond mtimes lost precision crossing JavaScript numeric serialization; mtime equality is not claimed. Final mtimes are recorded as exact decimal strings.

| Input | SHA-256 |
|---|---|
| Original Blend | `3920d8e67325002a1aaf8f03d5947440ff0fdbf243f20ae063ce09c8b5e976e3` |
| Original FBX | `bd41192a0ab6b0606403a501d8fabe7623ac68c0bf44284a8110e8189a928ebe` |
| Original archive | `85ae349b74bb916c19dd30bf16cac6d00e3a0cdc8b9c8bf1949d698c622a1f49` |
| W30 bbmodel | `f0af312b159d8a8a5558dcec7049789cdfea59cad25257c74657524cb01d091f` |
| Runtime geometry | `d166bc28532cf9461c5cb2e568f532bbceba1d3d0d0d7e43afc82408f9390ed0` |
| Original W30 texture | `451805809af885130bcda938e7e86035d0a1d0b188590699f511107bbd090a0e` |

## Geometry identities

Saved Blend: three meshes and one armature, totaling **21,082 vertices / 41,865 edges / 21,812 polygons and triangles**, matching W30 source-triangle provenance. All meshes are parented to Armature; each has an operative armature modifier and an older armature modifier with no target.

| Saved Blend object | Material | Vertices | Triangles |
|---|---|---:|---:|
| `1FD6FB80_Group4_Index16_4__lod_category_0` | `Sight` | 2,421 | 2,496 |
| `40DAFB80_Group0_Index0_0__lod_category_0` | `Bullet` | 334 | 476 |
| `A6D6FB80_Group2_Index8_2__lod_category_0` | `Frame` | 18,327 | 18,840 |

**Magazine:** no separate magazine-named mesh or bone. Integral tube/storage surfaces inside Frame remain semantically unresolved; detachable-magazine movement is unsupported.

**Shell/ammo:** the exact Bullet mesh/material/group is `40DAFB80_Group0_Index0_0__lod_category_0`. It has two near-translation-equivalent units of 167 vertices each. Unit A uses indices 0–142 and 286–309; unit B uses 143–285 and 310–333. The pair differs by a common translation within about 0.0000032 source units. Both are weighted 1.0 to the same Bullet bone. No independent insert-shell rig or spent-shell role is established.

**Lever:** an explicit rigid subset inside Frame, not the entire receiver. **Chamber:** a separate named rigid subset exists, but equating it with the footage loading gate is unverified. No Gate-named mesh/bone exists.

## Rig, actions and original part partition

Armature object `Armature`, data `Armature.001`, has seven deform bones: Pedestal, Slide, Hammer, Bullet, Chamber, Lever, Trigger. All except Pedestal parent to Pedestal. Every mesh vertex has one nonzero bone group at weight 1.0; each triangle lies wholly in one group.

**No stored actions, object/scene NLA tracks, mesh animation data or shape keys.** Two procedural armature drivers are present:

- `Slide.location[1] = .25 + var`, where var is Lever local ROT_X.
- `Hammer.rotation_euler[0] = -.576 + trigger if trigger < 0.001 or slide == 0 else slide *2`, from Trigger local ROT_X and Slide local LOC_Y. A Lever variable is also declared.

These mechanical relationships carry no reload timing. Stored pose offsets and constraints are in JSON; they are not a gameplay animation sequence.

Frame object is `A6D6FB80_Group2_Index8_2__lod_category_0`. Indices are zero-based, inclusive. Bounds below are W30 model coordinates: `X=8+s*sourceWorldX, Y=8+s*sourceWorldZ, Z=8+s*sourceWorldY`, `s=17.675692296761287`. -Z points toward the muzzle. Unposed source coordinates match the W30 builder.

| Object / bone | Vertex runs | Vertices | Triangles | Model bounds min; max |
|---|---|---:|---:|---|
| Sight / `Pedestal` | 0–2420 | 2,421 | 2,496 | [7.467924, 10.176083, 2.667620]; [8.494700, 11.550186, 7.326303] |
| Bullet / `Bullet` | 0–333 | 334 | 476 | [7.883256, 9.562138, 2.684055]; [8.089590, 9.813468, 6.425989] |
| Frame / `Slide` | 10063–10204 | 142 | 124 | [7.774460, 9.594971, 4.631887]; [8.209259, 10.016876, 7.775752] |
| Frame / `Chamber` | 2121–2172 | 52 | 48 | [7.670986, 9.529358, 4.521196]; [8.307169, 9.939819, 6.433540] |
| Frame / `Hammer` | 9754–10062 | 309 | 350 | [7.943284, 9.420258, 7.406205]; [8.056312, 10.201507, 8.497970] |
| Frame / `Lever` | 336–1317 | 982 | 944 | [7.742572, 6.094228, 4.747943]; [8.234282, 9.070451, 9.072613] |
| Frame / `Trigger` | 2659–3292 | 634 | 608 | [7.904180, 8.116778, 6.888960]; [8.087191, 9.153230, 7.755009] |
| Frame / `Pedestal` | 0–335, 1318–2120, 2173–2658, 3293–9753, 10205–18326 | 16,208 | 16,766 | [7.279090, 6.026326, -10.769520]; [8.808067, 11.227278, 14.230479] |

Lever identity is verified by **vertices 336–1317 / 982 vertices / 944 triangles**. Rest-bone head maps to **[8, 8.834439, 5.059170]**; bone-local X is approximately model +X. Saved local-X limits are **−36° to 0°**, Y/Z locked. These are rig capability only, not measured reload motion or a reason to animate the lever. Chamber’s source subset has 52 vertices / 48 triangles and rest pivot [7.692365, 9.817437, 6.365706]; its loading-gate role is unknown.

FBX 7500 independently has one skeletal root, six limb models, 17 Skin deformers and 119 Cluster deformers. Hashed names map by equal weighted vertex-index runs:

| FBX bone | Blend identity |
|---|---|
| `4A0810C4` | `Pedestal` |
| `69768858` | `Slide` |
| `689CCC6C` | `Bullet` |
| `BE811ABD` | `Chamber` |
| `2234F927` | `Hammer` |
| `14AC2D55` | `Lever` |
| `0CB702A7` | `Trigger` |

No FBX AnimationStack, AnimationLayer, AnimationCurve or AnimationCurveNode records exist; Takes contains only Current. The 17 raw geometry records total **84,348 vertices / 105,518 raw triangles**, including four identical Frame variants, four identical Bullet variants, four identical Sight variants and five tiny planes. These are not 17 distinct weapon parts. Array hashes and degenerate counts are in JSON.

Each Frame FBX variant has 22,846 raw triangles, 3,854 exactly zero-area, leaving 18,992 nonzero-area triangles versus saved Blend’s 18,840. The remaining **152-triangle discrepancy is unresolved**. Bullet 588−112=476 and Sight 2,943−447=2,496 match Blend counts. Do not attribute all Frame differences to degenerate faces.

## W30 cube mapping

W30 has **256 cubes / 1,536 quad faces / 3,072 triangles when quads are triangulated**, a flat 256-leaf outliner, no named groups, no bone bindings and no animations. Names are only source_volume_000–255. Runtime extents and face UVs match in the same order. The source reconstruction merges meshes before greedy volume packing, so source ownership does not survive as named groups.

Each cube is tested against canonical source triangles using triangle/AABB separating-axis intersection, tolerance 0.000001 model units. Shared-boundary contacts count on both sides. This establishes conservative **surface provenance**, not a preserved bone binding, ownership percentage or complete part isolation. JSON records all 256 names/UUIDs/bounds and source-bone triangle intersection counts.

| Source bone | Touching cubes | Exclusive surface candidates | Mixed cubes |
|---|---:|---|---:|
| `Pedestal` | 237 | 193 fixed candidates; complete list in JSON | 44 |
| `Bullet` | 10 | none | 10 |
| `Lever` | 36 | `source_volume_095`, `source_volume_164`, `source_volume_166`, `source_volume_168`, `source_volume_171`, `source_volume_174`, `source_volume_177`, `source_volume_181`, `source_volume_182`, `source_volume_183`, `source_volume_184`, `source_volume_185`, `source_volume_189`, `source_volume_191` | 22 |
| `Chamber` | 11 | `source_volume_240` | 10 |
| `Trigger` | 5 | `source_volume_190` | 4 |
| `Hammer` | 7 | `source_volume_208`, `source_volume_209` | 5 |
| `Slide` | 13 | none | 13 |

There are **193 Pedestal-only** fixed-surface cubes, **45 mixed-bone cubes**, and **18 single-moving-bone candidates** (14 Lever, two Hammer, one Trigger, one Chamber). Pedestal combines fixed Frame and Sight. No Bullet-only or Slide-only cube exists.

**Lever-only surface candidates (14):** `source_volume_095`, `source_volume_164`, `source_volume_166`, `source_volume_168`, `source_volume_171`, `source_volume_174`, `source_volume_177`, `source_volume_181`, `source_volume_182`, `source_volume_183`, `source_volume_184`, `source_volume_185`, `source_volume_189`, `source_volume_191`.

**Lever mixed with fixed body (22; keep fixed):** `source_volume_025`, `source_volume_073`, `source_volume_074`, `source_volume_075`, `source_volume_076`, `source_volume_085`, `source_volume_091`, `source_volume_092`, `source_volume_094`, `source_volume_096`, `source_volume_099`, `source_volume_100`, `source_volume_103`, `source_volume_163`, `source_volume_165`, `source_volume_167`, `source_volume_169`, `source_volume_172`, `source_volume_193`, `source_volume_194`, `source_volume_196`, `source_volume_197`. Cube 197 also touches Trigger.

Lever-touching cube envelope min; max: [7.470212, 6.026326, 4.660167]; [8.425823, 9.454929, 9.347667]. Lever-only candidate envelope: [7.661334, 6.407282, 5.441417]; [8.234701, 8.693017, 8.175792]. Spatial envelopes are not sufficient selection rules.

Chamber-only candidate is `source_volume_240`; ten other Chamber-touching cubes are mixed. Bullet touches ten cubes, all mixed. Exact sets and bounds are in JSON. No complete W30 lever, gate or shell group can be claimed from these candidates alone.

## Practical recommendation and footage bounds

1. Retain all 256 cubes, extents, face UVs and original texture. Add no ammo cubes and delete no body detail.
2. Use main-authored initial/loop/return poses for the intact body. Keep current internal ammo, sight and part candidates together.
3. Do not move all 36 lever-touching cubes: 22 include fixed body surfaces. Moving only the 14 unmixed candidates would leave part of the lever behind and can tear the shape. Chamber-only cube 240 does not prove complete loading-gate isolation.
4. Optional future source-part motion requires a complete part partition within existing cube/detail limits plus footage demonstrating this reload actuation. Original source weights prove a lever exists; they do not prove its reload motion.
5. User-provided W48 video `XPB6leAQKuQ`: 10.0 s raise; 10.2–13.4 s held tilt with repeated hand insert; 13.6 s skill interrupts reload. This audit did not decode video. Natural reload exit is not reliably visible; exact hand-occluded insertion path, gate angle and lever phase are unknown. Any return pose is authored, not a footage-verified natural exit.

Main owns footage, animation, generator and runtime. This audit changes only:

- `art/weapons/w71/references/original-model-audit.json`
- `art/weapons/w71/references/original-model-audit.md`
