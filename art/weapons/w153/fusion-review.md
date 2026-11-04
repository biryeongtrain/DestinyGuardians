# W153 fusion ADS physical sights

Implemented in the existing dirty-seeded CoW linked worktree `w153-fusion`.
The original repository and dependency sources were read-only. All nine delta
paths are exclusively owned by this batch. No canonical HIP/third-person/reload
models, source textures, W123 design/provenance, Java, shared generators or QA
documents were changed. No companion is required: each ADS body is the complete
W123 static assembly, including its seated cartridge/cell/powerpack exactly once.
Do not append another magazine when creating the shared wrappers.

## Sight decisions

The minecraft-weapon-art-design skill and Ace/Izanagi study informed preservation
of functional solid volumes and real openings. The actual five default reference
photos were opened with `view_image`; their hashes agree with W31 and each W123
manifest/design. W151 pulse/rifle generators and targeted tests supplied patterns,
without importing or changing them. Source is always the actual
`models/weapon_surface_w123/<id>.json`, not the historical W30 canonical model.

| Weapon | Cubes source → ADS assembled | Eye relief | Sight center XYZ | Visible original hardware |
| --- | ---: | ---: | --- | --- |
| `erentil_fr4` | 135 → **137** | 0.48m | `[8, 14.6, 2.815]` | omolon_blue_raked_reflex |
| `hollow_words` | 96 → **98** | 0.60m | `[8, 14.48, 5.56]` | taken_long_chamfered_box_tube |
| `dream_breaker` | 186 → **187** | 0.55m | `[8, 13.62, 3.79]` | lunar_original_fork_and_post_irons |
| `null_composure` | 91 → **93** | 0.42m | `[8, 14.3, 1.57]` | gold_foot_arched_black_reflex |
| `coriolis_force` | 104 → **106** | 0.32m | `[8, 15.3, -0.2]` | europa_red_twin_open_ears |

All counts include the seated assembly once, with **zero triangle adapter
outputs**, and remain below 1,000. Full versus split representations are not
summed. No fake split resource or companion schema is introduced. W151-compatible
rows retain `id`, `family`, `body`, `sightCenter`, `forwardPoint`, `eyeSide`,
`plane`, `scale`, `eyeToSightMeters`, `elementCount`, `source`, `sourceSha256`,
removal/addition lists, style, aiming tip and reference provenance. Body parents
are absent and source `display` is omitted for master-owned ADS wrappers.

### erentil_fr4

Photographed blue raked reflex on toothed silver rail, left adjustment dial, open square window. Preserve all original roof/uprights/sill/dial UVs and hoses. A small pale pin seats on the real sill; 0.48m relief keeps the blue frame visible above the stock.

Actual photo: [erentil_fr4](https://www.bungie.net/common/destiny2_content/screenshots/2398848320.jpg); opened local `/tmp/destiny-weapons-w31/references/erentil_fr4.jpg`. SHA-256 `2e018c1643cb9851ca6580470db4d670d50f1a5cb44ccec846cdb7478301a58c`.

### hollow_words

Photographed long dark rectangular tube, chamfered corners and narrow base over teal/gold marbled rail. Retain all nine original optic solids and their UVs; no opaque glass exists in W123. A small pale pin stands at the objective end inside the existing tunnel; 0.60m relief preserves its long-wall perspective.

Actual photo: [hollow_words](https://www.bungie.net/common/destiny2_content/screenshots/607191995.jpg); opened local `/tmp/destiny-weapons-w31/references/hollow_words.jpg`. SHA-256 `192adbf328450c2e53a98c63c4fd3a3eabe862b34f10aad8ab3171b444d14390`.

### dream_breaker

Actual photo has low irons along the ivory cord-wrapped housing, not a scope. Keep the source fork pair and foot. The tall original front post would overlap the useful lower sight field; shorten only that post in the ADS copy, crop its original side UVs, and give its upper 0.05 units a pale cap. 0.55m relief views the real notch ahead of the shoulder, without removing the stock.

Actual photo: [dream_breaker](https://www.bungie.net/common/destiny2_content/screenshots/2931957300.jpg); opened local `/tmp/destiny-weapons-w31/references/dream_breaker.jpg`. SHA-256 `08d67d733f1af642286388f394992277a08ed9a14dc20599f0cedaa1c8b199b3`.

### null_composure

Photographed black arched reflex with open low cheeks, gold feet and side dial above blue breech. Keep every original hood/arch/dial/foot and face UV; place the pale guide on its existing sill inside the real opening. 0.42m relief keeps the sight ahead of the rear buffer and shoulder.

Actual photo: [null_composure](https://www.bungie.net/common/destiny2_content/screenshots/1644680957.jpg); opened local `/tmp/destiny-weapons-w31/references/null_composure.jpg`. SHA-256 `48a6fc624ae06d766947dcbae4568e78412b6284947031d580097787799754ad`.

### coriolis_force

Actual photo shows two tall red open ears on the ribbed top shroud; no reflex roof/tube is invented. Keep both source ears, rear sill and all asymmetric U-clamp/stock parts. Seat a short pale guide on an existing shroud bridge. Forward 0.32m relief puts the rear upper stock rail behind the eye and leaves both ears visible.

Actual photo: [coriolis_force](https://www.bungie.net/common/destiny2_content/screenshots/3512349612.jpg); opened local `/tmp/destiny-weapons-w31/references/coriolis_force.jpg`. SHA-256 `0ded6a9889a127e244206734293d7d7f187fa7a058fd32076fae61100f8ff0c7`.

## ADS-only changes and source preservation

Erentil, Hollow Words, Null Composure and Coriolis retain every original element,
rotation and face UV exactly. Each adds two seated guide cuboids: a small dark
stem and pale green-white tip. The original W148 sights atlas supplies its opaque
metal swatch at UV `[0,0,1,1]` and pale tip at `[4.25,.25,4.75,.75]`; its bytes are
unchanged and hash pinned. These physical aiming guides are a visibility
adaptation, not recovered Destiny shader reticles or glass. No new lens card
fills any opening, and no generic replacement sight/hood is pasted onto the guns.

Dream Breaker replaces only `front_sight_post`. Its original bounding box is
`[7.955,13.36,-7.64]` → `[8.045,13.6,-7.46]`. The replacement retains exactly that
X/Z footprint and base; its new top is **13.458017**, a **0.141983** unit trim in the
ADS copy. The lower stem retains the original face texture slots and crops side
V coordinates to preserve texel density. The upper 0.05 units are a pale cap.
The original source post demonstrably intersects the declared viewing window;
reinserting it fails the obstruction regression. Rear forks, base, wraps, stock,
links, housing, grip and seated powerpack remain value-identical. No non-sight
obstruction fix is necessary on these five candidates, and no optic is removed
for convenient placement behind a stock.

Eye distances deliberately differ. Coriolis seats at 0.32m: eye Z=5.4888889 and
its unchanged upper stock rail starts at Z=5.63, behind the eye. Dream Breaker's
eye Z=13.5677778 lies ahead of its tall butt at Z=14.785. For the remaining models
the elevated original optical paths and source rims remain visible above the
retained rear structure. The manifest pins source textures and W123
`design.json`, `manifest.json`, `review.md`, raw FBX/BLEND provenance and photo.

## Offline verification and visual inspection

**15 targeted unittest cases pass.** The generator reproduces all six generated
files byte-for-byte. `--verify` is nonwriting on both success and mismatch; tests
forbid `Path.write_bytes` and `mkdir` during verification. A preservation check
also hashes source/canonical models and textures and checks their mtimes before
and after generate/verify.

The ray checks invert native XYZ and legacy axis rotations, including legacy
rescale, and use exact finite segment/slab intersections. Each body is tested
with 81 parallel and 81 perspective rays through a useful asymmetric rectangular
window (width 0.24–0.36, height 0.235–0.305 model units). This leaves air above the
aiming point rather than certifying only a tiny center ray. The physical tip is
visible with no intervening part, with a 0.075-unit apparent vertical gap on the
rear sight plane. Actual eye-facing surfaces on both original sides/forks/ears
and the existing hood, where present, have at least 4/9 unobstructed samples.

A W152 regression fixture surrounds a tiny clear center hole with foreground
stock panels. Both center and aiming-tip rays still pass, while the broad window
and original optic visibility fail. This prevents accepting a hidden optic only
because its central ray remains clear. Tests additionally cover original post
reintroduction, all source geometry/UV preservation, actual reference hashes,
finite JSON/UV/texture references, unique names, exact output scope and assembled
budget. Hollow Words' existing cell is named `under_grip_cell`; it is explicitly
included in the seated-cell regression, without inventing a magazine resource.

A transient in-memory CPU textured view from each declared eye was inspected:
Erentil has its full blue window, Hollow Words shows its nested chamfered tunnel,
Dream Breaker shows both rear fork tips and the forward post above the wrapped
housing, Null Composure shows the arched opening and side dial, and Coriolis
shows two distinct red ears above the ribbed shroud. No preview file was written.
This was a zoomed geometric/UV inspection, not a native screenshot or PBR proof.

Executed targeted commands:

```text
rtk proxy python3 -B scripts/generate_sight_bodies_w153_fusion.py
rtk proxy python3 -B scripts/generate_sight_bodies_w153_fusion.py --verify
rtk proxy python3 -B scripts/qa/test_sight_bodies_w153_fusion.py
```

## Master-owned native followups

Master owns shared18 admission, ADS21frame wrappers and Java registration. Use
each row's scale 0.9, +Z eye, XY plane, exact center/forward point and individual
eye relief. The complete static body must not receive a duplicate magazine.
Validate actual26.3 parser/pack loading, source rotations/textures, first-person
ADS frame and both original optic sides, physical aiming point at settled and
transition frames, twohand where supported, charge/fire and muzzle alignment,
reload return/ammo timing, and unchanged HIP/third-person appearance. A short
10–20-display check and native audio/charge check remain with master. No Gradle,
CU/Vision, game/server or native acceptance was run or claimed here.

## Exact owned delta

- `scripts/generate_sight_bodies_w153_fusion.py`
- `scripts/qa/test_sight_bodies_w153_fusion.py`
- `art/weapons/w153/fusion-sights.json`
- `art/weapons/w153/fusion-review.md`
- `src/main/resources/assets/destiny/models/weapon_sight_w153/erentil_fr4_body.json`
- `src/main/resources/assets/destiny/models/weapon_sight_w153/hollow_words_body.json`
- `src/main/resources/assets/destiny/models/weapon_sight_w153/dream_breaker_body.json`
- `src/main/resources/assets/destiny/models/weapon_sight_w153/null_composure_body.json`
- `src/main/resources/assets/destiny/models/weapon_sight_w153/coriolis_force_body.json`

Export target: `/private/tmp/w153-fusion-export`; `worktree_batch.py export`
checks the dirty-seed baseline, exact ownership, source conflicts and hash drift.
The export is a handoff delta only; it is not integrated into main.
