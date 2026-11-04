# W194 Killing Tally

Base Trait 557221067 only. DDC Weapon Perks row 134, exact td name Killing Tally.
Pinned HTML SHA256: 8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437.
source.json retains the complete rawHTML row, including yellow enhanced-only +10 Magazine.
Base: actual weapon final blows grant up to three stacks; PvE +10/20/30%, PvP +5/10/15%.
Stow or reload removes stacks. No duration or invented remaining timer. Enhanced
2896748467 and older Trait 2782457288 are excluded. No default selected trait.

All 65 canonical entries scanned against Bungie manifest 245114.26.10.13.2000-1-bnet.66137:
only Fixed Odds 2194955522 / socket4 / real randomized plugset1686775256,
currentlyCanRoll=true and exact itemTypeDisplayName Trait. Full scan, pool proofs,
official definition and input hashes are in source.json.

## Reset research and local policy

DDC establishes stow/reload reset, without specifying refill mechanisms or reset timing.
First-hand community tests report Marksman Dodge clears Killing Tally, while
Demolitionist refreshes the magazine without resetting it:
https://www.reddit.com/r/DestinyTheGame/comments/1q8bcz1/a_very_brief_breakdown_of_all_the_ways_to_reload/
Additional first-hand discussion:
https://www.reddit.com/r/DestinyTheGame/comments/186qfne/
These are community observations, not an exhaustive official current refill matrix.
Bungie's generic perk description does not settle these exceptions. No Destiny
runtime measurement was performed here.

Local explicit policy: accepted manual reload resets immediately at acceptance, even
if later cancelled. Positive actual Marksman ammo refill resets; a no-credit Dodge
does not call the hook. Demolitionist, Subsistence, Overflow and other reserve-only
magazine credits do not call reloadStarted. Holster itself has no reload proc;
the earlier stow already cleared stacks. Fixed Odds cannot co-select Demolitionist,
Holster or Overflow in its actual pinned socket pool. Do not broaden its rolls.

## Settled integration API

- Register KillingTallyProfile.ID/HASH/rolls in master WeaponPerks; no default/enhanced.
- capture(p) returns WeaponKillingTally.Token AFTER successful ammo payment and BEFORE
  any own direct/splash damage/final-blow callback. Share ONE token per emission.
- multiplier(p, token, target) is a pure immutable pre-kill stack snapshot:
  ServerPlayer targets use PvP, other LivingEntity targets PvE. Master applies once
  in DamageTraits, never also in the firing profile. Ordinary stow/reload clears
  live stacks but paid scalars survive; lifecycle/source edits revoke the token.
- killed(p, token, target) only AFTER positive actual HP/absorption loss AND a confirmed
  attributable eligible enemy final blow. No ability/melee/unpaid callbacks.
  Live stacks cap at three; the killing emission retains its pre-own-kill scalar.
- stacks(p) is a pure held-source probe, no binding/update/attachment creation.
- reloadStarted(p, stack) at accepted manual reload, and positive Marksman credit only.
- update(p) in server tick; stowing(p, outgoing) at accepted selection BEFORE vanilla
  changes slots, including same-tick away/back. Delayed pre-reset final blows consume
  dedup credit but cannot re-bank live stacks after reset (explicit local policy).
- edited(stack) on every successful selection edit/clear including away/back;
  changed(p, originalStack) for loss/replacement/move; cleanup(p) on death/disconnect,
  respawn, dimension/class/super changes; clear() at shutdown. These revoke source epochs.
  Ordinary stow must use stowing, not changed/cleanup. Old-player cleanup cannot
  clear replacement-player state. Exact stack/count1, hotbar slot, loadout mode,
  canonical entry/roll, owner object, level, GuardianData/runtime/class are revalidated.

Corpse identity ledger is capped at256 per paid emission; at saturation it fails
closed without eviction. Caller owns actual-damage/enemy/final-blow attribution across
different emissions. Local bounds are not DDC values. No shared ammo mutation.

Regenerate: rtk proxy python3 scripts/build_killing_tally_w194.py
Verify: same command with --verify (byte-identical resource, source.json, SOURCE.md).
Focused cycle tests cover event ordering, cap, dedup, pure probes, reset vs revocation,
foreign epochs and rollback. No numeric mirror tests, fullgate, Vision or animation work.
Master owns registry, DamageTraits, lifecycle wiring and scoped server integration tests.
