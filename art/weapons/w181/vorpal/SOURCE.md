# W181 Vorpal Weapon

Base trait `1546637391` (Vorpal Weapon). Enhanced `3418165135` is excluded.
Only the current catalog intersection with official nonfake randomized trait pools and
`currentlyCanRoll: true` is admitted: 16 exact socket-4 rows across the selected 65 weapons.
Reusable-only, fake, nontrait, unavailable, exotic, enhanced, wrong-item and wrong-pool
references cannot grant a trait. Creating a weapon does not select Vorpal.

## Pinned source evidence

- Bungie manifest: <https://www.bungie.net/Platform/Destiny2/Manifest/>.
  Version `245114.26.10.13.2000-1-bnet.66137`, English inventory/plug-set component
  suffix `e677f6ea-2a1e-48d4-a8c8-700a39a62585`.
- Official definition: <https://www.light.gg/db/items/1546637391/vorpal-weapon/>.
  Bungie description: “Increased damage against bosses, vehicles, and Guardians with
  their Super active.” This link is a reference; generation uses the pinned official cache.
- Clarity: <https://github.com/Clarity-Destiny/Descriptions>.
  The exact base record is retained in `clarity-source.json`, including `lastUpload`.
  It specifies minibosses, bosses, vehicles, and players in Super. PvE increases are
  PRIMARY 20%, SPECIAL 15%, HEAVY/Power 10%; these mean 1.20, 1.15, 1.10 damage
  multipliers. Clarity's separate PvP values are retained as evidence, not implemented.
- `manifest.json` records full-input SHA-256 pins, byte counts and filtered output hashes.
  `official-sockets.json` retains only the two trait definitions' relevant fields, exact16
  proofs, all65 filtered socket scans, and excluded matching references. No entire cache
  or video is shipped. No unpinned later sandbox refresh is claimed.

## Catalog and paid modes

| Ammo | Multiplier | Exact IDs |
| --- | --- | --- |
| PRIMARY | 1.20 | seventh_seraph_officer_revolver, steelfeather_repeater, patron_of_lost_causes, aishas_embrace, farewell, whispering_slab |
| SPECIAL | 1.15 | bite_of_the_fox, first_in_last_out, hollow_words, nezarec_s_whisper |
| HEAVY | 1.10 | stormchaser, canis_major, dimensional_hypotrochoid, retrofit_escapade, crown_splitter, temptation_s_hook |

Normal paid weapon emissions, bow release, fusion bursts, glaive projectile and paid
sword contacts/projectiles use the source's ammo scalar. Direct/splash/wave targets must
each be checked independently. Abilities and glaive melee pass `Token.NONE`; no free attack,
HUD inspection, selection or hit can mint a paid emission. There is no base weapon-class
exclusion in the pinned Clarity record; this does not make glaive melee weapon damage.

## Local target mapping and lifetime

At impact, an alive, present, nonspectator native `WitherBoss`/`EnderDragon` qualifies, or a
`Mob` carrying the exact entity tag `destiny_boss` or `destiny_vehicle`. The `destiny_boss`
tag is the explicit custom miniboss/boss classification; no HP, display-name or boss-bar
heuristic applies. Players, armor stands, dead/removed and other nonmob living targets
are excluded even when tagged. Project combat already excludes players, so original PvP
Super eligibility/percentages are not implemented. Nonliving vehicles are outside scope.
The caller still owns ordinary combat hostility/damage eligibility.

At paid emission, `WeaponVorpal.capture(ServerPlayer)` requires the current genuine
selected weapon, an exact base allowlisted socket, canonical catalog entry, owned mainhand
stack and valid equipped slot when loadouts are enabled, plus alive/present/nonspectator/
connected/not-Super source authority. Standalone mode follows existing loadout policy.
The private token holds immutable catalog entry, roll, and ammo scalar values only.
Already-launched paid snapshots survive stow/edit; later unselected sources receive NONE.
Target checks produce no fresh source credit. No stacks, timers, sessions, cleanup hooks,
active buff countdown, stat bonus or fake HUD timer are introduced.

## API and verification

`VorpalProfile.ID`, `HASH`, `rolls()`, `supports(entry)`, `multiplier(entry)`;
`WeaponVorpal.Token.NONE`, `WeaponVorpal.capture(ServerPlayer)`,
`token.multiplier(LivingEntity)`, and null-safe `WeaponVorpal.multiplier(token, target)`.
Unsupported profile scalar requests throw `IllegalArgumentException`; invalid capture is NONE.
Master owns shared selection/commands, outgoing DamageTraits, per-target damage, and actualGT.

Reproduce offline using `rtk proxy python3 scripts/build_vorpal_profile_w181.py --verify --self-test`.
Default caches match W178: `/tmp/destiny-weapons-w30/bungie-items.json`,
`/tmp/destiny-weapons-w60/bungie-plugsets.json`, `/tmp/destiny-weapons-w60/manifest.json`,
`/private/tmp/w167-clarity.json`. Every input is pinned before use.
JUnit `VorpalW181Test` exercises the production strict profile/catalog; `WeaponVorpalW181Test`
exercises production immutable source snapshots and explicitly static mapping/authority checks.
The pure target-scalar boundary is not proof of actual Minecraft entity or damage behavior.
Native pending cases are enumerated in `manifest.json`; test logs/failures belong outside
source in `/private/tmp/w181-vorpal-report`. No game/server or shared gate is launched here.
