# W227 owned equipment service

Root: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow`

## Owned delta

Only these two worktree files were created (both absent at worker start):

- `src/main/java/kim/biryeong/destiny/inventory/WeaponEquipmentService.java`
- `src/gametest/java/kim/biryeong/destiny/test/WeaponEquipmentW227GameTests.java`

Manifest: `/private/tmp/destiny-w227-equipment/delta.json`. Paths are relative to its root; SHA-256 values describe the final worktree files.

## Implementation

`Owned` retains actual index and exact stack reference. `owned` scans indices 0..35 in order, includes only count-one live `WeaponItems.entry` matches for the requested characteristics category, and marks equipped only at that category's hotbar index. It performs no runtime observation, attachment write, ammunition migration or component mutation.

`equip` rejects off-server-thread, dead, removed, spectator, disconnected, super-active, stale-reference, invalid-index, preview and count-not-one requests before lifecycle/write calls. Rejections preserve enabled state. Sources in the wrong equipment bucket 0..2 cannot steal a category even if its destination is empty. Nonempty destinations must be valid count-one live weapons of the destination category. Resulting real equipped slots admit at most one exotic; stored/misfiled weapons do not count, and a replaced exotic is excluded from the conflict count.

Accepted swaps exchange the exact source and destination objects, without item creation/copy/destruction or ammo/roll saves. Existing `WeaponHandling.update`, `WeaponRuntime.cancelUseForSkill`, inventory mutation mixins and (where selection changes away from another held object) `selectedSlotChanging` own lifecycle. Selection is set to the category hotbar with `ClientboundSetHeldSlotPacket`, enabled attachment is set true, and inventory/menu changes are broadcast. Moving a held source preserves its held identity without an artificial intermediate Handling transition. A currently held, correctly equipped no-op only enables the loadout if necessary; it does not cancel pending runtime work or reset cooldown. The controller may already have cancelled use on screen open.

## Prepared GameTests

Ten methods use the project's Fabric 26.3 `@GameTest`, `TestPlayers`, `TestCleanup`, existing floor structure and `w90_isolated` environment. No registration was edited.

- Exact-reference finite-special swap at main index35; all components, actual selected socket rolls, reserve/overflow totals and unrelated slots retained; actual Handling timing and held-slot packet.
- Ace from storage index9 to kinetic0, original Austringer displaced to9 with both ammunition/component states retained.
- Preview, component-equal copy, stale object after replacement, count2, negative/36 index and null token rejected while an existing reload, every inventory reference/component, selected slot and enabled attachment remain unchanged; attachment false and true both checked.
- Invalid/preview/wrong-category/count2 destinations and stealing from wrong hotbar buckets rejected.
- Pure category projection with indices0/1/8/35, wrong-category placement, preview, count2, legacy ammo data, armor and offhand; repeated calls leave state unchanged and send no packets.
- Same-slot enable and repeated no-op preserve actual shot cooldown and pending reload.
- Held source movement and stowed equipped selection preserve identity/cadence and send category selection.
- Off-thread call, spectator, death, super and removed player rejection, with both enabled states.
- Misfiled second-exotic rejection and legal same-category exotic replacement/storage behavior.
- General distinct-category exotic-conflict rejection loop, with both enabled states when a catalog pair exists.

## Evidence and limits

Read worktree `AGENTS.md`, `/Users/qf/.codex/RTK.md`, and the minecraft-testing skill. No `.codegraph/` exists in this slot. Verified current source contracts in `WeaponLoadout.equipHeld/select`, `WeaponHandling`, `WeaponRuntime` cancellation/selection/cadence/reload paths, `InventoryAceMixin`, `WeaponItems`, `WeaponCharacteristics`, `WeaponPerks`, `TestPlayers`, and existing W40/W58/W59/W113 GameTests. API matches are source-reviewed, not compiler-confirmed.

Performed read-only skill layout validation: PASS with one warning (the generic skill validator only looks in `src/test`, so it does not discover this project's separate `src/gametest` layout). Separately confirmed that the referenced floor SNBT and isolated environment JSON exist. Scoped `git diff --check` returned success; because these files are new/untracked, explicit final-file trailing-whitespace/newline/brace checks were also performed. Lightweight source checks confirmed ten annotations, no item create/copy/shrink/grow/split calls in the service, no mutators/runtime observation in projection, and validation preceding the first attachment/lifecycle mutation. SHA-256 manifest was generated from final files.

IMPORTANT: current production `WeaponExotics` appends only W83 Ace and W84 Izanagi; both have KINETIC characteristics. A real distinct-category exotic-conflict fixture is therefore impossible with the retained catalog. The general test's rejection loop currently has zero pairs. It is prepared for a future catalog pair, not claimed as exercised coverage of the exotic-limit branch. The current misfiled second-exotic test exercises wrong-category rejection, not the exotic-conflict branch. No global catalog reflection, synthetic production definitions or perk expansion was introduced.

No Gradle, compilation, GameTest/server/client, native/Vision/ComputerUse, shared build, main-checkout edit, commit or remote push was performed. Central registration, compile, test execution and native equipment batch remain master-owned. No runtime pass is claimed. No child agents were created.

## Follow-up: corrected same-slot cooldown oracle (2026-10-28)

Latest `delta.json` contains ONLY the revised GameTest file, ready to apply over original test SHA-256 `2fc66bbf009ee45102a3e35ac2650aafa75f1f30142d954adbb9b464a8821493`.

Revised test SHA-256: `d5fb018d35a0394c113bf78c08e7f01a547e403594b2f20a4545cf395ac5dbda`.
Service remains byte-identical: `d4ede03cdbb7417f0aa6618fdc200014cf756f0acef7d5adfd1b0364d9332299`.

Central evidence read: `/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-28/w227/server-1.log` and `server-1-report.xml`. XML has 11 targeted server cases, 10 passing and the sole failure at the original test line252: `No-op cannot erase paid shot cooldown on tick 0`. Central compile and ten pure UI tests passed per master; those separate results were not rerun here.

Source diagnosis: `WeaponRuntime.beginUse` checks `if (s.holding) return true` before evaluating `s.cycle.ready`. The test's first accepted shot leaves that holding flag set. A second logical use can therefore return true without firing or spending ammo. The original negative-return assertion was an incorrect oracle, not evidence of a service cooldown defect. `WeaponCycle.fire` owns the actual magazine debit and firing deadline; `releaseUse` clears holding without resetting that deadline.

Correction is limited to the failing test method. The initial shot must now actually debit rounds5 to4. After same-slot equip enables the loadout, duplicate use must leave rounds4 and every component unchanged. The test then calls real `releaseUse` and retries a fresh press in the same tick, again asserting rounds4 and unchanged components. Clearing the duplicate-input guard ensures a cooldown reset would debit rounds4 to3 and fail the test rather than being masked by holding. The existing subsequent pending-reload/no-op state checks remain intact. No service or other test methods were changed.

Verified before revision that slot/main original test hashes matched; after revision a unified diff against the unchanged main baseline shows only this method changed. Final newline, trailing whitespace, balanced braces and ten GameTest annotations checked; service hash rechecked unchanged. No build, server, Gradle or runtime test was run for this correction; central rerun remains master-owned.
