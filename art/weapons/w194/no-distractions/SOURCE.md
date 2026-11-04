# W194 base No Distractions

This batch supplies a stateless profile and held-stack validator for base Trait **2866798147**. Master owns registry, Aiming, lifecycle, HUD and scoped server-test integration. The copied shared Aiming source still admits only intrinsic Izanagi; helper compilation alone does not establish live activation for the five legendary rolls.

## Source and exact scope

The user-designated DDC **Weapon Perks, gid1662574278, row152** says: after **1 second of ADS without firing**, **35% Flinch Resist while ADS**; the timer starts when the ADS input is pressed. The row's yellow **↑0.9** and **0.9?** annotations belong to enhanced No Distractions **3974407819** and are excluded. There is no activity-specific PvE/PvP value stated in this row. `source.json` preserves the complete exact-name-matched row as `ddc.rawHTML`, alongside plain base text and the yellow spans, so flattened text cannot silently promote enhanced timing to the base trait.

The generator pins the inventory, plugsets, manifest, DDC and canonical catalog/characteristics/exotic inputs by SHA256. Manifest version is **245114.26.10.13.2000-1-bnet.66137**. It scans every one of the **65** canonical entries, including exotics, then restricts matches to category **4241085061**, actual `randomizedPlugSetHash` references, `isFakePlugSet=false`, `currentlyCanRoll=true`, exact `itemTypeDisplayName="Trait"` and exact base hash2866798147. Each matched weapon must be legendary and nonexotic. Same-name exotic-specific hashes and Enhanced Trait are not admitted. Fixed Izanagi's intrinsic socket is outside the randomized pool and remains supported by the existing `exactIza` branch.

| Canonical ID | Official weapon hash | Socket | Real randomized plugset |
|---|---:|---:|---:|
| biting_winds | 1621657423 | 3 | 3968704963 |
| bite_of_the_fox | 1403800851 | 3 | 563442205 |
| beloved | 3107853529 | 3 | 1196545279 |
| apostate | 2164448701 | 3 | 1306932196 |
| fixed_odds | 2194955522 | 3 | 4227334000 |

The generated resource contains exactly these five tuples. Provenance contains all65 positive/negative results, every examined trait socket/pool status, the complete base definition, each positive category/socket/plug proof, input hashes, helper hashes, generator hash and resource hash. No candidate shortlist substitutes for the catalog scan.

## Settled helper API

`NoDistractionsProfile.ID`, `HASH`, `rolls()` and `supports(entry)` expose the exact base pool. Initialization reads only its own JSON and constructs value records; it does not call the live catalog, characteristics or registry during initialization. The loaded timing/resistance must equal existing `WeaponFlinchState.PROC_TICKS` and `NO_DISTRACTIONS_RESISTANCE`. There is no second source of runtime timing or resistance.

`WeaponNoDistractions.eligible(ServerPlayer, ItemStack)` is a pure **source eligibility** check: connected/alive/nonremoved/nonspectator owner, no active Super, usable loadout, actual selected hotbar object identical to both main-hand and selected inventory slot, count1, live combat item, matching canonical model/entry and one of the exact supported official weapon hashes. Eligibility alone does not assert that this perk is selected and does not assert ADS.

`WeaponNoDistractions.selected(ServerPlayer, ItemStack)` adds `WeaponPerks.selected`'s strict saved integral hash/socket validation and exact allowed `Roll` membership, including weapon hash, perk hash, socket and plugset. A copied/foreign/offhand/nonselected stack cannot qualify. `selected(ServerPlayer)` delegates using the current main hand. These methods create no attachment/session, advance no timer, mutate no tag, and retain no owner, stack or level. Loadout/guardian reads use existing pure paths.

## Master application and lifecycle hooks

Register `NoDistractionsProfile.ID`, `HASH` and `rolls()` in shared `WeaponPerks.available/ids/name`. The helper intentionally delegates selection decoding to that shared registry; before registration its selection query is inert. Do not introduce another NBT parser or alter legacy corruption/fallback behavior here.

In `WeaponAiming.updateNoDistractions(Session s)`, retain `exactIza` and tick the **existing** `s.flinch` with:

```java
(exactIza || WeaponNoDistractions.selected(s.owner, s.stack)) && aimingInput(s)
```

Outer Aiming eligibility and `matching` continue to enforce owner/session/stack/level, camera, loadout, handling, reload and input boundaries. Use the existing `s.flinch.active()` boolean in `WeaponAiming.damaged` → `WeaponFlinchState.magnitude` **once**. The existing resistance multiplies remaining flinch by0.65; never add another0.65 multiplier or additive35% resistance. Existing `WeaponPerkHud.update` already reads `WeaponAiming.noDistractions`, so its earned flag follows automatically without a separate HUD timer.

Master confirmed `WeaponAiming.perksEdited(ItemStack)` will reset **only the flinch clock** of sessions whose `Session.stack == editedStack`. Call it **after the tag change on every real `WeaponPerks.select/clear` edit**, including edits to a different trait and edits that return to the original roll within one server tick. Do not call on successful no-op selection or pure inspection. Polling the selected roll each tick cannot observe edit-away-and-back between polls; a real mutation hook is required. Do not use `suspend` or `releasedAim` as the edit hook: those affect other ADS/tracking behavior. This hook is documented here and is not authored in the six owned files.

Keep existing release/stow/suspend/session replacement/death/disconnect/dimension cleanup. Same-tick ADS release uses the existing `releasedAim` reset; validated stow uses the existing original-stack reset. No local event, counter or new lifecycle state is added.

## Firing semantics and uncertainty

The locally re-read W85 raw Clarity snapshot is pinned to commit **039cfbc4732c33573568b28cc6335dd3332a9296**, SHA256 **881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384**, JSON pointer `/2866798147/descriptions/en`. Its exact text says: **"Grants 35% Flinch Resistance after 1 second of Aiming Down Sights (ADS) without firing. Remains active until you're no longer ADS."** It separately states that the timer starts when ADS input is pressed. This is existing community evidence re-read locally, not a new live Destiny measurement or a claim that an old snapshot proves all2026 internals unchanged.

This supports the existing Izanagi rule: firing after earning the buff retains it while ADS continues. A shot before earning it interrupts the quiet interval. Restarting that interval rather than pausing is an interpretation of "without firing"; exact Destiny reset-versus-pause internals are not directly specified. Dry fire/rejected trigger behavior, exact Destiny same-tick proc/shot ordering, and independent reload/handling exceptions remain unresolved. DDC specifies the activation condition but does not separately spell out earned-buff firing retention; the Clarity text supplies that evidence. No certainty is inferred from absent wording.

Preserve `WeaponRuntime`'s accepted paid shot → `WeaponAiming.shot` path. Aiming calls `updateNoDistractions` before `s.flinch.shot(now)`, which restarts only unearned windup; an already earned flag survives. At the threshold the existing local order earns before processing the shot. Twenty elapsed server ticks at20TPS converts one second; it is not an independently measured Destiny tick boundary. Reload/handling suspension ends the local ADS interval; held crouch is not proof of uninterrupted ADS. Existing authored camera magnitude and stability interpolation remain local policies, with no new Destiny angle/curve claim.

## Reproduction and validation

Run in the assigned dirty-snapshot worktree:

```text
rtk proxy python3 scripts/build_no_distractions_w194.py --root /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w194-no-distractions
rtk proxy python3 scripts/build_no_distractions_w194.py --root /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w194-no-distractions --verify
rtk proxy env JAVA_HOME=/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home ./gradlew compileJava -Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w194-no-distractions/libs/gcb-server --console=plain --no-daemon --max-workers=2
```

The generator writes only the owned resource and provenance JSON. `--verify` compares their exact bytes and writes nothing; source drift fails before generation. Its reviewed application-source hashes describe the local snapshot, so integrated shared source changes require deliberate regeneration/review rather than treating this snapshot as a constraint on master.

Source/path review covers canonical item identity (`WeaponItems` → `WeaponModels` → `WeaponCatalog`), `WeaponCharacteristics`, `WeaponLoadout.canUse`, strict `WeaponPerks.selected/select/clear`, `WeaponAiming` input/flinch/damage/shot/release/stow paths, `WeaponRuntime` accepted paid shot callbacks and the existing `WeaponPerkHud` earned query. Deterministic generation/verification passed. Isolated Java25 `compileJava` passed with all three main/GCB/minigame compile tasks executed; only existing deprecation warnings were reported. The final helper edit after compilation only names the agreed master hook in a comment and changes no executable code.

Only six assigned files are authored: `NoDistractionsProfile.java`, `WeaponNoDistractions.java`, `scripts/build_no_distractions_w194.py`, `src/main/resources/destiny/weapons/w194-no-distractions.json`, this `SOURCE.md`, and `source.json`. Existing dirty/untracked files and sealed QA are preserved. No commit/stash/reset/clean/push or child workers. No shared registry/Runtime/Aiming/Handling edits. Animation research/extraction/implementation remains paused until the user's Windows files.

No new numeric mirror tests, gameplay tests, fullgate or Vision were run in this batch. Master owns the scoped GameTest for exact base ADS activation and edit-away/back/release, integration and any server validation. These pending integration checks are not claimed as passed here.
