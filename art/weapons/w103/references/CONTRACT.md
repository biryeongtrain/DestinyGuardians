# W103 final frozen L1 source/API contract

- Base Demolitionist hash **3523296417**; enhanced hash **1906147653** excluded.
- `perk`: `id=demolitionist`, `hash=3523296417`, `energyPercent=10`, `specialEnergyPercent=20`, `reloadCooldownTicks=60`.
- `specialEnergyFamilies`: `sniper_rifle`, `shotgun`, `glaive`, `fusion_rifle`. Despite the API name this is a family exception, **not Special ammo generally**.
- `mechanicsSource=art/weapons/w103/references/mechanics.json`, `reloadFromReserves=true`, `energyIsBaseChunk=true`.
- `weapons[]` is compatible with generic `WeaponPerks.Roll(id,hash,socket,perkHash,plugSetHash)` and additionally has `proofMode` and `baseEnergyPercent`.

| id | official hash | socket | plugSetHash | proofMode | base % |
|---|---:|---:|---:|---|---:|
| austringer | 3055790362 | 4 | 785215120 | randomized | 10 |
| gnawing_hunger | 821154603 | 4 | 594510568 | randomized | 10 |
| bug_out_bag | 2744715540 | 4 | 575371383 | randomized | 10 |
| lonesome | 2199171672 | 4 | 167712635 | randomized | 10 |
| high_albedo | 1197486957 | 4 | 718633408 | randomized | 10 |
| whispering_slab | 211938782 | 4 | 967526625 | randomized | 10 |
| first_in_last_out | 3616586446 | 4 | 1439234589 | randomized | 20 |
| stormchaser | 3652506829 | 4 | 4213354588 | randomized | 10 |
| retraced_path | 548958835 | 4 | 398391969 | randomized | 10 |
| salvager_s_salvo | 2060863616 | 3 | 253 | fixedCuratedOption | 10 |
| nezarec_s_whisper | 254636484 | 3 | 210449465 | randomized | 20 |

## Required qualifications

- Ten non-fake randomized pools require `currentlyCanRoll=true`, exact selected item hash, and the weapon-perks socket category. No broad family availability inference.
- Salvo socket 3 is a fixed **curated selectable alternative** in reusable fake plug set **253**. Initial perk is Ambitious Assassin (2010801679), not Demolitionist; both curated options have `currentlyCanRoll=true`. Do not assign the trait by default. Keep explicit proofMode validation; do not treat set253 as randomized or fabricate hash0.
- Bow/trace/GL/glaive are included. The exact selected Deafening Whisper wave GL and all five swords have no base Demolitionist in inspected pools, rather than being artificially excluded by family.
- Trace Retraced Path and GL Salvo are baseline10%; shotgun First In Last Out and glaive Nezarec’s Whisper are baseline20%. Linear fusion Stormchaser is baseline10%, not the ordinary Fusion Rifle exception.
- The 3s / 60tick refill cooldown is source-supported, but its owner-wide versus per-instance scope is unproven. Master chose owner-wide60ticks as an explicitly local policy; that choice is not promoted to a source claim.
- These are BASE energy chunks. D2 ability-tier and Armor3.0 grenade-stat scalars are not implemented. Master’s flat percent of the authored Minecraft grenade base cooldown is an explicitly local adaptation; do not derive current D2 scalars from Minecraft cooldowns.
- Clarity’s scalar blog warns partly outdated; Character-Stats README says severely outdated and not to use. No present-day scalar curve is guessed.
- Snapshot is official manifest `245114.26.10.13.2000-1-bnet.66137`, matching W40/W60/W62 JSON components. No cached SQLite found in inspected /tmp/run caches; no SQLite provenance claim.

## Reproduction

```sh
rtk proxy python3 scripts/extract_demolitionist_w103.py --verify
```

Generator and generated resource/reference JSON are frozen. No Java build, game/CU/native input, commit, or push performed by this worker. Eight targeted query strings total; no further numeric searches. Child-agent and direct sub-agent messaging tools unavailable in this worker environment; master must relay this exact contract to test lead.
