# W195 Whirlwind Blade

DDC Weapon Perks row 248; raw row and yellow enhanced markup retained in source.json.
Confirmed base DDC: powered sword positive-loss contacts add stacks, 3% each up to ten, 3.5 seconds = 70 ticks; refresh on additional contacts. Actual blocking/stow resets live stacks. Paid snapshot remains fixed; source lifecycle revokes it.

All 65 canonical entries scanned against pinned official inventory and actual randomized
plug sets. Require isFakePlugSet=false, currentlyCanRoll=true, exact base Trait.
Runtime tuples are unique; raw matching pool entries remain in socketProofs.
Enhanced/exotic unsupported; no default selections. No shared integration files owned.

Integration:
- Register WhirlwindBladeProfile in master-owned WeaponPerks; no trait selected by default.
- WeaponWhirlwindBlade.update(p) on server tick. EnGarde.update also BEFORE swordAttack,
  after the actual held source can be observed and WeaponHandling.blocked is false.
- capture(p) only AFTER payment for nonempty powered sword contact, BEFORE damage.
  One exact Token across cleave/direct/splash; never fresh capture at explosion.
- multiplier(p, token) is pure and frozen; remaining(p) is pure.
- Whirlwind additionally stacks(p), confirmed(p,token,target,actualLoss) AFTER actual
  positive damage, blocking(p,stack) only when actual guard becomes active.
- stowing(p,outgoing) BEFORE selection changes, including same-tick away/back.
- edited(stack)/changed(p,stack) revoke same-tick old tokens. For EnGarde,
  source edits retain incoming readiness consumption and cannot rearm.
- cleanup(p) for lifecycle; clear() on server stop. Old-owner cleanup cannot remove successor.
- master excludes empty sword/glaive contacts, validates attributable enemy targets,
  and owns shared Runtime/Handling/registry/damage integration.

Only focused pure cycle tests and standalone compile are in scope. No native/server QA,
no broad gate, no numeric mirror tests, no model/animation work.
