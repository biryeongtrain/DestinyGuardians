# W105 source/research L1 — completed handoff

The schema-1 runtime resource is `src/main/resources/destiny/weapons/w105-shotgun-patterns.json`. Its exact five rows were delivered before the other generated references. CONTRACT.md was written as soon as the initial evidence was available and updated with count, ADS and image-informed integration policy.

## Exact identities and dated rules

| Local ID | Item hash | Frame | Intrinsic hash | Historical pattern | Pellet count |
|---|---:|---|---:|---|---:|
| mindbender_s_ambition_adept | 912150785 | aggressive | 3983457027 | evenly distributed cone, occupied interior | 12 |
| dust_rock_blues | 636912560 | precision | 1636108362 | vertical oval | 12 |
| first_in_last_out | 3616586446 | pinpoint_slug | 918679156 | single slug | not applicable; one slug round |
| parcel_of_stardust_fell_to_earth | 2217366863 | lightweight | 1458010786 | diamond | 12 |
| ikelos_sg_v1_0_1 | 1887808042 | rapid_fire | 996573084 | square | 12 |

Every intrinsic is initial socket 0 under category 3956125808. All 63 selected hashes were classified against the official inventory, so no selected shotgun is silently excluded. Exact socket/definition/pool proofs appear in roster-proof.json. These intrinsic reusable pools are fake source pools; they corroborate initial sockets and are not misrepresented as randomized trait rolls. Parcel's official item name omits the local parenthetical alias.

[Official August 2021 text](https://www.bungie.net/7/en/News/article/50572) explicitly establishes twelve pellets historically. Its randomized wedge/ring distribution is superseded and not adopted. [Official December 2022 S19 preview](https://www.bungie.net/7/en/News/article/51999) assigns the qualitative fixed shapes and links four original illustrations; each visibly shows twelve impacts. Count evidence is primary historical, not merely community support. No inspected source independently establishes unchanged live 2026 count. `sourceRules.currentPelletCount` remains null.

## ADS and revision limits

Generic ADS pellet-spread shrink/no-shrink and its magnitude are unresolved, including for S19. The [February 2020 effective-range statement](https://www.bungie.net/7/en/News/article/48743) must not be silently read as a physical spread multiplier. Community assertions conflict; their evidence is explicitly secondary and not adopted. Exact community post dates were not verified, so their published fields are null rather than invented timestamps.

Pinned Full Choke descriptions establish a conditional ADS spread effect; the [June 2026 patch](https://static01.bungie.net/7/en/News/Article/destiny_update_9_7_0) separately discusses Full Choke and Shot Package. None of the selected initial intrinsics is Shot Package 3054949324. No equipped Full Choke assumption or generic ADS scalar follows from those exceptions.

The [S21 lightweight retuning](https://www.bungie.net/7/en/News/Article/weapon_tuning_s21_mid_season) proves later tuning occurred. The [S20 reticle response change](https://www.bungie.net/7/en/News/article/s20-weapon-tuning-preview) concerns HUD size response. Shape, physical spread, reticle screen size, FOV/zoom, range/falloff and aim assist are kept distinct. Original spread angles, coordinates, aspect ratios, damage and generic ADS source scalars remain null.

## Original illustrations and master integration

Pinned original private inputs are:

- `run/private-sources/w105/aggressive.png`: center plus four inner plus seven outer impacts.
- `run/private-sources/w105/precision.png`: ten oval-perimeter impacts plus two on its interior vertical axis.
- `run/private-sources/w105/lightweight.png`: eight diamond-perimeter impacts plus an interior four-impact cross.
- `run/private-sources/w105/rapid_fire.png`: eight square-corner/side-midpoint impacts plus four interior impacts.

The PNGs are 250 by 250. Turquoise reticle lines are not impacts. `evidence.json` links the original official URLs and hashes, and retains the human visual observations. The extractor checks actual PNG signatures/dimensions/hashes and recorded observation consistency; it does not claim fresh automated visual analysis.

Master's selected policy is recorded under `localPolicy`: adopt historical twelve for the exact four pellet rows, preserve the old total HP budget by old-count/new-count scaling, retain the existing `1 - .35 * ADS` factor as unconfirmed local tuning, and author historical image-informed estimates of impact centers and four reticle outlines. Those estimates are not exact engine coordinates, exact pixels or current numeric spread. Source JSON contains no authored geometry numbers. Master owns replacing the old exact eight/cap-eight test assertions with exact exceptions, without broadly weakening tests.

## Offline verification

Run:

```sh
rtk proxy python3 scripts/extract_shotgun_patterns_w105.py --verify --self-test
```

All four generated JSON outputs reproduce byte-for-byte in two disjoint output roots. The second reproduction uses an independently copied generator and every copied pinned input, and passes its own offline verify. There is no runtime dependence on the old /tmp caches or network. Verification is read-only and preserves generated output hashes.

Fifteen bounded semantic negative fixtures reject identity/edition/frame/socket/type drift, roster broadening, historical count tampering, mirrored primary source URLs, a ninth query, illustration-count changes, false current-count promotion, null ADS coercion, invented geometry, slug pellets, and an equipped-barrel assumption. Two additional black-box CLI fixtures reject a source SHA mismatch and modified generated bytes with exit code 1. Details and file hashes are in verification.json.

Exactly eight focused query strings were used. Later web calls only opened/found/clicked discovered sources. Direct article HTTP requests returned identical 1,301-byte JavaScript shells; they are excluded as article evidence. URL-bound web-tool extracts carry the text evidence, while the real official PNG bytes were retrieved and visually inspected. All raw research and copied source inputs stay under ignored run/private-sources/w105.

No Java/tests/shared docs/registry/build/runtime/CU/visual assets were changed. No child work is claimed. All 314 files and the file sets under sealed docs/qa/2026-10-25/w104 and art/qa/w104 remain byte-identical to the initial snapshot. Scope of this result is source research and reproducibility, not native/gameplay acceptance.
