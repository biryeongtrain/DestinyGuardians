# W194 Sympathetic Arsenal

Base Trait3350417888 only, DDC Weapon Perks row220, exact td name Sympathetic Arsenal.
Pinned HTML SHA256: 8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437.
source.json preserves rawHTML, including yellow enhanced unknown window (not adopted).
Base passive +20 Reload Speed; finishing a real reload within3.6 seconds of a
weapon kill refills stowed weapons. Enhanced1537607344 excluded; no default trait.

All65 canonical entries scanned; exact socket4 real randomized currentlyCanRoll=true
Trait pools: Cold Denial1216130969/720537379, Brass Attacks2121785039/3403850295,
Biting Winds1621657423/2763203653, Whispering Slab211938782/967526625,
Hollow Words607191995/1485010760. Source includes official pool evidence and hashes.

## Raw reload plan and exhaustive co-selection audit

plan(p, entry, base) goes OUTERMOST after other wrappers, immediately before reload
acceptance. Sum actual legal raw bonuses, clamp once to0..100 (bow cap85 from historical
W46), evaluate raw quadratic seconds, multiply legal duration scalars, then ceil(*20) once.
No ratios of already rounded plans; bow nock only, draw/charge/recovery unchanged.
Historical community curves are a local approximation, not newly measured Destiny timing.
The accepted plan stays fixed through later tier changes.

The complete WeaponPerks54 implementation inventory, including all five W193 traits,
is audited against every official base Trait on these weapons in source.json.
Legal reload-stat/scalar companions, all socket3:
Cold Denial: Feeding Frenzy, Threat Detector.
Brass Attacks: Feeding Frenzy, Rapid Hit, Threat Detector, Surplus.
Biting Winds: Rapid Hit, Surplus.
Whispering Slab: none. Hollow Words: Feeding Frenzy.
Exactly one socket3 choice can be selected; only the chosen active source contributes.
Raw tier bonuses/scalars are copied deterministically from pinned existing profile data,
not inferred from capped effective-stat deltas. Field Prep/Outlaw/PM/Frenzy/SFA/Elemental
Capacitor/Ensemble/Compulsive Reloader/Impulse Amplifier have no distinct legal pair.
Brass Attacks can pair W193 Overflow; it changes ammo, not reload duration.
W193 Ambitious Assassin, Clown Cartridge, Adagio and Impulse Amplifier have no distinct
legal pair. Same-socket Demolitionist, Multikill Clip, Frenzy, Backup Plan etc cannot stack.

## Settled master integration

- Register SympatheticArsenalProfile.ID/HASH/rolls; no default/enhanced.
- capture(p) returns WeaponSympatheticArsenal.PaidToken AFTER successful weapon payment,
  BEFORE own damage/kill. Retain the original source token and reuse for direct/splash.
- killed(p, paidToken, target) AFTER positive actual HP/absorption loss AND confirmed
  attributable enemy final blow; no ability/melee/unpaid callbacks. Distinct corpse
  identity ledger capped256 per emission, no eviction; duplicates cannot refresh.
- acceptedReload(p) returns WeaponSympatheticArsenal.ReloadToken only AFTER
  WeaponCycle.startReload succeeds, while WeaponRuntime.reloadOwnedBy(p, held) is true.
  This creates real reload authority, NEVER arbitrarily checks eligibility at start.
  Store alongside the accepted cycle. A kill during the reload may qualify.
- reloaded(p, reloadToken, creditedRounds) returns one boolean at the FIRST genuine
  positive ammo-credit boundary. Measure kill -> that boundary, inclusive <=72 ticks
  (3.6s at20TPS), even when credit precedes full reload recovery. Zero/negative/no-reserve
  credits do not trigger. Positive ineligible credit consumes authority too; no replay.
  Master computes genuine delta and invokes after saving ammo. Instant Marksman/
  Demolitionist/Holster/Overflow/refill paths cannot obtain this accepted reload token
  and MUST NOT call this API. Do not substitute a query or full recovery boundary.
- On true, master calls refillStowedArsenal(p) ONCE. Only stowed equipped canonical
  loadout stacks (or canonical standalone hotbar) qualify; skip held/source, Sword,
  and loaded Honed. Transfer actual finite reserves into missing magazine space,
  never conjure ammo or overflow normal capacity. No nested reload/kill-clip/SA procs.
  The helper returns boolean and deliberately performs no shared ammunition writes.
  Eligibility is spent even when no stowed target has available ammo/space.
- reloadCancelled(p, stack) on accepted reload cancellation/interruption/ability refill;
  a newer accepted reload replaces old authority. Store NONE after the credit decision.
- update(p), stowing(p, outgoing) on accepted selection BEFORE slot mutation;
  ordinary stow clears pending eligibility/reload authority but retains source epoch.
  Delayed pre-stow kills cannot bank eligibility after re-equip (local policy).
- edited(stack), changed(p, originalStack), cleanup(p), clear(): revoke tokens on every
  actual roll edit/source loss/owner lifecycle. Use cleanup on death/disconnect/respawn,
  dimension/class/super changes. Same-tick away/back needs explicit hooks.
  Owner object, level, GuardianData/runtime/class, exact stack/count1/hotbar slot,
  loadout-mode and canonical entry/roll are revalidated; no attachment creation by reads.

Regenerate: rtk proxy python3 scripts/build_sympathetic_arsenal_w194.py
Verify: same with --verify (deterministic resource + SOURCE.md + source.json).
Focused cycle tests cover before/during reload kills, inclusive72/expired73 boundary,
first real credit vs recovery, zero credit, replay, cancellation, stow/edit/foreign epochs,
bounded dedup and pure probes. Numeric +20 path receives source/application review only.
Master owns shared registry/runtime refill wiring and scoped server tests. No fullgate,
Vision, shared Aiming/Handling edits, sealed QA edits or animation research.
