# W342 PvE combat balance and enemy death audio

User-requested Minecraft tuning, not recovered Destiny combatant HP or current original-game damage values. Weapon body damage, head multipliers, range curves and timing remain on their existing paths.

## Resulting tuning

| Enemy / damage category | Before | After |
| --- | ---: | ---: |
| Dreg HP (campaign and strike) | 20 | 11 |
| Thrall HP | 14 | 11 |
| Acolyte HP | 24 | 11 |
| Shank HP (campaign / strike) | 14 / 16 | 10 |
| Devil's Lair Walker core | 1600 | 200 |
| Each Walker leg armor pool | 100 | 12.5 |
| Sepiks HP | 2200 | 550 |
| Shared PvE ability multiplier | 1 | 3 |
| Shared PvE super multiplier | 3 | 10 |

Unbuffed rapid-fire auto rifles are the limiting frame: 5.7375 applied precision damage per in-range bullet, so two shots kill 11 HP minors while one does not. Every bundled auto rifle frame is checked against those pools. A 4-base direct ability now deals 12 PvE damage; an 11-base roaming-super light hit deals 110, covering even the ordinary Captain's 80 HP + 24 shield. Damage-over-time and continuous beams retain their individual tick cadence. PvP conversion is still excluded from this PvE scaling. Immunity, Sepiks shield phases and Walker multipart deduplication remain in their existing paths.

## Audio

A shared enemy mix lowers normal strike combat packets to 0.55, death to 0.35, pain to 0.25 and impacts to 0.45. Campaign Fallen weapon, bark, movement and heavy sound categories are also quieter; death vocals use 0.35. Original recordings are unmodified and full length.

Strike Dreg/Vandal/Captain death routes now use the already-shipped species death vocals. Marauder uses the Vandal vocal, explicitly marked as a family approximation. Thrall/Acolyte/Wizard lacked death routes; they use the already-shipped **Hive Knight death movement** cue, explicitly marked as a shared Hive approximation, not an extracted exact species death vocal. Every strike species now has a valid bundled death event. Lethal damage no longer queues an extra pain cue after the death callback. Neutral removal still uses the existing discard path.

## Verification scope

Targeted unit coverage includes all Devil's Lair unit suites, all auto frame two-headshot checks, shared PvE/PvP category boundaries, campaign archetypes and routed sound resources. The bounded server batch checks actual accepted actor damage, precision classification, death callback counts, quieter outgoing sound packets, Walker region accounting, Brig armor, and Sepiks thresholds/completion. It does not certify native aim input, visual presentation, sustained FPS/TPS, or speaker loudness.

Initial checks exposed outdated test assumptions: the old Walker threshold was expressed as fixed 300 HP; the old archetype test assumed Shank was weaker than Dreg. The updated values preserve that role order and express the Walker fixture threshold relative to its new pool. Initial server checks also caught fixture setup ending before the Knight's spawn and an untagged legacy test hit receiving the new ability multiplier. Those fixtures were corrected without relaxing the requested damage outcomes.

Detailed results, matching artifacts and isolated cache boot measurements are recorded beside this file.

Final checks: **131 unit tests and 5 real server GameTests passed**. Actual damage confirmed the two rapid-auto headshots, direct basic ability kill, light-super Knight kill, one death callback per minor and no pain cue on the lethal hit. All 13 strike species sent a 0.35-volume death packet. Brig armor, reduced Walker multipart pools and Sepiks shield/completion checks passed. The production JAR was assembled by Gradle, then booted from its own isolated normal-server setup: fresh matching cache ready in 112.5 s, subsequent cache hit in 14.1 s with 1967 ms restoration and no generation. Both servers exited 0. The client resource pack remains 188,236,924 bytes; the W342 companion bundle is 200,294,514 bytes. Extract the matching companion into the server root. Raw runtime fixture configs were restored and port 25630 closed.
