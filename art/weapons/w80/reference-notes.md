# W80 — base Explosive Payload research

Research date: 2026-10-24. Scope: base trait **3038247973**, selected63 exact W30 catalog hashes only. Research artifacts only; no production, tests, config, build, client, app or commit work.

## Verified exact eligibility — ready for parent/tests

All indexes below are **zero based**. Socket 4 is the fourth perk column, not API index 3. All five randomized entries have `currentlyCanRoll: true`, are in trait category `4241085061`, and have `isFakePlugSet: false`.

| Selected weapon ID | Exact item hash | EP socket index | Randomized plug set |
|---|---:|---:|---:|
| distant_relation | 2034817450 | 4 | 3824767299 |
| patron_of_lost_causes | 2723241847 | 4 | 120674550 |
| long_arm | 8293111 | 4 | 619833418 |
| bite_of_the_fox | 1403800851 | 4 | 2442672691 |
| apostate | 2164448701 | 4 | 2826016044 |

**Coexistence:** only Distant Relation has base Auto-Loading Holster `3300816228`, socket **3**, randomized set `1131958073`. No base Rampage occurrence in either set field on any of the five eligible weapons. Distant Relation and Apostate additionally contain EP in socket 4 direct reusable entries; these are duplicate paths to the same sockets. Exact direct fields are preserved in the evidence JSON.

Evidence: [official-eligibility.json](references/official-eligibility.json) contains literal input SHA256 pins, complete matching raw socket entries, complete relevant raw plug sets, exact perk definitions, and a negative/positive audit for all 63 weapons. It scanned **678 sockets / 627 referenced plug-set fields** without a name/family prefilter, checking both randomized/reusable set fields and direct initial/reusable items. Selected hashes were independently matched against W30 catalog hashes. Official manifest version: `245114.26.10.13.2000-1-bnet.66137`.

## Verified mechanics and critical split — original source inspected

Original [Destiny Data Compendium, Weapon Perks](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit?gid=1662574278), Explosive Payload row 91 in formatted sheet HTML (row 90 in gviz CSV data). Read directly on the research date. Its actual wording includes:

> Weapons deal 50% of their Non-Precision Direct Impact Damage as an Explosive Payload.
> Explosive Payload detonates on impact, damaging enemies within 3 meters.
> Explosive Payload portion deals 30% increased [7% decreased on Hand Cannons] damage and inflicts increased stagger.
> Impact Damage's Precision Multiplier is increased to offset the Explosive Payload portion lacking the ability to score Precision Hits.
> New Ratio = (Base Ratio - 50%) / (1 - 50%)

Formatted source colors distinguish modes: `30% increased` is PvE blue `#a4c2f4`; `[7% decreased on Hand Cannons]` is PvP red `#ea9999`. The Landing sheet legend explicitly identifies PvE/combatants and PvP/Guardians. All selected eligible weapons are scouts/snipers; the hand-cannon PvP exception does not belong to selected63 W80 eligibility.

Let **B** be original full, nonprecision, pre-shot-distance-falloff body damage for the relevant weapon/target, and **M** the original precision multiplier (use M=1 for body). The source explicitly supplies the split and compensation; the following is algebra from that supplied formula:

- Direct impact body: `0.5 B`.
- Compensated direct precision: `0.5 B × ((M − 0.5) / 0.5) = BM − 0.5B`.
- PvE explosive component: `0.5 B × 1.3 = 0.65 B`, independent of precision.
- In-range body total: `1.15 B`; in-range precision total: `BM + 0.15 B`.
- Relative precision gain is `15% / M`; it is not a flat 15% precision-damage buff.
- For non-hand-cannon PvP, the DDC's mode-specific summary says body damage remains the same and precision remains “roughly” the same; the split without the PvE modifier algebraically restores `B` / `BM` before later mode-specific rounding or sandbox adjustments.

**Parent proposal:** `impact = (B*M − B*0.5) * rangeFalloff; explosion = B*0.5*1.3`. The compensated precision split and PvE explosion term are verified from the inspected DDC formula. Half of the entire crit damage would contradict that formula. **The no-shot-distance-falloff clause still requires a separate inspected source**; DDC's EP row does not itself state range falloff. Keep this part provisional until the follow-up evidence below is complete.

**Explosion precision:** false for direct-target and nearby splash. Preserve the original precision bonus in compensated impact only. Native trigger is projectile impact/contact, not a precision hit or kill; nearby enemies receive the impact-centered AoE. No explosion occurs merely because an enemy is near a flying shot. Official base description independently says “Projectiles create an area-of-effect detonation on impact.”

## Requested local integration contract — distinct from external measurements

Parent requested one original shot cost and one positively identified original owner/weapon/shot token; full damage is converted into impact plus explosion, rather than appending a blast to unchanged full impact damage. Single hitscan applies only on exact eligible sockets. Native block/world contact and entity contact both need a resolved impact position for nearby splash; contact-trigger wording supports impact AoE but does not establish Minecraft callback details.

Apply impact then explosion as separate damage transactions. Explosion final blows must have precision=false and cannot activate precision refunds, Outlaw, or Dragonfly. Positive original weapon kill ownership can route splash final blows to Kill Clip/Rampage token handling when legally co-equipped; none of these five can co-equip base Rampage in the pinned catalog. No unsupported claim is made that Destiny uses this project's transaction/event implementation.

A 3 m maximum radius is sourced. Spherical selection, line of sight, nearest-AABB-point distance, exact boundary inclusion, splash radial attenuation, and wall occlusion algorithms remain local policy unless a separate source is found. No friendly fire, invalid/protected target exclusion, shooter exclusion, and PvP mode filtering must use parent targeting policy; the DDC says “enemies” but does not measure all these cases or justify bypassing protection.

## Current / historical boundary and remaining uncertainty

Current means the actual original DDC content inspected on 2026-10-24, not a claim that it was last updated that day. The official socket catalog is the pinned October manifest, not a historical claim that every reissue of the same weapon name has these pools. Base EP only; enhanced EP `64866129` and Timed Payload are excluded. DDC's ↑+5 reload is enhanced-only and must not be granted to base EP.

Historical Bungie content was read through a Jina text renderer because direct news URLs returned only a JS shell; the cached exact excerpts identify both original URLs and retrieval URLs. The current original DDC and Clarity EP records do not explicitly mention shot-distance falloff, so that clause remains unverified here. No historical percentage is substituted for current data. Exact splash attenuation, LOS geometry, and projectile material/immune-target edge cases are not established by the inspected EP row.


## Additional exact coexistence evidence

[coexisting-sockets.json](references/coexisting-sockets.json) retains all five exact third-column raw sockets/pools. Distant Relation can legally combine EP with **Triple Tap or Outlaw**; Apostate can legally combine EP with **Outlaw**. These are actual selected-catalog precision-credit exclusion cases. ALH shares socket 3 with those perks on Distant Relation, so ALH and Outlaw cannot both occupy that same slot.

Dragonfly is an EP alternative in socket 4 for Distant Relation and Long Arm. Kill Clip/Multikill Clip are EP alternatives in socket 4 for Apostate. There is **no legal selected EP+Kill Clip, EP+Rampage, or EP+Dragonfly pair**. Generic kill-token plumbing should not authorize an otherwise illegal pair. Direct compensated-impact precision final blows may still qualify for a legal Outlaw perk; the later nonprecision explosion final blow may not.

## Independent original compendium corroboration

[clarity-explosive-payload.json](references/clarity-explosive-payload.json) is the exact base-EP record from the original [Clarity live database](https://github.com/Database-Clarity/Live-Clarity-Database), fetched directly at an immutable Git commit. It explicitly says the payload splits off 50% of bodyshot damage, detonates on impact, receives +30% damage in PvE, cannot benefit from crits, and the impact receives compensation. It independently states the PvE total gain is 15% of bodyshot damage. Its PvP wording cautions that critical totals can vary by 1–2% either way; do not promise bit-exact universal PvP equality from the ideal formula. Record `lastUpload` corresponds to 2025-02-04 UTC; the exact value/time and repository commit date are in the capture. This older record is corroboration, not a newly measured October 2026 result.

## Inspected historical Bungie primary content

- [Update 7.3.5, March 5, 2024](https://www.bungie.net/7/en/News/article/destiny_2_update_7_3_5), [exact excerpt](references/bungie-2024-03-05-excerpt.json): under Crucible damage changes, hand cannons had critical damage increased 10%, body damage reduced 5%, and flinch reduced 12.5% for impact / 10% for EP. These flinch percentages are not an EP damage split or PvE damage nerf.
- [TWID April 4, 2024](https://www.bungie.net/7/en/News/article/this-week-in-destiny-04-04-24), [exact excerpt](references/bungie-2024-04-04-excerpt.json): previewed adaptive hand-cannon body +1% / crit +4% adjustments and explicitly said the EP reduction was offset to permit three critical hits against any resilience within optimal range. It is a historical announcement, not independent proof of a shipment date or current scout/sniper multiplier. A March 21 preview was also read but is redundant and not cached.

These historical hand-cannon details explain why old reports about EP losing three-crit kills must not be generalized to the current selected five. Current DDC separately labels its PvP −7% explosive modifier as hand-cannon-only. Enhanced ↑+5 reload is excluded from base EP.

## Parent/test contract and explicit limits

[source-contract.json](references/source-contract.json) separates verified equations/radius/socket eligibility from requested local runtime rules and unverified details. Example from the DDC equation: B=100, M=2 gives impact 150 + PvE explosion 65 = 215; body gives 50+65=115. B=100, M=3 gives 250+65=315. These are algebra examples, not fresh in-game measurements.

The parent's full proposal `(BM−0.5B)F + 0.65B` is **verified for conversion/precision/PvE bonus**, while the decision to leave explosion unaffected by shot-distance F remains **provisional without explicit source in this research**. Do not conflate shot-distance falloff with radial splash attenuation. A 3 m radius alone proves neither uniform splash damage nor a particular attenuation curve.

Native contact/AoE wording does not require a kill or accepted direct damage and does not support a proximity fuse. Resolve an impact at actual entity/world contact and apply nearby-hostile selection; exact friendly contact, immune contacts, self damage, LOS, AABB distance and protection handling are local policies. Preserve PvP/party exclusions through existing target policy; there is no evidence here for bypassing them.

Evidence caches are minimal exact rows/records/excerpts with source URLs, retrieval time, raw-response SHA256, and input hashes. [provenance.json](references/provenance.json) pins the delivered files. Entire Bungie inventory/plug-set databases remain in their original pinned private caches. No production tests were run for this documentation-only task.


## Final stagger / enhanced / local-policy boundary

The inspected original Clarity wording says the payload “staggers PvE Combatants more”; DDC says “inflicts increased stagger.” Neither source supplies a numeric stagger tier, poise damage, flinch impulse, duration, proc threshold, guaranteed interrupt, immunity bypass, or intrinsic Unstoppable/Champion stun. Do not invent those mechanics. Bungie's historical 10% hand-cannon EP **flinch reduction** is a 2024 PvP tuning detail, not an instruction to assign a stagger tier or a current general EP multiplier.

**Base EP `3038247973` grants no sourced reload bonus.** The DDC's `↑Passively grants +5 Reload Speed` is enhanced-only. Enhanced EP `64866129` is excluded; its official description separately says “Improves reload.” No enhanced statistic/duration or Timed Payload behavior is transferred to W80 base EP.

The parent reports an explicitly local `.25` radial policy, nearest-AABB-point distance, LOS, and cap. These are not Destiny measurements and are not derived from the sourced 3 m radius. The bullet-distance-falloff exemption remains **not verified by an inspected primary/original-compendium statement in this task**. Its absence from these entries does not prove that explosion damage actually suffers bullet-distance falloff; the researched sources simply do not establish either behavior explicitly.
