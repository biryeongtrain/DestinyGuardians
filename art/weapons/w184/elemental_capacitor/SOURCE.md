# W184 base Elemental Capacitor / 원소 축전지

Only base hash3511092054. Enhanced711234314 is explicitly excluded. Current official English Bungie inventory/plugset components share manifest version245114.26.10.13.2000-1-bnet.66137 (component suffixe677f6ea-2a1e-48d4-a8c8-700a39a62585). Generator reads existing offline caches; it downloads nothing. manifest.json pins every input SHA256 and output SHA256, including all historical formulas and their license files.

## Selector and effect sources

Clarity-Destiny Descriptions: https://github.com/Clarity-Destiny/Descriptions . The pinned full cache and extracted original base entry are in manifest.json / clarity-source.json. Current Destiny Data Compendium perks CSV, pinned SHA2567880b2029a7e7b8f97afb8f079ca48a585ec0765a94b6b3f983a47daf983ba30, independently agrees: **equipped Super Ability**, Solar+50 reload speed, Arc+50 handling, Void+20 stability. Enhanced higher values in the DDC row are not base values.

Use only the existing attached GuardianData active class's equipped SUPER ID; registry resolution must match exact ID, SUPER slot and active non-NONE guardian class. KINETIC/null/missing/invalid resolves neutral. Other powered abilities, last cast, weapon element, energy0/1 and cooldowns do not select the bonus. No attachment/runtime/session is created and no passive timer/stack HUD row exists.

**Stasis and Strand are absent from the current Element enum. Neither is simulated or implemented.** The source includes them as provenance only. No native, audio, performance, IK, current Destiny sandbox timing or exact-engine timing claims follow from this offline work.

## Official socket audit

Independently rescanned all65 current selected catalog/characteristic entries, including exotic metadata. Admission requires legendary nonexotic, official trait category4241085061, randomizedPlugSetHash, real nonfake pool, currentlyCanRoll exactly true and base hash exactly3511092054. Initial/default, reusable, fake, enhanced, non-current and unrelated slots do not grant EC. Complete per-weapon scan, exclusions, selected socket proofs and full official companion pools are in official-sockets.json.

| Weapon | Official item | EC socket | Plugset |
| --- | --- | --- | --- |
| Steelfeather Repeater |1251729046|4|2645685327|
| Patron of Lost Causes |2723241847|4|120674550|

Exactly five distinct pairs among currently implemented traits: Steelfeather socket3 Feeding Frenzy2779035018, Subsistence1820235745, Grave Robber1631667848 (pool473189353); Patron socket3 Rapid Hit247725512, Grave Robber1631667848 (pool2564227946). Only FF/RapidHit alter reload timing. MKC/Swashbuckler/Surrounded/Vorpal on Steelfeather and Payload/Vorpal on Patron share EC socket4 and cannot compose. Official pools and current profiles both contain no Patron/Steelfeather Surplus or Outlaw; **no hidden Surplus bonus or broadened grant**. Other official socket3 options (e.g. Field Prep, Slideways) are retained as source evidence, not claimed implemented.

## Math and ownership

Historical d2foundry oracle commitdcd0c7d302b056ffbb532edcb711d724a17ca8c1 from art/weapons/w46: weapon_formulas.json, stat_calc.rs, rs_types.rs and license pins. Family/category mapping is pinned art/weapons/w43/extraction.json. Both selected whole-magazine weapons reproduce existing W46 reload, W58 handling and W44 ADS baselines exactly. Raw quadratics, base stats, neutral/Solar/Arc/Void cases and40 FF/RapidHit combinations are in curves.json. Source-current socket/bonus truth and historical timing approximation remain distinct.

Sum nonnegative reload bonuses then cap stat100, evaluate raw seconds, apply the sourced FF/RH scalar and ceil(seconds*20) once. The existing profiles expose capped effective-minus-base stat increments; with EC's nonnegative50 addition this yields the same final capped stat as uncapped tier sums. EC adds no reload scalar. Stow retains the historical stat100 floor; ADS changes only through Arc handling, with no Snapshot pair. No applicable Solar/Arc bonus returns the previous plan/ticks unchanged, preserving prior legal companion bonuses. Accepted reload Plan is immutable; future SUPER edits affect future queries only.

Source authority follows production SurplusW183: alive, connected, nonspectator, nonSuper owner; read-only genuine inventory object identity. Handling accepts genuine equipped incoming/outgoing objects before selection, including when a nonweapon is selected. Element/HUD/debug/stability/ADS/reload require the actual held equipped EC source. Master owns shared registry/routing/runtime/debug/stability/HUD/gates and actualGT/native integration. Static source guards and pure selector/math JUnit tests do not establish native identity/lifecycle correctness.

Regeneration: rtk proxy python3 scripts/build_elemental_capacitor_profile_w184.py --verify --self-test
