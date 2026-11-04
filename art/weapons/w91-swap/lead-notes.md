# W91 N2 swap presentation handoff

Scope: distinct Austringer → Beloved and Beloved → Austringer only. Cosmetic server-tick samples on the currently selected incoming wire carrier: outgoing geometry during STOW, incoming geometry during READY. Existing source geometry, UVs, textures, runtime semantics and Handling deadlines remain authoritative. These locally authored transforms are not measured original frames, render-frame interpolation or hand IK.

## Lead files and parent integration

- `src/main/java/kim/biryeong/destiny/weapon/WeaponSwapPresentation.java`
- `src/test/java/kim/biryeong/destiny/weapon/SwapPresentationW91Test.java`
- `src/gametest/java/kim/biryeong/destiny/test/WeaponSwapPresentationW91GameTests.java`
- `art/weapons/w91-swap/lead-notes.md`
- `art/weapons/w91-swap/native-scenarios.json`

Public helper API: `SELECTOR_INDEX=5`, `supports(fromEntry,toEntry)`, `update(owner,current,outgoing,phase,progress)`, `active(stack)`, `model(stack)`, `clear(owner,stack)`, `cleanup(owner)`, `clearAll()`. `STEPS=20` means 21 samples per phase. Encoded sample is STOW `0..1` / READY `2..3` plus a stable positive binding offset below `.001`. Choose the offset to avoid the saved slot5 and prior donor live value across every phase/sample, invalidating component-keyed wire caches. Existing generator thresholds tolerate this offset, including exact final HIP samples.

Parent confirmed and implemented `WeaponSwapCycle.progress(long tick)` and `WeaponHandling.Presentation(outgoing,phase,progress)` / `Optional<Presentation> presentation(ServerPlayer)`. Presentation reads that view without binding state or moving clocks. It also requires actual current stack identity, matching live combat entry, owner object/level and usable loadout. Parent calls `update` from Handling only with present view, otherwise owner cleanup; each real selection cleans the prior binding. Parent alone owns shared classes/registry/README/index/journal/QA. No shared file was edited by this lead.

Parent route priority: swap before reload/Izanagi/ADS. Route through `WeaponSwapPresentation.active(stack)` then `model(stack)`; never infer authorization from persisted CMD. Shared runtime State.cancel must not clear swap because Handling is independent. Parent Handling.cleanup/clear paths own lifecycle cleanup. Register `kim.biryeong.destiny.test.WeaponSwapPresentationW91GameTests` in the parent-owned GameTest entrypoint list.

Binding is an identity map keyed by actual ItemStack, holding owner object, exact level, pair, phase, original nullable slot5 and offset. An exact-stack recipient inherits the pre-donor slot5 snapshot, not donor's live sample. Old-owner `clear/cleanup` cannot retire recipient state. Cleanup modifies only slot5 and preserves all newer lower/higher floats, flags, strings and colors. If slot5 originally did not exist, remove it only when trailing; otherwise neutralize it without shifting higher indices. Lower padding is retained because lower slots belong to other renderers. Getter/model queries never mutate authoritative components or authorize gameplay.

## Delegation and first review

Exactly one native ASSET child: `01a16f6c-0695-7680-bf60-33b280461e21` (Leibniz), `logicalParent=L1 N2`, `spawnedBy=topmaster`. This lead had no native spawn/wait/close tools, reported the exact-file request early, and did not use app task creation. Master broker created the actual native child and relayed completion/write release. No direct spawn or direct close by this lead is claimed.

Child files: `scripts/generate_swap_presentation_w91.py`; two `src/main/resources/assets/destiny/items/weapon_swap_w91/{austringer_to_beloved,beloved_to_austringer}.json`; 168 children under `src/main/resources/assets/destiny/models/item/weapon_swap_w91/`; `art/weapons/w91-swap/asset-manifest.json`, `asset-samples.json`, `asset-authoring-notes.md`. Total 174 files including generator. No child edits were made by this lead.

First review status: **reviewed; no child correction required; close requested through master**. Master closes via its available native tool; close confirmation was not yet received when these notes were written. Read generator and actual outputs; direct read-only reconstruction produced `Verified 173 W91 files; 168 display children, 2 pair items, 3 asset reports`. Independently checked 27 input hashes, 26 original hashes and 172 output hashes. All 174 child-owned file contents and mtimes were identical before/after verify. Consumed input pin: `68f9e5fee9a785ce48bce7ad173ee1974a4d9edc38642dde3584de2163d9741a`.

Review confirmed pair paths, outgoing/incoming phase parents, source-only parent/display children, exact native/twohand HIP endpoints, both-hand current-carrier matrix compensation, float32 threshold routing, and exact incoming non-first-person graph fallback. Detailed source parents have Austringer 255 / Beloved 253 cubes; original face UV and atlases are inherited untouched. The test initially compared twohand child non-first-person contexts to native originals; corrected to the actual carrier-specific original display while retaining exact endpoints and geometry inheritance checks. Child accurately identified this assertion conflict.

## Central verification pending

JUnit: two tests in `SwapPresentationW91Test` check only the two supported catalog directions plus native ItemModels/CuboidModel codec, complete 2-item/168-model inventory, all 42 thresholds, exact endpoints, inheritance, unrelated contexts and both-hand carrier compensation. Production pathways are used rather than a mocked selector algorithm.

GameTest: nine tests use real validated slot packets, actual Handling/runtime ticks, actual Polymer packet contexts and NBT ItemStack codec; no direct presentation activation or synthetic time. Cover both pair directions with both incoming carriers, exact incoming HUD/ammo/custom data/charged sentinel preservation, real deadlines, same-tick retarget/building detours, READY interruption, skill/ADS suspension, owner/stack/level/spectator/death/super cleanup, saved-selector/preview rejection, exact donor handoff and late cleanup, absent slot5, unrelated newer field preservation, and actual context-cache invalidation for saved `0`/offset/future READY collisions and simultaneous donor/saved collisions. Each fixture registers `TestCleanup.register`; all tests declare `destiny-test:w90_isolated`.

No Gradle/build/Java test/GameTest/native codec execution, commit, server/client startup or user app operation was performed. Executed checks were limited to read-only offline asset reconstruction/hash/mtime audit, scenario schema/test declaration inspection and whitespace inspection. Central execution/registration/integration and independent parent review remain required. `native-scenarios.json` contains four `planned_unrun` scenarios with null candidate pins, fixture/native separation, unsupported Q/slot-input boundaries, no listening claims and terminal cleanup requirements. No native screenshot or audio acceptance is claimed.

Lead implementation, tests and manifests are ready for parent review; lead writes released after final static inspection. Child already released its own writes. No further build gate may be attributed to this lead.
