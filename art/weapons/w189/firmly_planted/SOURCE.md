# W189 base Firmly Planted

Base hash **280464955** only; enhanced **3920370755** is excluded. This package contains effects and exact selection/timing data. Master owns the shared registry, actual crouch/source authority, companion collection, runtime gameplay, HUD/debug routing and native batch. No proc HUD, reload, damage or extra recoil-direction stat is introduced.

## Numeric evidence

Current user-priority [DDC Weapon Perks, gid1662574278, row97](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278), fetched 2026-10-27. Whole HTML SHA256 eae6696dfc65d4cc195026df2abb015fd758b4f7e136ea16701ae5536eaac4cc; exact HTML row and text are retained in clarity-source.json. CSV export returned HTTP401; the current HTML sheet succeeded. The row has no PvE/PvP split. Basic and enhanced arrow values are distinct:

| Base only, while crouched | Stability | Handling | Cone size | Cone growth | Horizontal recoil yaw |
| --- | --- | --- | --- | --- | --- |
| Ordinary | +20 | +30 | .6 | .83 | .2 |
| Fusion | +10 | +15 | .8 | .915 | .6 |

Enhanced ordinary +25/+35 and Fusion +13/+18 are provenance only, never applied. Original text, including any uncertainty markers, remains verbatim. Row97 contains no question marks for these base numeric values; no unspecified flinch percentage, pitch reduction, damage, reload or lifetime is inferred. Stability's existing gameplay mapping remains master's integration responsibility.

Clarity independently confirms crouch condition, ordinary bonuses and halved Fusion effects. Exact original base entry and commit039cfbc4732c33573568b28cc6335dd3332a9296 are retained in clarity-source.json. [Immutable original source](https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/039cfbc4732c33573568b28cc6335dd3332a9296/descriptions/clarity.json); whole SHA256881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384. These are numeric source records; they are not gameplay footage or visual/model evidence. This worker makes no native/audio/footage/IK/performance claim.

## Official eligibility and co-selections

Pinned Bungie manifest245114.26.10.13.2000-1-bnet.66137, English item/plugset components e677f6ea-2a1e-48d4-a8c8-700a39a62585, from the user-specified existing caches. All source SHA256s and byte counts are recorded in manifest.json. All65 actual catalog entries including exotics were examined. Admission requires exact legendary nonexotic item, trait category4241085061, actual randomizedPlugSetHash, isFakePlugSet exactly false, currentlyCanRoll exactly true and exact base hash. Names, initial/default/reusable fields and enhanced entries never grant support.

| Weapon | Item hash | FP socket | Random pool |
| --- | --- | --- | --- |
| seventh_seraph_officer_revolver | 3037520408 | 3 | 903350103 |
| steelfeather_repeater | 1251729046 | 3 | 473189353 |
| distant_relation | 2034817450 | 4 | 3824767299 |
| whispering_slab | 211938782 | 3 | 1885424927 |
| bite_of_the_fox | 1403800851 | 3 | 563442205 |
| beloved | 3107853529 | 3 | 1196545279 |
| apostate | 2164448701 | 3 | 1306932196 |
| dream_breaker | 2931957300 | 3 | 3785896921 |

Apostate's official randomized pool contains two matching current base entries with different source metadata. Both are retained as proof; they resolve to one identical Roll, not duplicate available selections.

All35 implemented registry IDs were independently compared to the generator's35 profiles (snapshot_sights, vorpal_weapon, explosive_payload and archers_tempo use their actual IDs). There are **32 exact distinct-socket co-selections and22 same-socket denials**, fully listed in official-sockets.json. That file retains full official trait pools, current65 scans, both exact perk definitions, accepted proof entries and all implemented-trait audits.

The only handling/ADS companions are:

| FP weapon/socket/pool | Companion socket/pool | Exact base companion |
| --- | --- | --- |
| Steelfeather 3/473189353 | 4/2645685327 | Elemental Capacitor3511092054 |
| Dream Breaker 3/3785896921 | 4/1206254527 | Frenzy4104185692 or Quickdraw706527188 |
| Beloved 3/1196545279 | 4/887157889 | Quickdraw706527188 |
| Apostate 3/1306932196 | 4/2826016044 | Quickdraw706527188 or Snapshot Sights957782887 |

Each companion independently meets the same official category/random/nonfake/current predicate and exact implemented Roll identity. Shared socket4 choices cannot be selected together. No Surplus, Threat Detector, Adrenaline Junkie, Stats for All or Perpetual Motion companion grant is implied. Apostate Rapid Hit is a legal stability/reload companion, not an additional handling bonus. Every other legal effect is left to its existing implementation.

## API and raw timing contract

FirmlyPlantedProfile publicly exposes ID/HASH, rolls(), supports(Entry), stabilityBonus(Entry), handlingBonus(Entry), accuracyScalar(Entry), growthScalar(Entry), yawScalar(Entry), handlingTicks(Entry,int TOTALbonus,double scalar,boolean ready), adsTicks(Entry,int TOTALbonus,boolean snapshotEntering) and compatible(Entry,String perk,WeaponPerks.Roll selected).

Unsupported, null or noncanonical Entry returns 0 stat bonuses, 1 scalars and false compatibility; timing calls throw IllegalArgumentException. Entry equality checks every canonical catalog field. rolls() is immutable. compatible is exact across all five Roll fields, actual perk ID, canonical weapon and distinct socket. The profile does not decide whether the player is currently crouched or owns a genuine equipped selected weapon; master checks those conditions before using its effects.

Timing TOTALbonus already includes FP plus all legal active companion increments. Sum first using a wide integer, cap baseHandling+TOTALbonus to0..100, evaluate original raw seconds, multiply the supplied handling scalar, then ceil(seconds*20) once. FP itself has no handling duration scalar. For Quickdraw, master passes enough total bonus to reach100 handling; ready scalar is .95 and stow scalar is1. No caller should multiply an already rounded timing. Stow retains the accepted historical stat100 floor.

adsTicks uses the same total handling, with Snapshot's special-ammo .8 only when snapshotEntering=true and the exact distinct official pair exists (Apostate only). false is used for ordinary entering or exiting; exit never inherits Snapshot's scalar. Handling duration scalars do not modify ADS.

Raw coefficients come directly from pinned art/weapons/w46/weapon_formulas.json and family/category mapping art/weapons/w43/extraction.json, matching W183/W184's original d2foundry oracle commitdcd0c7d302b056ffbb532edcb711d724a17ca8c1. stat_calc.rs, rs_types.rs and MIT/UNLICENSE hashes are retained. Base handling is checked against original/current w40-characteristics.json and supplied official item JSON. All8 neutral ready/stow/ADS results exactly reproduce existing W58/W44 JSON. These historical community curves are not fresh current-sandbox gameplay measurements. No invented curve fields or prior rounded-duration multiplication is used.

| Requested combined case | Total bonus | Ready | Stow | ADS |
| --- | --- | --- | --- | --- |
| Dream FP+Frenzy |115|8|4|5|
| Steel FP+Arc EC |80|5|5|5|
| Apostate FP+Snapshot entering |30|6|5|6|
| Apostate FP, Snapshot exit |30|6|5|7|
| Dream FP+Quickdraw ready .95 / stow1 |100|7|4|5|

All units are Minecraft ticks at20TPS. Full8 baseline/crouch comparisons and17 combined timing vectors are in manifest.json. Dream Quickdraw proves the single-ceil rule: raw ready produces7, whereas ceil(previous8*.95) incorrectly produces8.

Initialization reads JSON directly and never calls WeaponCatalog.find/all, WeaponCharacteristics.of or WeaponPerks registries. Resource SHA256 and exact schema/roll/curve/pair checks fail closed. This avoids a profile/catalog/perk bootstrap cycle.

## Verification and handoff

`rtk proxy python3 scripts/build_firmly_planted_w189.py --verify --self-test` is offline and read-only, pins all actual source inputs, verifies all4 generated JSONs, runs69 bounded negative cases and checks deterministic regeneration. The generator writes only the4 owned JSON outputs in non-verify mode. No shared build, server or dependency compilation is needed.

FirmlyPlantedW189Test has10 focused JUnit cases covering exact8/current65, neutral/null/forged entries, strict resource mutations, all35/32/22 pair audits, all8 legacy baselines,17 frozen crouch/combined timings, caps/invalid scalars/one ceil/Snapshot entry-exit, original coefficient fields/current stats and bootstrap source guards. Isolated compilation and JUnit execution passed10/10. Actual production Catalog, Exotics, Characteristics and enums were compiled; only WeaponPerks.Roll's record carrier was reproduced outside source to avoid compiling shared Minecraft runtime. Profile-first initialization before Catalog succeeded. This is not a full production Gradle/actualGT result; master owns that check.

Worker outputs, harness, logs, downloads, registry-ID coverage and concrete native queue remain outside source at /private/tmp/w189-planted-report. Master native queue: crouch/stand transitions on ordinary and Fusion weapons; genuine held/incoming/outgoing authority and forged/corrupt/ineligible/enhanced denials; exact FP+ArcEC80, FP+Frenzy115, Quickdraw ready/stow and Apostate Snapshot enter/exit; stability/flinch, cone bloom/growth, yaw-only recoil with unchanged pitch; no proc HUD; death/disconnect/inventory edits with immediate passive authority checks. The worker did not run that queue.
