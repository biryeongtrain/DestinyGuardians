# W195 En Garde

DDC Weapon Perks row 82; raw row and yellow enhanced markup retained in source.json.
Confirmed base DDC: 30% for 1.5 seconds = 30 ticks on actual sword ready. DDC enhanced duration is 2? and cooldown after removal is 2? seconds, both UNKNOWN. Local provisional cooldown is 40 ticks after buff removal; NOT a confirmed DDC value. Pinned official Trait definition supplies only generic description, no resolved cooldown.

All 65 canonical entries scanned against pinned official inventory and actual randomized
plug sets. Require isFakePlugSet=false, currentlyCanRoll=true, exact base Trait.
Runtime tuples are unique; raw matching pool entries remain in socketProofs.
Enhanced/exotic unsupported; no default selections. No shared integration files owned.

Integration:
- Register EnGardeProfile in master-owned WeaponPerks; no trait selected by default.
- WeaponEnGarde.update(p) on server tick. EnGarde.update also BEFORE swordAttack,
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
