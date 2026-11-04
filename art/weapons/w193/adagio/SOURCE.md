# W193 Adagio

Base Adagio 3673922083 only, DDC Weapon Perks row **7**, read 2026-10-27.
Pinned HTML SHA256: `8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437`.
The exact named row says weapon kill: damage +30% (+27% Hand Cannons), Range +10,
fire recovery/charge/draw delay x1.2 for base 7 seconds; removed on stow.
Enhanced 2889515627 and yellow 8 seconds are excluded. No PvE/PvP split in this row.
The exact eligible pool contains no Hand Cannon, bow or charge weapon.
7 seconds at 20 TPS = 140 ticks, exact deadline exclusive; eligible kills refresh.

## Exact official pool and range

Catalog 65 scan: only Aisha's Embrace 2638190703 / socket 4 / plugset 4211351701 and
Canis Major 2066434718 / socket 4 / plugset 2791121719. Both real randomized Trait pools,
currentlyCanRoll=true, base Trait only. source.json records all 65 results, official
socket/category/plugset evidence, manifest components/version and input SHA256s.

Aisha: base Range 34; raw hip start 30.25 + .1568*Range, end 60.75, floor .5.
Canis: Range stat absent (JSON null), zero range slopes, existing sentinel falloff
999/999.9, floor .999. Its +10 Range must not invent travel distance, velocity or blast radius.
Add legal range bonuses before one 0..100 stat clamp and raw hip curve, then apply ADS.
AdagioProfile.rangeCurve(entry) exposes the sourced curves for master composition.

## Settled master integration

- Register AdagioProfile.ID/HASH/rolls with the shared trait registry.
- WeaponAdagio.firingProfile(p, entry, base) is a PURE cadence-only snapshot.
  Call on raw/unmodified Adagio cadence ONCE before WeaponCycle.fire; retain the
  returned profile through that paid firing decision. cadenceTicks*=1.2 and
  intervalTicks=ceil(cadenceTicks); ALL other fields, including RAW damage, stay intact.
  A kill/expiry/stow must never recompute an already accepted readyAt deadline.
  No charge/bow API exists because neither eligible weapon uses it.
- WeaponAdagio.capture(p) AFTER successful payment and BEFORE any damage/kill callback.
  Add the Token to DamageTraits; reuse the SAME token for direct and projectile splash.
  WeaponAdagio.multiplier(p, token) is a PURE validated immutable pre-kill snapshot.
  Master multiplyDamageTraits applies this scalar exactly ONCE to both direct and splash;
  do not also boost profile.damage. An emission that earns the first kill stays 1.0
  through its other splash contacts; an emission captured while active stays 1.3 after
  natural expiry/stow, while its original source remains valid.
- WeaponAdagio.killed(p, token, target) only AFTER positive actual HP/absorption loss
  and an attributable eligible enemy final blow. No ability/melee/unpaid proc.
  Tokens/corpses are per emission; distinct corpses can refresh, duplicates cannot.
  A stowed final blow consumes dedup credit without banking a re-equip buff.
- Pure remaining(p)/rangeBonus(p) read only the exact held valid source. No attachment
  creation, session binding, mutation, expiration or refresh in these queries.
- update(p) in server tick/lifecycle writer; stowing(p, outgoing) on accepted outgoing
  selection BEFORE vanilla changes slots, including same-tick away/back. Accepted stow
  clears live benefits immediately and suppresses them through that tick, but retains
  paid tokens. Do not use changed/cleanup for ordinary stow.
- edited(stack) on ANY trait edit/clear; changed(p, originalStack) on source removal,
  replacement/move; cleanup(p) on death/disconnect/respawn/dimension/class/super;
  clear() on shutdown. These revoke old tokens. Slot/loadout-mode changes also fail closed.
  Old-player callbacks cannot clear the replacement player's sessions.

## Local policies and checks

The 256-corpse-per-emission cap fails closed without eviction; this is a local policy,
not a DDC value. Immutable multiplier survives duration expiry; source/epoch validity
still applies. Explicit lifecycle/edit hooks are required for changes that go away
and back between observations. Original exact stack/count 1, canonical entry, exact
base roll, owner object, level/data/runtime/class and hotbar slot are revalidated.

Regenerate: `rtk proxy python3 scripts/build_adagio_w193.py`; add `--verify` for byte comparison.
Generator writes only the assigned resource, SOURCE.md and source.json.
Targeted AdagioCycleW193Test covers pre-kill paid snapshots, delayed direct/splash,
expiry/refresh/stow, dedup/saturation, pure queries, invalid epochs/time and fixed
WeaponCycle deadlines. No mirror tests for numeric values. Shared runtime, registry,
ammo economy, HUD and server/client integration are master-owned and unverified here.
No full gates, Vision, native input or animation work.
