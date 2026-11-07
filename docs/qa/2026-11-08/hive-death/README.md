# W344 species-specific Hive death dissolves

Source: read-only `Downloads/Destiny-Hive-Death-SFX-Comparison-2026-11-08`. The supplied manifest identifies **ordinary Hive death dissolve** events, not confirmed headshot-only sounds. soft/hard are preserved source labels; they are not relabeled as body/headshot. No Taken weakspot sound is substituted for ordinary Hive.

## Mapping

| Actor | Source unit | Default ordinary-death event | Separate optional event |
| --- | --- | --- | --- |
| Thrall | thrall | death.thrall.soft | death.thrall.hard |
| Acolyte | trooper | death.trooper.soft | death.trooper.hard |
| Knight | knight | death.knight.soft | death.knight.hard |
| Wizard | wizard | death.wizard.soft | death.wizard.hard |

Each unit has 5 soft and 4 hard variants: **8 events, 36 files**. Defaulting ordinary deaths to soft is an authored Minecraft playback choice, not a recovered original damage selector. Hard is available as the explicitly separate `death_hard` route; it is not triggered automatically by precision classification. Both use the existing shared death gain **0.35**, normal playback pitch, and strike-owned positional listeners. No damage/health/precision calculation or death lifecycle changes were needed. Existing `DevilsCombatSounds.stop` automatically includes all new routes.

The previous Knight movement substitute for Thrall/Acolyte/Wizard and the Knight's old movement death route are replaced by species-correct dissolve events. Their obsolete approximation entries are removed. Headburst and other species remain on their existing mappings.

## Source and conversion

All 36 original WAV/OGG pairs match the supplied SHA-256 list. Event/bank/WEM/media-id/package/patch and the source README's semantic limits are retained under `art/audio/hive-death-w344/`. Downloads files are unchanged. The full-length stereo sources are converted to positional mono at their original sample rate with `0.5*L + 0.5*R`, Vorbis q5, metadata stripped, one thread and bitexact flags. Each is fully decoded, checked non-silent/mono and within 256 samples of its original frame count. No trimming, normalization or pitch change is performed. Derivatives total **1,713,355 bytes**. One equal-weight variant is selected per Minecraft event; original Wwise random weights/history and final mixing are not reconstructed.

`audio_variant_common.py` shares the exact conversion path with the W343 importer. W343's existing 40 outputs were verified unchanged; both importers support `--verify` for source and output hashes.

## Validation boundary

Targeted units verify 8 events / 36 mono variants, separate soft/hard routes and honest non-headshot metadata, plus previous headburst and death assets. The two real server GameTests create accepted encounter-owned Hive actors with actual models and damage, verify one species-correct death cue and no repeat after death, and verify all four optional hard events separately. This is server/packet coverage, not native client or speaker A/B acceptance. The QA AutoHost configuration is restored to its original bytes and owned servers are stopped.

Build, actual client-pack contents/size, matching cache measurements and artifact hashes are recorded beside this file. Existing unrelated changes are preserved.

Final checks: **14 unit tests and 2 real server GameTests passed**, including accepted damage deaths for all four Hive species and distinct hard-event packet checks. Gradle assembled the actual W344 JAR. The normal isolated server generated a matching cache once (116.5 s readiness) then restarted without generation (13.1 s readiness, 1807 ms restoration). Both servers exited 0; owned port 25630 is closed. The actual client ZIP is **191,661,837 bytes**, under 250 MB. All 36 Hive OGGs were verified byte-for-byte inside that ZIP, and all 8 event definitions are semantically identical after Polymer formatting. Extract the matching W344 companion into the server root.
