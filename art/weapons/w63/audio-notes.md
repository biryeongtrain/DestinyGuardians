# W63 reload audio resources

The current 63-entry resource catalog yields 50 full-magazine base entries and 11 supported non-shell Outlaw variants (61 unique id/ticks rows). Deduplication by sourceEvent + ticks produces 53 Ogg assets/events. All 99 previous sounds.json key/value definitions are preserved.

Runtime resource: `src/main/resources/destiny/sounds/w63-reload.json`. Exact schema:

```json
{"stage":"W63","entries":[{"id":"weaponCatalogId","ticks":59,"event":"weapon.reload_w63.weapon.hand_cannon.reload.59","sourceEvent":"weapon.hand_cannon.reload","sourceSha256":"<W33 Ogg SHA-256>","asset":"assets/destiny/sounds/w63/reload/weapon_hand_cannon_reload_59.ogg"}]}
```

`id` is the catalog weapon ID, never a mode suffix. Lookup uses (id, actual captured full-magazine phase ticks); there is no duplicate id/ticks. Base ticks come from W46 after respecting WeaponReloadPolicy: canonical Long Arm is incremental even though W46 still lists a whole-magazine estimate. Outlaw firstTicks comes from W62 only for its 11 eligible full-magazine entries. The two shell Outlaw entries are excluded. WeaponCycle captures firstTicks at reload start; expiry of Outlaw does not retime an active clip. Runtime lifecycle, cancellation, emitter behavior and fallback are integrated separately by the main task.

`sourceEvent` follows DestinySounds.weaponKey exactly: choose a present weapon-ID reload event, otherwise family.reload. Named aliases share W33 family-file bytes but retain distinct sourceEvent/ticks deduplication identity. `sourceSha256` pins the consumed W33 Ogg bytes, not the original WAV/MP3; original hashes, URLs, trims, confidence and limitations are in the audio manifest. No original source cache is read. Event names contain only lowercase letters, digits, dots and underscores.

Processing decodes the hash-verified W33 Ogg to mono float32 at 32000 Hz. Tempo = decoded source sample count / target sample count, factored into atempo stages between 0.5 and 2.0. apad=whole_len and atrim=end_sample set exactly ticks*1600 samples, then libvorbis q4 encodes with one thread, stripped metadata/chapters and bitexact flags. Playback pitch must remain 1.0. There is no asetrate, resampling-based pitch shift, boost or new download.

Offline validation: container EOS granule is within 1 sample of ticks/20; decoded PCM tolerance is 1024 samples (0.032 s) for Vorbis long-block overlap. Observed maximum decoded delta: 0 samples. All outputs are mono 32000 Hz Vorbis, non-silent, finite, zero clipped samples; worst sample peak -4.916159 dBFS (required <= -1 dBFS). The manifest records each duration, hash, peak, RMS and filter.

Commands (no Gradle):

- `rtk proxy python3 scripts/audio/build_reload_sounds_w63.py --verify`: offline/read-only, no mkdir, temporary files, encoding or writes; checks pins, coverage, definitions, hashes and decoded PCM.
- `rtk proxy python3 scripts/audio/build_reload_sounds_w63.py --check`: runs verification, regenerates every Ogg twice in a private system temporary directory and compares bytes with repository assets; compares regenerated config/manifest/notes and sound definitions too. No repository writes.
- `rtk proxy python3 scripts/audio/build_reload_sounds_w63.py`: renders in private temporary storage, then publishes only owned W63 paths and appends missing sound events. Existing W63 mismatches fail instead of replacing old events.

The cached W33 ffmpeg 7.1 binary is hash-pinned; `--ffmpeg` may supply an identical local binary. The manifest pins the generator itself and all consumed repository inputs. Sound definitions are pinned as an original-event snapshot and selected-event subset; the whole evolving sounds.json file is deliberately not hashed. A drifted policy/source requires review before changing pins.

## Evidence limits

- W46 historical community reload curves and W62 Outlaw timings are the current server's authored/approximate durations, not official original-game measurements.
- Original animation endpoint, ammo insertion endpoint, acoustic endpoint and any original post-insertion tail have unknown equivalence. W63 fits the entire already-trimmed W33 clip to the server phase; it establishes no original endpoint semantics.
- Family representatives remain representatives; exact event aliases identify only the documented named uploader source, not independently verified per-weapon acoustic identity. Apostate still uses the sniper family source with W33's unverified Aprostate identity.
- Pitch is preserved algorithmically by ffmpeg atempo at a fixed sample rate. Time stretching can change transients; final apad/atrim handles sample rounding and algorithm tail differences. No new silence analysis, action segmentation, looping, concatenation or loudness boost is applied.
- W33 authorization and provenance are inherited. No new download or redistribution permission is inferred. Original private source files are neither required nor published.
- These are offline resource/PCM checks only. No native playback, original-game animation synchronization, acoustic-output proof or independent audition is claimed.
- Shotguns, canonical Long Arm, bows, swords and every incremental reload are excluded. A full reload source must never stand in for a single-shell insert.
