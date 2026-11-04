# Impulse Amplifier — W193

Base Trait **951095735**, [DDC Weapon Perks row124](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278): **+20 Reload**, **0.85 duration**, with **0.8 duration for Rocket Launchers**. Rocket projectile speed is **1.10**. Enhanced `↑+25` / hash3878366039 is excluded. Pinned HTML SHA256: `8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437`.

The deterministic generator checks all **65** catalog entries (63 W30 entries plus both exotic supplements) against pinned official manifest `245114.26.10.13.2000-1-bnet.66137`. Exactly these base Trait tuples survive the official weapon-perk socket category, randomized set, `isFakePlugSet=false`, and `currentlyCanRoll=true` filters:

| Weapon | Weapon hash | Socket | Plug set |
| --- | --- | --- | --- |
| Canis Major | 2066434718 | 3 | 4037911937 |
| Code Duello | 2496242052 | 3 | 3719628667 |
| Nezarec's Whisper | 254636484 | 3 | 210449465 |

## Velocity research and limits

DDC enumerates rocket, support-auto and rocket-sidearm velocity bonuses. It omits concrete heavy-GL and glaive values. On 2026-10-27, indexed [light.gg base community research](https://www.light.gg/db/items/951095735/impulse-amplifier/?_=738), marked updated 2026-07-03, also enumerated those archetypes without a GL/glaive value. Direct page fetch returned HTTP402; the indexed research text was available through search. It does not resolve either missing number.

The [Bungie Weapons Team's Season 23 preview](https://www.bungie.net/7/en/News/Article/season-23-weapons-preview), dated 2023-10-25, describes faster **baseline** glaive projectiles. It provides no numerical current Impulse Amplifier scalar for either supported family. Historical community claims of universal 35% are insufficient to replace the current DDC omissions. Neither 1.35 nor a scalar inferred from baseline tuning is implemented.

For Canis Major and Nezarec's Whisper, the resource keeps `status=OMITTED_UNKNOWN` and `scalar=null`; `projectileSpeedScalar(entry)` returns `OptionalDouble.empty()`. `projectileVelocityStatus(entry)` exposes the uncertainty explicitly. The runtime helper **preserves incoming launch speed** for these two unresolved families. This is a conservative implementation limit, not a claim of zero original-game benefit. Their sourced reload bonuses are implemented independently. Unsupported families do not gain bonuses from the support-auto/rocket-sidearm numbers.

## Settled APIs and master integration

`ImpulseAmplifierProfile.ID`, `HASH`, `rolls()`, `supports(entry)` and `compatible(entry, perkId, selectedRoll)` expose the exact base pool. Add the ID/rolls/display name to shared `WeaponPerks.available`, `ids`, and `name`. Until registration, selection queries remain inert. Static initialization reads the owned resource and instantiates `WeaponPerks.Roll` values only; it calls no live catalog, characteristics, or perk registry.

`WeaponImpulseAmplifier.selected(player)` checks the actual main-hand inventory object, selected hotbar slot, count1, canonical entry, exact saved base roll, usable loadout, connected/alive/nonspectator owner and no active Super. Queries create no attachments, bind no session, advance no timer and retain no owner/stack references. All eligibility is read again from the current source. Existing Frenzy state is queried only for that original held object and its current owner/level.

`WeaponImpulseAmplifier.plan(player, entry, base)` must be the **outermost** wrapper, after `WeaponCompulsiveReloader.plan`, immediately before accepted `cycle.startReload`. It returns the incoming plan unchanged for invalid/foreign sources, incremental topology or an owned reload already in progress. Otherwise it computes total legal bonuses from the actual held stack and calls the raw profile once. Never apply another reload wrapper afterward or retime an accepted reload.

The complete official base-trait audit is in `source.json`. Code Duello can pair with Frenzy in socket4/set147528717; Nezarec's Whisper can pair with Frenzy in socket4/set699056095. When that exact selected partner is active, add Frenzy's +100 Reload before the clamp. Canis Major has no distinct reload partner. Ensemble/Surplus/Field Prep on Canis Major, Surplus/Field Prep on Code Duello, and Compulsive Reloader on Nezarec's Whisper compete for socket3. Stats for All, Threat Detector, Outlaw, Feeding Frenzy, Rapid Hit, Perpetual Motion and Elemental Capacitor provide no legal distinct pair here. Do not borrow effects from another weapon or from same-socket alternatives.

`ImpulseAmplifierProfile.reloadSeconds(entry, totalReloadBonus, totalScalar)` and `reloadPlan(entry, totalReloadBonus, totalScalar, base)` accept **totals including this perk**. The formula is `S = clamp(officialBaseReload + totalReloadBonus, 0, 100)`, then `seconds = (evpp*S*S + vpp*S + offset) * totalScalar`, then exactly one `ceil(seconds*20)`. W43 family/category selects the original raw W46 quadratic; existing rounded reload ticks are never divided or multiplied. All three are whole-magazine reloads; there is no shell/insert path. Curves are historical approximate community timings, not new current official Destiny measurements.

`WeaponImpulseAmplifier.projectileSpeed(player, entry, launchSpeed)` is pure and accepts the exact paid shot entry. Master samples it **once**, after the existing accepted `cycle.fire`/ammo save and before freezing `Shot.velocity`, after any existing launch-profile scaling. The reviewed projectile path is `WeaponRuntime.fire` → `emit` → `new Shot`; current `Shot` line165 already applies `WeaponRangefinder.projectileSpeed`. Compose there as `WeaponRangefinder.projectileSpeed(owner, entry, WeaponImpulseAmplifier.projectileSpeed(owner, entry, profile.speed()))`. Each helper independently verifies its selected exact roll; the present three Impulse Amplifier pools have no colegal Rangefinder pair. Preserve that distinct-socket restriction if pools change. Do not sample from flight ticks, impacts, bounces, tracking, hitscan or glaive melee. Earlier shots keep their launch velocity across swap, ADS release, roll edit, death and owner lifecycle changes. Nonpositive/nonfinite launch inputs pass through; multiplication overflow also preserves the input.

## Reproduction, paths and checks

Run from the isolated worktree:

```text
rtk proxy python3 scripts/build_impulse_amplifier_w193.py --root /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w193-impulse-amplifier
rtk proxy python3 scripts/build_impulse_amplifier_w193.py --root /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w193-impulse-amplifier --verify
rtk proxy env JAVA_HOME=/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home ./gradlew compileJava -Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w193-impulse-amplifier/libs/gcb-server --console=plain --no-daemon --max-workers=2
```

Passed: pinned source/row124 checks, exhaustive catalog65 exact socket scan, legal companion audit, raw W46 baseline/topology review, deterministic output comparison, and Java25 `compileJava` with isolated GCB/minigame sources. Compilation reported existing deprecation warnings only. Source/path review covered `WeaponPerks.selected`, `WeaponItems.entry`, `WeaponLoadout.canUse`, `Guardians.runtimeIfPresent`, `WeaponFrenzy.ownedRemaining`, and `WeaponRuntime.startReload/fire/emit/Shot/reloadOwnedBy`.

Only the six assigned paths are authored: `ImpulseAmplifierProfile.java`, `WeaponImpulseAmplifier.java`, `src/main/resources/destiny/weapons/w193-impulse-amplifier.json`, `scripts/build_impulse_amplifier_w193.py`, this document, and `source.json`. Generator writes only the two owned JSON outputs; `--verify` writes none. Input hashes, generator hash, resource hash, socket proofs and research decisions are in `source.json`.

This numeric-only change adds no mirror tests or new stateful logic. No targeted gameplay tests, full gates, Vision/native runs or animation work were performed. Registry/runtime/ammo/HUD integration and Ambitious Assassin/overflow foundations remain master-owned. Successful helper compilation does not claim that the copied shared runtime activates the feature.
