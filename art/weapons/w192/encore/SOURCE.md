# W192 Encore

Base Encore only, DDC Weapon Perks row **83**, read 2026-10-27. The pinned HTML SHA256 is
`8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437`.
Exact row-name selection excludes other rows; enhanced hash 838873202 and yellow 7.5-second duration are excluded.

Each paid weapon kill grants +1 stack, or +2 total on a precision kill, cap 4.
Each stack gives +5 Range, +8 Stability and -1.25% Accuracy Cone Size
(`1 - .0125 * stacks`, cap scalar .95). All further kills refresh the complete
7-second window (140 ticks at 20 TPS). The exact deadline expires. Stow preserves the running window.
These source values have no PvE/PvP split in this row. No handling/reload changes.

Only Fixed Odds 2194955522, trait socket 3, randomized plugset 4227334000,
base Encore 1195158366 is eligible among the 65 catalog weapons. `source.json`
records the full scan, official socket category/entry/currentlyCanRoll proof,
manifest version/components, base Trait definition and input hashes.

Regenerate: `rtk proxy python3 scripts/build_encore_w192.py`; append `--verify` for byte comparison.
Generation writes only the assigned resource, source.json and this document.

## Master integration

- Register EncoreProfile.ID/HASH/rolls in the shared trait registry and display choices.
- Add WeaponEncore.Token to DamageTraits. Capture once after the emission pays its cartridge;
  carry the SAME token through every pellet/direct/payload callback. Melee/ability/unpaid paths use NONE.
- Call `WeaponEncore.killed(player, token, target, precision)` only AFTER positive actual
  HP/absorption loss and the attributable eligible enemy final blow. Splash passes false.
  Body kills grant 1; precision kills grant 2 total. Repeated corpse callbacks cannot refresh.
- Compose pure `stabilityBonus(player)` additively before the shared stat cap and
  `coneScalar(player)` multiplicatively with the existing cone scalar.
  Add `rangeBonus(player)` to legal other stat bonuses BEFORE one 0..100 range cap;
  use `EncoreProfile.rangeCurve(entry)` / the resource's raw Fixed Odds hip curve and apply ADS afterward.
  Base Range 63, Stability 28; raw start 28.5 + .0223*range, end 38.2, floor .5.
- Call `update(player)` from the server tick/lifecycle writer; `edited(stack)` on every
  trait edit/clear, `changed(player, originalStack)` on source removal/replacement,
  `cleanup(player)` on death/disconnect/respawn/dimension/class/super lifecycle, and `clear()` on shutdown.
  Ordinary stow is NOT changed/cleanup: an in-flight shot can credit its still-owned equipped original.
- Pure held-source `stacks`, `remaining`, `stabilityBonus`, `rangeBonus`, `coneScalar`
  never create attachments/sessions or refresh time. Stowed originals keep state;
  their benefits are visible again when held within the original deadline.

## Local policy and verification boundary

The 256-corpse bound per emission fails closed at saturation without eviction;
it is a local defensive policy, not a DDC number. Owner/data/runtime/class/level,
original inventory identity, exact selected roll and source epoch are required.
Tick rollback and explicit invalidation revoke old tokens permanently. No copied-source rebinding.
The master must dispatch same-tick lifecycle/edit changes; observations cannot detect an unreported away-and-back edit.
Focused Cycle tests cover stack transitions, deadlines, cap refresh, pure reads,
paid-emission dedup/bounds, source epochs and clock rollback. Shared runtime/registry
wiring, server lifecycle integration and real client behavior are master-owned and unverified here.
No Vision/native/animation or unrelated fullserver gates.
