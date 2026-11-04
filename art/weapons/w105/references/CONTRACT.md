# W105 shotgun source contract — evidence established

Scope: L1 source research only. W104 is sealed. Only the new extractor, this references directory, w105-shotgun-patterns.json and ignored run/private-sources/w105 are owned.

Pinned Bungie manifest: 245114.26.10.13.2000-1-bnet.66137. All 63 selected IDs/hashes will be checked; exactly five selected shotguns:

| Local ID | Bungie item hash | Frame | Initial intrinsic hash | Socket | Historical S19 pattern |
|---|---:|---|---:|---:|---|
| mindbender_s_ambition_adept | 912150785 | aggressive | 3983457027 | 0 | fixed, evenly distributed cone |
| dust_rock_blues | 636912560 | precision | 1636108362 | 0 | vertical oval |
| first_in_last_out | 3616586446 | pinpoint_slug | 918679156 | 0 | single slug; no pellet pattern |
| parcel_of_stardust_fell_to_earth | 2217366863 | lightweight | 1458010786 | 0 | diamond |
| ikelos_sg_v1_0_1 | 1887808042 | rapid_fire | 996573084 | 0 | square |

Every initial socket is in intrinsic category 3956125808. Parcel's official item name is Parcel of Stardust; the parenthesized local label is not a separate official item edition. The slug intrinsic explicitly describes a single-slug round. Do not substitute a similarly named Precision Frame intrinsic.

Bungie's 2022-12-01 S19 preview explicitly assigns the four qualitative fixed shapes: https://www.bungie.net/7/en/News/article/51999 . This is historical evidence, not proof of unchanged 2026 tuning. Fixed does not establish exact coordinates or angles. The source describes a cone for aggressive, not a hollow circle.

Pellet count: **12 is primary historical evidence**, not merely community reporting. Bungie 2021-08-19 explicitly states the count: https://www.bungie.net/7/en/News/article/50572 . Its randomized ring distribution is superseded and is not adopted. The four original S19 illustrations linked by the 2022 article each visibly contain 12 impact marks (human visual inspection; pinned private PNGs). Neither source independently certifies unchanged 2026 count. The resource uses pelletCount=12 with pelletCountScope=historical_2021_text_and_2022_S19_illustrations and currentPelletCount=null. Slug pelletCount=null, singleSlugRound=true, slugProjectileCount=1. Do not derive count from manifest stat 3555269338: it is also 12 on the slug.

Exact historical evidence maps only to the four non-slug selected IDs above. Master may adopt that count under the chosen historical fidelity target while preserving local HP budget. Do not claim current live count is independently verified.

ADS: **generic shrink/no-shrink remains unresolved**, including for the S19 revision. Runtime WeaponRuntime.java:655-657 reaches 0.65 at full ADS; that is local tuning with no source-exact status. genericAdsShrinksPelletSpread=null and genericAdsSpreadMultiplier=null. Null is not false, 1.0, 0.65 or any default.

Bungie 2020-02-20 says ADS no longer changes effective range: https://www.bungie.net/7/en/News/article/48743 . That is not a quantitative spread statement. Conflicting dated community assertions (2020 testing report and 2023 discussion) are kept as secondary reports, with no adopted generic rule. Full Choke base 1047830412 and enhanced 3311319252 explicitly describe conditional ADS spread reduction in the pinned manifest; no selected/equipped barrel eligibility is claimed here. Bungie's 2026-06-09 Update 9.7.0 separately documents Full Choke and Shot Package changes: https://static01.bungie.net/7/en/News/Article/destiny_update_9_7_0 . These are perk/intrinsic exceptions. All five selected initial intrinsics differ from Shot Package 3054949324. No conditional perk percentage is encoded as a universal scalar or adopted into runtime.

Temporal warning: the 2023-07-06 S21 preview explicitly retunes lightweight outer horizontal spread: https://www.bungie.net/7/en/News/Article/weapon_tuning_s21_mid_season . The 2023-02-01 S20 preview separately changes reticle response to spread angle: https://www.bungie.net/7/en/News/article/s20-weapon-tuning-preview . Shape labels, projectile angle, FOV/zoom, reticle screen size, range/falloff and aim-assist remain distinct. No current-source pattern coordinates or base angles were established.

The JSON will carry exact roster, dated source claims, evidence IDs, qualitative shapes and explicit unknowns. No authored pellet coordinates, spread angles, aspect ratios or geometry scalars are encoded in this source profile. Master will use the inspected official S19 PNGs to author historical image-informed estimated impact centers and four reticle outlines. Those are visual estimates, not exact engine coordinates, exact pixels or unchanged current geometry. Physical spread and ADS scaling remain local tuning. Master owns any exact four-non-slug count exception and replacement of WeaponCombatTest's old eight-pellet/cap-eight assertions; no broad test weakening is authorized here. Master will preserve the old local total HP budget using old-eight/new-count scaling; this is local Minecraft policy, with no original Destiny damage claim or source numeric damage encoded here.

Offline verification will fail closed on source SHA drift, identity/socket/category/definition drift, unsupported temporal promotion and output byte drift. Two disjoint offline reproductions and bounded negative fixtures are required before final handoff. No Java/tests/shared docs/registry/build/runtime/CU/assets edits.


Research bound is exhausted at exactly eight focused query strings (four search batches). Later calls only open/find/click discovered sources. Direct article HTTP fetches returned a 1,301-byte JavaScript shell, not article text; these are explicitly excluded as article evidence. URL-bound web-tool extracts supply the text evidence. Actual official PNG bytes were retrieved and inspected. No delegated child work is claimed.


## Runtime schema 1 (available before references were generated)

The resource is `src/main/resources/destiny/weapons/w105-shotgun-patterns.json`. Top-level fields are stage, schemaVersion, manifestVersion, patternScope, weapons, sourceRules, localPolicy, evidencePath. Every weapon row has id, hash, frame, intrinsicHash, socket, pattern, pelletCount, pelletCountScope, singleSlugRound, slugProjectileCount, evidenceIds. The five rows are the table order above. Pattern tokens are fixed_evenly_distributed_cone, vertical_oval, single_slug, diamond, square respectively. Socket is always integer 0; every ID/hash/frame/intrinsic tuple must match exactly. Slug pelletCount is null and slugProjectileCount is integer 1. Other rows have pelletCount integer 12 and slugProjectileCount null.

`sourceRules` has only explicit nulls: currentPelletCount, currentPatternUnchangedSinceS19, genericAdsShrinksPelletSpread, genericAdsSpreadMultiplier, pelletCoordinates, baseSpreadAngleDegrees, patternAspectRatios, sourceDamagePerPellet, sourceDamageScalars. No null-to-zero/default coercion. `localPolicy` retains the existing 1 - .35 * ADS factor as unconfirmed local tuning and assumes no Full Choke. Master owns image-informed geometry/reticle estimates and old-eight/new-count local HP scaling. No original Destiny damage claim.

## Historical visual arrangement handoff

Original image paths are ignored private research inputs, not shipped assets:

- run/private-sources/w105/aggressive.png: central impact, four inner, seven outer; occupied interior.
- run/private-sources/w105/precision.png: ten perimeter impacts around the vertical oval and two interior impacts on its vertical axis.
- run/private-sources/w105/lightweight.png: eight around the diamond and four interior impacts forming a cross.
- run/private-sources/w105/rapid_fire.png: eight square-corner/side-midpoint impacts and four interior impacts.

All are 250 by 250 original official PNGs. Turquoise reticle lines are not pellet impacts. Arrangement was visually inspected; SHA pins preserve these observations' actual image inputs. Offline extraction does not pretend to rerun visual analysis. Approximate image-relative centers may inform master's historical geometry without becoming a claim about engine angles or current tuning.


## Final verification

PASS: four generated JSON files, two disjoint reproductions (the second with independently copied script and complete private source cache), read-only offline verification, fifteen semantic negative fixtures and two black-box CLI tamper fixtures. All 314 sealed W104 files and their file set are unchanged. See verification.json and REPORT.md. Re-run `rtk proxy python3 scripts/extract_shotgun_patterns_w105.py --verify --self-test`. No builds/runtime were run.
