# W200 Unrelenting

Base Trait 3108830275 only; Enhanced Trait 855168139 excluded. No default selection.
DDC Weapon Perks row 241: weapon final blows within five seconds of each other add
34% rank-and-file, 100% elites/minibosses/bosses, 67% Guardians. Reaching 100 resets
progress, restores 65 HP and begins Health Regeneration. Enhanced 70 HP excluded.
The raw HTML row and full official base definition, manifest/input SHA256 pins,
65-entry catalog scan and 13 exact real currentlyCanRoll randomized socket proofs
are retained in source.json. Regenerate with scripts/build_unrelenting_w200.py;
--verify checks without writes. Source HTML SHA256:
8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437.

The user's saved DDC perk row/table supplies no defensible regeneration rate.
Destiny regeneration rate stays UNKNOWN. Explicit local Minecraft mapping:
65/200 * maxHealth instant healing (.325; 6.5 at native 20 maximum health), then
1% maxHealth each server tick (20%/second). No separate shield, absorption grant,
vanilla potion, potion removal, duration timer or invented five-second expiry.
Regeneration ends at full HP, positive actual damage or source/owner invalidation.
Normal original-source stow retains paid in-flight authority and regeneration,
matching WeaponEnergyPerks/AssassinsBlade ownership policy; no transfer to a copy.

Local target mapping follows explicit product tags, never HP/name heuristics:
Player -> Guardian; WitherBoss/EnderDragon or Mob with destiny_boss or
destiny_vehicle -> powerful; other Mob -> rank-and-file.
Armor stands/non-Mob decorative entities excluded. Product PvP filtering remains
in the actual caller; this helper does not authorize otherwise forbidden PvP.

Integration (shared files owned by master):
- Register UnrelentingProfile.ID/HASH/rolls with WeaponPerks; exact 13 tuples only.
- WeaponUnrelenting.capture(p) AFTER paid ranged/charged/projectile/sword emission,
  BEFORE own damage. Carry SAME Token through direct/payload/cleave callbacks.
- killed(p,token,target) ONLY after positive actual HP/absorption loss and an
  attributable eligible enemy final blow. Never ability/ambient/dry-fire/glaive melee.
- update(p) once per server tick, even with source stowed. active(p) is a pure
  own-regeneration HUD observer; does not bind, heal or inspect vanilla potions.
- damaged(p,actualLoss) AFTER actual positive HP/absorption loss, never attempts.
- changed(p,stack)/edited(stack) revoke source epochs and regeneration immediately;
  ordinary held-slot switch MUST NOT call changed. cleanup(p)/clear() on lifecycle.
- Register UnrelentingW200GameTests in existing GameTest entrypoint.
