# W183 Surplus source and adaptation

BASE trait **3436462433**; enhanced **2658083589** is excluded. The generator scans the current65 catalog (W30 63 entries plus W83/W84 exotic entries) against the pinned Bungie inventory and plug-set components. It accepts only non-exotic legendary weapons whose actual trait-category socket references a non-fake randomizedPlugSetHash containing the BASE trait with currentlyCanRoll=true. Reusable/default plugs, enhanced traits, non-trait sockets, fake pools and non-current entries never grant membership.

Official manifest version: `245114.26.10.13.2000-1-bnet.66137`. Component suffix: `e677f6ea-2a1e-48d4-a8c8-700a39a62585.json`. Exact byte SHA256 pins, full65 scan, accepted socketEntry/matchingEntry and rejected matches are in manifest.json / official-sockets.json. The source files remain external read-only caches:

- `/tmp/destiny-weapons-w30/bungie-items.json`
- `/tmp/destiny-weapons-w60/bungie-plugsets.json`
- `/tmp/destiny-weapons-w60/manifest.json`
- `/private/tmp/w167-clarity.json` (Clarity-Destiny/Descriptions, BASE entry records lastUpload=1709252348445)
- `/private/tmp/w182-hir-report/ddc-perks.csv` (current downloaded Destiny Data Compendium perks table; SHA256 `7880b2029a7e7b8f97afb8f079ca48a585ec0765a94b6b3f983a47daf983ba30`)

Both Clarity BASE and the exact current DDC Surplus row agree:

| Charged powered slots | Stability | Handling | Reload |
|---|---:|---:|---:|
| 0 | 0 | 0 | 0 |
| 1 | 5 | 5 | 10 |
| 2 | 15 | 25 | 25 |
| 3 | 25 | 60 | 60 |

No 50-point tier is used. clarity-source.json retains the BASE entry verbatim and complete CSV Surplus row. The enhanced entry is provenance only and never admitted.

The exact9 BASE socket3 entries are Ammit AR2, High Albedo, Brass Attacks, Biting Winds, Beloved, Apostate, Deafening Whisper, Canis Major and Code Duello. Eligibility is exact catalog identity + official hash/socket/pool, never a family grant. A checksum pins the entire production resource; the profile also verifies all canonical catalog fields, official stats and all four pre-existing timing baselines.

Official distinct socket companion proof yields Snapshot4 (High Albedo, Biting Winds, Apostate, Deafening Whisper), Frenzy2 (Brass Attacks, Code Duello), Adrenaline Junkie1 (Ammit), Rapid Hit1 (Apostate), Threat Detector1 (Deafening Whisper). PM, Outlaw, Feeding Frenzy, Stats for All and Heating Up have no distinct pair. Same-socket candidates are recorded as rejected. No universal allperks permission is granted. Existing traits affecting unrelated damage do not become Surplus timing bonuses.

Timing uses the existing W43 category mapping and W46 historical D2Foundry oracle equations, commit `dcd0c7d302b056ffbb532edcb711d724a17ca8c1`; raw formula sources/license files are separately pinned. The generator reproduces W46 reload, W58 ready/stow and W44 ADS baselines before producing any bonuses. These historical community equations are **not current sandbox measurements or exact-engine claims**. Sum legal active RAW stat bonuses, cap handling at100 and reload at100 (bow nock85 per the existing Rust stat_calc), apply sourced companion scalars, then ceil(seconds*20) once. Stow uses the original at100 floor before scalar. Snapshot scales ADS entry only; Surplus adds no ADS animation scalar. Bow draw is unchanged. None of the9 weapons uses incremental shell reload.

Runtime adaptation: read only the real attached GuardianData, active class/loadout, exact registered ability ID and matching ability.slot()/guardianClass(). Count GRENADE, MELEE and CLASS_ABILITY only when cooldown<=0. The current Ability API has no independent enabled boolean: registered, equipped, matching class/slot is its enabled configuration. Missing/unknown IDs, classNONE, SUPER/JUMP, dead/removed/spectator/disconnected players and active super never count. Current Hunter has one charge per slot; no invented multi-charge counters or timer sessions.

Held queries require the real genuine owned equipped selected main-hand object. Ready/stow also accept genuine incoming/outgoing equipped objects before selection and do not require the currently held nonweapon to pass canUse. Explicit standalone hotbar compatibility follows the existing PM pattern. Backpack, offhand, preview and external copied objects are rejected. All getters are read-only, do not create attachments/runtime, and never activate/recharge an ability. A returned immutable Plan snapshots the live count and compatible companion state at acceptance; later ability use/recharge cannot mutate it.

Offline checks are production Java JUnit profile/math and pure ability projection tests, deterministic generator negatives and static source guard checks. Static checks are not runtime identity proof. Master owns shared registry/routing/HUD, actualGT, native input/rendering and paid stability integration. Native-pending and failures are reported separately under the assigned report directory.
