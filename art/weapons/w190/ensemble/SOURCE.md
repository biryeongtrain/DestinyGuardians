# W190 Ensemble

Base hash **2621346526** only; enhanced hash **2495011826** excluded. User DDC,
Weapon Perks tab `gid=1662574278`, row **86**, retrieved 2026-10-27 from
`/private/tmp/destiny-w190/ddc-perks.html`: an ally within **15 metres** grants
**+30 Handling, +40 Reload Speed**. It lingers **1.5 seconds**, exactly **30 ticks
at 20 TPS**, from the first observation that the ally condition is lost.
The enhanced +35/+45 text in that row is not applied. The row does not distinguish
PvE/PvP; this implementation uses the repository's PvE player policy.

Official inventory and plug-set caches are from manifest
`245114.26.10.13.2000-1-bnet.66137`. The complete selected 65-weapon scan finds
exactly one base roll: `canis_major`, weapon hash **2066434718**, socket **3**,
randomized plug set **4037911937**, `currentlyCanRoll=true`, real trait pool.
This same socket contains Surplus **3436462433**. Socket **4**, plug set
**2791121719**, contains Rampage, Kill Clip, Vorpal, Adagio, Chain Reaction and
Unrelenting; it contains neither Ensemble nor Surplus. Thus there is **no legal
Ensemble + Surplus pair**, and no ability-charge bonus to combine. Current
implemented distinct companions are Kill Clip, Rampage and Vorpal; none changes
handling/reload stats or duration scalars. The outer Ensemble wrappers therefore
recompute raw totals using Ensemble's own bonus, and return prior values unchanged
when Ensemble is inactive. No old Surplus companion-list change is needed.

`source.json` preserves input SHA-256 pins, the DDC row, both complete socket/plug-set
proofs, the 65-weapon scan, companion acceptance/rejection, and the resource hash.
`scripts/build_ensemble_w190.py` writes only the owned resource and `source.json`;
`--verify` reproduces both without writing. The raw reload/ready/stow/ADS curves
are copied from pinned `w183-surplus.json`, originating in the historical
D2Foundry oracle `dcd0c7d302b056ffbb532edcb711d724a17ca8c1`. They are not current
Destiny engine timing measurements. Bonuses are added to base stats and capped at
100 before evaluating raw seconds; exactly one `ceil(seconds * 20)` follows.
Stow retains the existing raw stat-100 floor, ADS the existing 2..20 tick clamp.
Reload acceptance returns a fixed whole-magazine Plan.

Local geometry maps one Minecraft block to one metre, uses inclusive Euclidean
foot-point distance without LOS, and inspects only this level's loaded players.
An ally is another alive, connected, non-spectator ServerPlayer in the same level,
with both players unteamed or vanilla `isAlliedTo` true. Opposing/one-sided teams,
self, pets, mobs and armor stands do not count. The owner additionally requires
existing GuardianData, an active class and existing GuardianRuntime, with no super.
Queries create no attachments/runtime and never scan or refresh the cycle.

## Shared integration owned by master

These files deliberately do not edit shared integration. Add the following calls:

1. **WeaponPerks:** route `EnsembleProfile.ID` to `EnsembleProfile.rolls()` in
   `available`, add the ID to `ids`, name it `Ensemble`, and invoke
   `WeaponEnsemble.edited(stack)` after actual `select`/`clear` mutations. In
   command mutation hooks add `WeaponEnsemble.changed(p, stack)`.
2. **Observation:** `WeaponEnsemble.update(p)` in player tick and both runtime
   refresh paths, before Aiming calculations, and immediately before accepted
   reload planning. It resamples even within the same tick. Do not call it from
   HUD/status getters. Diagnostics can use `active(p)`, `remaining(p)`,
   `handlingBonus(p)` and `reloadBonus(p)` (all pure). Remaining reports available
   linger while near an ally, not an artificial running countdown.
3. **Handling:** wrap the complete existing duration result with
   `WeaponEnsemble.handlingTicks(p, stack, ready, previousTicks)`. At an actual
   selection, first `WeaponEnsemble.update(p)` while the outgoing object is held;
   compute outgoing stow; then call `WeaponEnsemble.selecting(p, desired)` before
   computing incoming ready. This must be inside `WeaponHandling.select`, after
   its `s.stack == desired` early return, so native selection and command/inventory
   selection both work. Do not call `update` between `selecting` and ready
   calculation: update intentionally retires nonheld sessions. The incoming
   preparation permits only that actual equipped object, source slot, owner,
   level, runtime/class and same-tick selection transaction. It inherits no
   outgoing linger.
4. **Aiming:** after explicit update, wrap both final transition results with
   `WeaponEnsemble.adsTicks(p, motionEntry, previousTicks, entering)` using
   `true` on entry and `false` on exit. No Snapshot pair is permitted here.
5. **Reload:** after explicit update and all existing plan wrappers, including
   Compulsive if integrated, use
   `plan = WeaponEnsemble.plan(player, entry, plan);` at acceptance. Do not invoke
   it to retime an already accepted reload. There is no legal Compulsive or
   Surplus stat pair in this exact Canis Major pool.
6. **Revocation:** `WeaponEnsemble.stowing(p, outgoing)` after outgoing stow
   duration is captured (the existing `selectedSlotChanging` hook after
   `WeaponHandling.selecting` is suitable), and at inventory stow/removal;
   `changed(p, stack)` on drop/loadout removal/replacement;
   `cleanup(p)` on disconnect/death/dimension/class/runtime/super transitions;
   `clear()` at global shutdown. Generic `cancelUseForSkill` is also used by an
   ordinary weapon swap: do not clear the freshly prepared incoming session
   there. Use the actual super/class lifecycle boundary instead. Validity checks
   immediately suppress a mismatched owner/level/runtime/class/stack without
   relying on the next tick. Mutation hooks prevent same-tick away-and-back or
   clear/reselect resurrection.

## Verification

- Generator regeneration and read-only `--verify`: passed.
- Pure `EnsembleCycle` and `EnsembleCycleW190Test` compiled with JDK 25 into a
  temporary isolated directory and ran using cached JUnit 5.11.4: **4 passed**.
  Tests cover loss-observation deadlines, pure queries/absent samples,
  reacquisition, same-tick loss, invalidation/clear and clock rewind.
- No numeric perk-mirroring tests, Gradle/full gate, native/game/CU QA, animations
  or models. Full mod compilation and shared integration remain with master.
