# W182 base High-Impact Reserves

Base2213355989 only. Enhanced2002547233 is excluded. Exact10 nonfake, currently-rollable
randomized trait sockets across pinned selected65. Bygones uses socket3; the other nine
use socket4. No exotic default, no family-wide grant. Master owns registry/runtime hooks.

## Evidence and current-formula uncertainty

Bungie manifest version245114.26.10.13.2000-1-bnet.66137, component suffix
e677f6ea-2a1e-48d4-a8c8-700a39a62585. Original caches and all catalog inputs have SHA256
pins in manifest.json. official-sockets.json contains base/enhanced definitions, exact10
proofs, all65 filtered scans and rejected matching references.

Pinned Clarity record lastUpload1743183422022 (2025-03-28), retained verbatim in
clarity-source.json, gives normal PvE12.1–25.6%, fusion/aggressive-LFR10.3–22.9%,
50% base magazine to empty, and excludes other perks' explosive/splash elements.
https://github.com/Clarity-Destiny/Descriptions
https://www.light.gg/db/items/2213355989/high-impact-reserves/

Current Data Compendium, Weapon Perks row119, retrieved2026-10-26T19:58:37Z:
https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1662574278
The row supplies50% base threshold and normal endpoints, additionally identifying maximum
at7.5% magazine. It contains no intermediate values, integer rounding or formula. Retained
filtered row and CSV SHA in clarity-source.json. Full CSV remains in external worker report.

Firsthand body-shot measurements by JadeRabbitEmperor, edited2019-11-18:
https://www.bungie.net/en/Forums/Post/254403883
The40-round Werewolf test has baseline473. Shot groups/damage:
1–19:473;20–21:530;22–26:531;27:541;28:542;29:543;30:544;31:555;
32:556;33:568;34:570;35:582;36–40:595. All twelve nonneutral measured
values and their positions are retained. The original page cache has a SHA pin.
These are dated community measurements, NOT official Bungie developer mechanics merely
because hosted on the Bungie forum. Small-mag sniper/fusion tests on the same page differ.

A second firsthand Palindrome10 table (2021-02-21) reports minimum/maximum plateaus and
intermediate15%/23%, supporting nonlinear quantization but no general current formula:
https://www.reddit.com/r/DestinyTheGame/comments/lpc5a9/

Rejected as exact-formula validation: Foundry oracle_engine commit
dcd0c7d302b056ffbb532edcb711d724a17ca8c1 (2026-05-20), year_1_perks.rs HIR block,
has curr_mag<=curr_mag/2, impossible at positive ammo, and lacks fusion endpoints.
https://github.com/d2foundry/oracle_engine/blob/dcd0c7d302b056ffbb532edcb711d724a17ca8c1/src/perks/year_1_perks.rs
Destiny2DPSGraphPY commit70252413562c66df886a7fffe79f67d8b48f1711 uses a linear
1.125/1.255 approximation and obsolete enhanced75%; it cannot establish exact fidelity.
The Damage Generator spreadsheet was retrieved but only supplied aggregate HIR1.16, not
a validated per-shot curve. No game/client/server was launched to invent a native table.

## Concrete measured-table adaptation

MAPPING=MEASURED_2019_40ROUND_QUANTIZED_ENDPOINT_NORMALIZATION_W182_NOT_CURRENT_EXACT_FORMULA.
This implementation does not claim an established current Destiny general integer formula.
It is a documented authored projection of measured discrete values, with endpoint normalization.

Require canonical catalog entry and baseCapacity=WeaponProfile.forEntry(entry).magazine,
with1<=roundsBefore<=baseCapacity. Reject arbitrary/overflow capacities and bad rounds.
For this paid cartridge, after=roundsBefore-1. If2*after>baseCapacity, scalar1.0.
Otherwise referenceAfter=ceil(40*after/baseCapacity), evaluated with integer arithmetic.
Read the measured40-round damage at this reference AFTER-shot index. Ceiling conservatively
retains the earlier higher-ammo sample until its rational boundary is crossed. No interpolation
between ammo rungs, no equal-step tier invention. Normalize measured DAMAGE difference:
minimumMultiplier+(measuredDamage-530)*(maximumMultiplier-minimumMultiplier)/65.
Normal endpoints1.121/1.256; fusion endpoints1.103/1.229.

roundsBefore1 means an actual final paid cartridge, after0, maximum. Argument0 cannot represent
a paid cartridge: profile throws IllegalArgumentException, runtime capture returnsToken.NONE.
For both even/odd capacities first affected pre-round count=floor(capacity/2)+1:
Officer11 pre7 neutral/pre6 minimum; Long Arm14 pre9 neutral/pre8 minimum.
This AFTER-shot threshold comes from the dated measured shot20/40 observation, which
already has a bonus with21 before firing and20 afterward. Passing true pre-rounds is still
mandatory: the profile subtracts exactly once; it never reads a later magazine.

Unresolved fidelity: dated40-round plateau starts at10% AFTER (12.5% BEFORE); current
Compendium instead says7.5%. Existing Clarity supplies only empty. Small-mag tests differ.
The normalization and projection onto other integer magazines, including reduced fusion,
are explicit local adaptations. They are not measured current values for each selected weapon.
This discrepancy remains an open source-fidelity issue for master, not a completed exactness claim.

## Public API and runtime contract

HighImpactReservesProfile.ID/HASH/rolls()/supports(entry);
public static float multiplier(WeaponCatalog.Entry entry,int roundsBefore,int baseCapacity).
The profile has no Minecraft entity/stack/runtime dependency. rolls() is immutable and schema
is bounded/strict: rejects unknown/missing/duplicate fields, wrong numeric types/fractions,
enhanced/forged/missing/duplicate sockets, altered endpoints/source/mapping.

WeaponHighImpactReserves.Token.NONE; public float Token.multiplier();
public static Token capture(ServerPlayer player,int roundsBefore,int baseCapacity).
Read-only current source authority matches Vorpal: genuine mainhand inventory object identity,
equipped identity if loadouts enabled, canUse, live/present/nonspectator/connected/notSuper,
exact selected base socket and canonical item entry. Caller must already have paid successfully.
Invalid selection/ammo/capacity returnsNONE. Frozen private immutable source entry/roll/pre-rounds/
base-capacity/scalar; no current ammo lookup at impact. Paid work persists after stow/edit/refund.
No timer, stacks, sessions, countdown HUD, tick or cleanup hooks.

Master captures after each successful paid emission, passing TRUE PRE-CONSUMPTION rounds.
Shared fusion/aggressive-LFR bolts retain one cartridge token. Ordinary pulse/sidearm burst
captures anew only per genuinely consumed bullet. Master injectsNONE for abilities, glaive
melee, Payload, Dragonfly and every perk-generated splash. No shared hooks edited here.

## Native choices and verification boundary

Officer: hash3037520408 socket4 pool3527094473, cap11 hitscan1bullet.
Bygones: hash2712244741 socket3 pool1760176771, cap38 ordinary3bullet burst.
Dream Breaker: hash2931957300 socket4 pool1206254527, cap6 shared7bolt fusion.
No eligible aggressive LFR or projectile in the pinned selected65; no such native claim.

Generator: rtk proxy python3 scripts/build_high_impact_reserves_profile_w182.py --verify --self-test
Full research defaults live under /private/tmp/w182-hir-report; override --compendium and
--measurements to archived files with matching pinned SHA. Other defaults reuse official W30,
W60 and W167 caches. Generation/verification is offline and only writes its four owned JSONs.
JUnit uses real pure product classes; source-authority inspections are explicitly static and
are not proof of native entity/payment behavior. Master owns shared selection/runtime
integration, actualGT, native pixels and audio. Logs/failures/native-pending remain external.
