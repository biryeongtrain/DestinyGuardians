# W195 Dynamic Sway Reduction

Base Trait 1359896290 only; enhanced 3060983774 excluded; no default selected trait.
DDC Weapon Perks row 77; source.json preserves the exact raw HTML row including
all yellow enhanced spans. HTML SHA256:
8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437.
All 65 canonical catalog entries scanned, including exotic exclusions, against the
pinned official manifest. Only real randomized plugsets (isFakePlugSet=false),
currentlyCanRoll=true and exact base Trait qualify. Exact tuples:
[
  {
    "id": "ammit_ar2",
    "hash": 2119346509,
    "socket": 3,
    "perkHash": 1359896290,
    "plugSetHash": 1723759242
  },
  {
    "id": "hammerhead",
    "hash": 603242241,
    "socket": 3,
    "perkHash": 1359896290,
    "plugSetHash": 2515290473
  }
]
Source input hashes, complete definitions, scan and pool proofs are in source.json.
Regenerate with scripts/build_dynamic_sway_w195.py --root <worktree>; --verify is read-only.

Confirmed base: while continuously holding trigger, each paid shot adds +1 Stability
and subtracts 10% Accuracy Cone Growth, capped at +10 and -100% at ten shots.
The intermediate Accuracy Cone Size curve is `?` UNKNOWN. Preserve incoming cone
size (scalar 1) below ten shots; at maximum return 0 because the DDC explicitly
says all bullet spread is removed. Do not interpolate or invent a percentage.
This is a provisional Minecraft mapping of that explicit maximum wording.
No timer is invented. Enhanced eight-shot ramp/-12.5% growth are excluded.

Settled integration API (master owns all shared integration):
- Register DynamicSwayProfile.ID/HASH/rolls; both real socket3 tuples only.
- WeaponDynamicSway.paid(p, entry) AFTER actual payment, BEFORE trace/recoil.
  Only actual paid emissions call it; duplicate input/polling never does.
- stabilityBonus(p, token), accuracyScalar(p, token), growthScalar(p, token)
  are pure captured shot snapshots. stabilityBonus(p) is the pure live contribution
  for incoming flinch; stacks(p) is diagnostic. No writes in queries.
- released(p, stack) on actual held release, including State.releaseHold lease
  expiry, reload and cancel. Resets the chain and revokes its tokens immediately.
- stowing(p, outgoing) resets before vanilla slot selection; update(p) also drops
  unheld chains. changed/edited revoke same-tick tokens. cleanup/clear on lifecycle.
  Tokens require the original held canonical selected tuple throughout evaluation.
- No shared Aiming/Handling/Runtime/registry/HUD writes are included here.
