# W219 Dead Man Walking XX7463 — FIRST same-worker no-change review

## Scope and status

Prepared first in `/private/tmp/w219-dead_man_walking_xx7463-prepare`; installed exactly three files after explicit READY in `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w219-dead_man_walking_xx7463`. FIRST same-worker image review is now complete; SECOND remains pending. No main checkout, generated output, shared loader, Java, rig, build, client, server or CU/Vision writes were made. No commit/reset/stash/clean/push. Exactly three owned files:

- `scripts/generate_reload_w219_dead_man_walking_xx7463.py`
- `art/weapons/w219/dead_man_walking_xx7463/profile.json`
- `art/weapons/w219/dead_man_walking_xx7463/review.md`

## Original evidence before implementation

Read main AGENTS.md, RTK.md, weapon-art skill and Ace/Izanagi study. This is a semantic moving-part split, preserving the current teal SUROS casing, oval muzzle, lower rail, red controls and dark swept grip/UVs.

The master evaluated original `sidearm_60848ee7/blender/source.blend` read-only with separate Blender5.4.0 Alpha. Worker read `/private/tmp/destiny-w219-source/source-review.json`, fresh `/private/tmp/destiny-w219-source/sidearm_60848ee7.json`, and VIEWED the actual `sheets/sidearm_60848ee7-80A8A560-upper-chain.png`. Worker did not independently open/evaluate Blender. Report: ARMATURE only, OBSlot, `Armature|fp_80A8A560_reload_full|Base` shared reload_full/reload_empty action, source1..67 at30fps,61 evaluated samples, prior-cache joint error0, original inputs unchanged. No weapon mesh, camera or finger IK was recovered.

Own source weapon bone is4A0810C4; LEFT D1232BA2 ->897A1504 ->8C83CB67 is the handling chain, RIGHT17025F50 ->A3781DCD ->DE9D6BEA stays near the grip. At32 units, source LEFT wrist relative to weapon changes from about Y+.52 atp0 toY-16.58 atp.35, returns toY-1.61 atp.50, then rises toY+6.39 atp.65. RIGHT remains aroundY1.61..1.83. This supports explicit LEFT and releasing the seated magazine before later wrist motion; it does not recover exact magazine events or contacts.

## Product changes and authored limits

Canonical W123 selected surface has100 elements. Move `heel_core`, `heel_roundover_-1`, `heel_roundover_1` together as the complete existing heel/baseplate. Their old design group is `grip`; treating this connected heel as the detachable magazine baseplate is an authored semantic interpretation, not recovered mesh truth. Keep filled_grip, filled_lower_haunch, straps, panels, latches, trigger and receiver fixed. No canonical elements/UVs are changed.

Add only one dark `authored_internal_magazine_shaft`, local `[7.45,7.0,6.35]..[8.55,11.2,7.55]`, using the unchanged filled_grip rotation and existing dark bevel UV faces. It is strictly inside the fixed opaque grip at rest, meets the heel and gives the withdrawn baseplate a magazine body. Its hidden dimensions and UV allocation are authored. No invented open magwell or new atlas.

The61-pose bank replays this source's original weapon transform, source-parent coordinate basis and32-unit conversion, with the existing .1 endpoint rest blend. Body and child transforms support native/twohand and both first-person hands. Authored C1 withdrawal/hold/reseat fallback follows only this own source timing; no trajectory is borrowed from another weapon. `gripWindow=[.08,.15,.46,.53]` reaches LEFT handling, holds through withdrawal/return, and releases by the authored.53 seat. Magazine remains present with positive scale throughout; no hiding/axis damping/stretching. Master shared source-palm fit translates the magazine to the original LEFT palm during the window while preserving ordinary source arm directions and lengths.

Profile preserves effective sidearm spatial framing: translation[-1,.25,0], rotation[-1,0,0], scale.98, rightWristRoll27; sourceFullChain=true, keepMeshSupport=true, hideSupportAtRest=false. Existing right/left and reload contact coordinates/rotations are retained. SourceFullChain adds ordinary fingerless player-skin full arms through master integration; source did not contain a player skin.

## Integration contract

Pure stdlib, inert import. `generate(root=ROOT)` returns absolute Path->bytes without creating directories or writing outputs. Explicit `rig_path`/`profile_path` keyword overrides support scratch no-write preparation. Installed default requires master-owned `art/weapons/w219/rigs/sidearm_60848ee7.json`; worker never installs rigs. Current root inputs are read and hashed dynamically, with semantic validation and no pinned new shared-file hashes.

Returns only247 own pack files under `models/weapon_reload_w219_dead_man_walking_xx7463/`, own item `items/weapon_reload_w219_dead_man_walking_xx7463/dead_man_walking_xx7463.json`, and own manifest:248 returned files total. Static geometry2, parent/display children244, item1, manifest1. Exact61 thresholds float32(i/60),60 intervals. Complete canonical item graph at0/1, negative inactive, positive overshoot and nonFP. Original ADS/inspect guards precede reload; native/twohand flag0 and reload progress float1 remain.

Master must load the W219 profile/rig/action and route this weapon. The shared `source_weapon_display` replaces baked body motion from ready (it does not multiply body motion twice) and retains relative child offsets. Master owns full arm materialization, actual all-route counts, Java lifecycle/routing, builds and FIRST/SECOND Vision. Worker has not run shared generators or game processes.

## Bounded verification

Passed AST syntax, audited inert import and two no-write generations with process/network/write operations blocked; deterministic mappings; exact output namespace; canonical endpoint/inactive/overshoot/nonFP and ADS/inspect guards; native/twohand endpoint displays; finite transforms and positive unchanged scales; intact100 canonical solids/UVs; fixed grip names and whole baseplate split; shaft containment in the same rotated grip frame; no magazine offset after seat.

Actual candidate geometry97 body+4 magazine=101 weapon elements; +448 classic arm surfaces=549. Selected surface100+448=548; raw canonical223+448=671. Alternatives are not summed. Maximum inspected alternative671<=1000; master composed all-route/ADS/inspect measurement remains pending.

Unchanged existing numbers:16 rounds,450RPM, cadence2.666666666667ticks, burst1, reload36ticks, shellReload=false; reload sound entries21/36ticks retained. No gameplay, ammo, cadence, reload clock or sound edits.

## Required feedback sequence and native limits

Original master Blender evaluation ->61-pose candidate ->master FIRST actual native capture ->same-worker FIRST review is complete. Decision: retain all geometry, shaft dimensions, UVs, contacts, source arms/body, framing and `[.08,.15,.46,.53]` gripWindow. Only review/evidence metadata changes in the three owned files;247 generated pack asset bytes remain identical. Master performs fresh SECOND after integrating these owned deltas; no final native acceptance is claimed.

### Actual FIRST images viewed and seat decision

Evidence root: `docs/qa/2026-10-28/w219/vision1/`. Worker VIEWED both requested `screenshots/dead_man_walking_xx7463-review.png` and `dead_man_walking_xx7463-reload.png`, then full actual `frames/w219-dead_man_walking_xx7463-reload-sample-{05,06,07,08,09,10,11,15}.png`, `...-ads-sample-08.png` and `...-after-reload.png`. Profile records their SHA256 and individual observations. Read sequence capture metadata and server reload timeline; capture indices are not61-pose indices.

- Ready/ADS: both ordinary arms present; native-grip ready contact reads as supported. Full ADS08 retains the red-tipped rear posts/open iron gap, with no arm crossing that gap. Server timeline explicitly says `grip=native`; visible two-arm support does not independently verify the separate twohand carrier.
- Extraction05/06: fixed filled grip remains on body; dark magazine shaft goes low beside LEFT hand. Part of the outgoing assembly reaches the lower screen edge, so the selected sheet alone cannot prove complete heel visibility or its exact junction.
- Return08: shaft is visible immediately above/alongside LEFT block palm, aiming toward the underside of the fixed grip. Lower baseplate is partly obscured by the palm; no obvious floating shard or open shaft-to-palm daylight is visible. This reads as credible coarse fingerless handling, not proven finger wrap or an exact original contact.
- Seat09/10: separate exposed shaft disappears into the fixed grip and the heel reads seated; LEFT hand then rises while heel stays put. Capture08 spans clientTick969..970;09 is972. Nearby serverTick1565 reports p.51666665, bracketing this transition near the authored.46..53 release. These clocks are not frame-synchronized, so no individual PNG is asserted to be exactlyp.53.
- Later11: LEFT palm crosses the receiver in the original-source late sweep; magazine does not visibly reappear as a withdrawn shaft. Retain release by.53 to avoid tethering the seated heel to that sweep. Do not stretch/damp/hide the source arm to remove it.
- Recovery15 and full after-reload: returned ready framing without a detached shaft; final image HUD16rounds. ServerTick1583 independently returns canonical inactive `[0,-1]`, reloading=false, ammo16/0.

There is no definite owned geometry/contact/timing blocker in these full-frame observations. Changing good shape/framing or delaying release would have no observed justification. Retain the sourceFullChain/keepMeshSupport settings and visible normal-length arms. The palm-occluded shaft/baseplate junction and unsampled exact seat microtransition remain focused SECOND observations, not passed claims. No fresh native command, shared generation, main/shared writes or Gradle was used by this worker.

### Remaining native limits

Master SECOND must reconfirm extraction, return/seat near.46..53, no late magazine pull during receiver sweep, ready return and clear ADS gap. FIRST sampled native-grip PNGs do not independently verify separate twohand carrier, lefthand display, inspect, every subframe, continuous60fps interpolation,10–20-item performance or all-route composition budgets. Original source remains ARMATURE only; authored shaft, baseplate interpretation and contact window have not become recovered source mesh/IK truth.
