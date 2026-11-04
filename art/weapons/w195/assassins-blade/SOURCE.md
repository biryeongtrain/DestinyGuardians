# W195 Assassin's Blade

Base Trait 354401740 only; enhanced 3678483220 excluded; no default selected trait.
DDC Weapon Perks row 21; source.json preserves the exact raw HTML row including
all yellow enhanced spans. HTML SHA256:
8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437.
All 65 canonical catalog entries scanned, including exotic exclusions, against the
pinned official manifest. Only real randomized plugsets (isFakePlugSet=false),
currentlyCanRoll=true and exact base Trait qualify. Exact tuples:
[
  {
    "id": "abide_the_return",
    "hash": 1644160541,
    "socket": 3,
    "perkHash": 354401740,
    "plugSetHash": 211008653
  },
  {
    "id": "abide_the_return",
    "hash": 1644160541,
    "socket": 4,
    "perkHash": 354401740,
    "plugSetHash": 2761485963
  },
  {
    "id": "goldtusk",
    "hash": 3371413057,
    "socket": 3,
    "perkHash": 354401740,
    "plugSetHash": 1162279549
  }
]
Source input hashes, complete definitions, scan and pool proofs are in source.json.
Regenerate with scripts/build_assassins_blade_w195.py --root <worktree>; --verify is read-only.

Confirmed base: actual sword weapon final blow grants +15% damage and maximizes
Movement Speed for five seconds (100 Minecraft ticks); further actual kills refresh.
Buff persists while stowed. Enhanced 5.5-second duration is excluded.
The exact Destiny movement algorithm is UNKNOWN; this helper returns only a
source-backed active flag. Master owns a provisional native Minecraft locomotion
mapping. Do not invent a Mobility stat, movement percentage or attribute write here.

Settled integration API (master owns all shared integration):
- Register AssassinsBladeProfile.ID/HASH/rolls. Abide has TWO legal source tuples;
  preserve either exact selected tuple, plus Goldtusk socket3. No arbitrary name hash.
- capture(p) AFTER actual paid nonempty sword acceptance and BEFORE own damage/kill.
  Carry the SAME opaque Token to direct/cleave/splash. Never recapture on explosion.
- multiplier(p, token) is pure pre-own-kill damage; it only benefits the original
  accepted original selected source sword, including its paid in-flight caster shot
  after ordinary stow. A later alternate weapon never gains damage.
- killed(p, token, target) AFTER positive actual HP/absorption loss AND attributable
  eligible enemy final blow. Generic deaths/abilities/empty swords never call it.
  One corpse counts once per paid token, with a 256-target never-evicting bound.
- remaining(p) returns maximum unexpired ticks across all still owned canonical
  sources including stowed swords; active(p) == remaining(p)>0 for movement only.
- update(p) retains ordinary stow. Optional stowing(p, outgoing) retains buff while
  blocking transient outgoing damage evaluation before vanilla changes selection.
- edited(stack)/changed(p,stack) revoke same-tick tokens and that source buff,
  including while stowed. Removed/noncanonical/count!=1 sources are inert immediately.
- cleanup(p)/clear() revoke lifecycle; old ServerPlayer cleanup cannot remove a
  successor. Identity/level/data/runtime/class/Super/loadout checks are pure.
