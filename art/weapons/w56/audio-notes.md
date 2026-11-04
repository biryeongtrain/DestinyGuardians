# W56 named-source sword audio

15 events, 51 unique Ogg Vorbis clips, 1,379,198 bytes (1.315 MiB), 165.666188 seconds total. Each file is mono at 32,000 Hz, libvorbis quality 4. Individual durations are 1.097156–6.794094 seconds. Decoded sample peaks are at most −5.4457 dBFS (at least 5.4457 dB headroom); zero clipped samples. RMS varies from −30.4846 to −20.9742 dBFS because the −6 dBFS PCM peak ceiling takes precedence over the −21 dBFS RMS aim.

**No native/game audition or acoustic listening has been performed.** Numerical verification does not establish acoustic fit, exact weapon identity, runtime synchronization, spatial mix, or intersample true peak. The main integration owns runtime code, tests, language additions, shared definitions and the final gate.

## Runtime handoff

Both `art/weapons/w56/audio-manifest.json` and `src/main/resources/destiny/sounds/w56.json` contain the same complete provenance manifest and a **`soundDefinitions` object** ready for main to merge into `src/main/resources/assets/destiny/sounds.json`. The importer never performs that merge. Paths below the `destiny` namespace are `w56/<event with dots replaced by slashes>_<variant>.ogg`, rooted at `src/main/resources/assets/destiny/sounds/`.

Each event selects one equal-weight variant; every variant has `stream: false` and `attenuation_distance: 32`. All light and empty-light events reuse `subtitles.destiny.weapon.sword.fire`. Main adds these subtitle keys to its language tables: `subtitles.destiny.weapon.sword.guard`, `subtitles.destiny.weapon.sword.heavy`, `subtitles.destiny.weapon.sword.impact`. Uppercut, heavy, heavy-air and caster release use the heavy subtitle. Existing `weapon.sword.fire` and all other pre-W56 definitions remain unchanged.

| Event | Uploader folder | Exact named subset | Clips | Subtitle suffix |
| --- | --- | --- | ---: | --- |
| `weapon.sword.light` | Half Truths | `Light_Att_1..4.mp3` | 4 | `fire` |
| `weapon.sword.uppercut` | Half Truths | `Heavy_Att_1..4.mp3` | 4 | `heavy` |
| `weapon.sword.guard` | Half Truths | `Guard_1..3.mp3` | 3 | `guard` |
| `weapon.falling_guillotine.light` | Falling Guillotine | `Swing_Reg_1..4.mp3` | 4 | `fire` |
| `weapon.falling_guillotine.heavy` | Falling Guillotine | `Tornado_Swing_1..4.mp3` | 4 | `heavy` |
| `weapon.falling_guillotine.guard` | Falling Guillotine | `Guard_1..3.mp3` | 3 | `guard` |
| `weapon.crown_splitter.light` | Throne Cleaver / Crown Splitter | `Light_Att_1..4.mp3` | 4 | `fire` |
| `weapon.crown_splitter.heavy` | Throne Cleaver / Crown Splitter | `Heavy_Att_1..3.mp3` | 3 | `heavy` |
| `weapon.crown_splitter.heavy_air` | Throne Cleaver / Crown Splitter | `Heavy_Air_Att_1..3.mp3` | 3 | `heavy` |
| `weapon.crown_splitter.guard` | Throne Cleaver / Crown Splitter | `Guard_1..3.mp3` | 3 | `guard` |
| `weapon.temptation_s_hook.light` | Temptations Hook | `Swing_1..4.mp3` | 4 | `fire` |
| `weapon.temptation_s_hook.empty_light` | Temptations Hook | `Swing_No_Ammo_1..4.mp3` | 4 | `fire` |
| `weapon.temptation_s_hook.guard` | Temptations Hook | `Guard_1..2.mp3` | 2 | `guard` |
| `weapon.sword.caster.release` | _Caster_Frame | `Caster_Swing_Far_1..2.mp3` | 2 | `heavy` |
| `weapon.sword.caster.impact` | _Caster_Frame | `Caster_Proj_Exp_Close_1..4.mp3` | 4 | `impact` |

Source actions are selected solely by uploader folder and filename evidence. Half Truths is a **proxy for Abide the Return / Goldtusk**; no exact match is asserted. The Crown Splitter folder is **shared with Throne Cleaver**, and individual clip identity remains unresolved. Generic caster **far-swing release is a candidate, not an exact near layer**; close projectile explosion labels support an impact candidate. Falling Guillotine and Temptations Hook retain their named uploader identity without independent listening verification. No unsheath, swirly, distant explosion, numeric, or additional variant files were imported.

## Original sources and deterministic processing

The previously fetched live public Drive listings are preserved privately as the six `<folderid>.json/.html` pairs in `run/private-sources/w56/`. `docs/qa/2026-10-24/w56/audio/source-discovery.json` captures the complete public listing rows, selected subsets, parent relations and listing hashes. `source-pins.json` pins all 51 direct public `uc?export=download&id=...` originals by Drive ID, filename, size and SHA-256; first-download response MIME type and public redirect URL are also saved. Listing size was checked at acquisition. The source bytes total 4,536,150. Originals remain in the ignored private tree; no original audio is embedded in QA or previews. Only the intended user-authorized Oggs are distribution assets; public availability is not treated as a separate redistribution license.

The importer pins those two evidence files and `shared-baseline.json` by SHA-256. W33's existing `decode`, `stats` and ffmpeg-location helpers are loaded with bytecode disabled; its importer entry point is never called. The saved W33 helper hash is checked before import. The installed bundled ffmpeg is `run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1`; its version string and binary SHA-256 are saved in both manifests.

Processing decodes the entire original to mono float32 at 32 kHz. Only edge silence below −72 dBFS in 10 ms RMS blocks is eligible for removal, retaining 30 ms before and 200 ms after active blocks. Trimming is capped at 200 ms leading and 350 ms trailing per clip. 41 clips had some edge silence removed, totaling 7.05615625 seconds; all start/end sample indices and original/output measurements are saved. There is no hard duration crop, fade, retiming, pitch shift, stretching, concatenation, looping, or invented action segmentation. Sources over eight seconds fail rather than being cut.

Scalar gain aims at RMS −21 dBFS, with PCM peak ≤−6 dBFS and boost ≤12 dB, whichever permits less gain. The encoder uses one thread, libvorbis q4, mono 32 kHz, metadata/chapters removed, and bitexact flags. Only generated codec/vendor and encoder identification comments remain. Each encoded output is decoded again; sample peaks must remain ≤−1 dBFS with zero clipping. A maximum of three encodes may reduce gain to correct lossy overshoot; no clip needed that correction here. Each output SHA-256, byte count, codec header, exact decoded sample count, RMS and peak are in the manifests.

Finite limits: exactly 15 events / 51 clips, originals ≤32 MiB each, action duration ≤8 seconds, total Ogg budget 8 MiB, download timeout 45 seconds, encode timeout 30 seconds. Verification and deterministic checking never download. No original is substituted or re-pinned automatically.

## Commands and evidence

Run from the repository root; every shell command starts with `rtk`:

```sh
rtk proxy python3 -B scripts/audio/import_sword_sounds_w56.py --verify
rtk proxy python3 -B scripts/audio/import_sword_sounds_w56.py --check
rtk proxy python3 -B scripts/audio/import_sword_sounds_w56.py --offline
```

`--verify` is read-only and offline: evidence hashes, private original SHA pins, all 51 output hashes and fresh decode measurements, action subsets, channel/rate, metadata, full trimmed action sample counts, sidecar equality, gain/trim records, and the existing shared baseline. New shared keys from main are allowed; previous values are immutable. The baseline covers 84 pre-W56 sound definitions, 68 file hashes (existing sound manifests, audio scripts and referenced Oggs), and existing entries in two language tables. `--check` first verifies, then encodes every clip twice into private temporary storage, requiring all 102 results to match the saved output hashes, and removes that temporary storage. `--offline` rebuilds only owned W56 asset/manifest/measurement/preview outputs using the pinned cache. Optional `--fetch` can restore missing originals only when the downloaded bytes match existing pins; it cannot accompany verification/checking.

QA artifacts are under `docs/qa/2026-10-24/w56/audio/`: `source-discovery.json`, `source-pins.json`, `shared-baseline.json`, `measurements.json`, `determinism.json`, `verification.json`, and `audition.html`. The standalone HTML has 51 individual browser audio controls, no autoplay, no scripts or external dependencies, and relative URLs directly to the current resource Oggs. It was inspected structurally without opening a native app or playing audio. The user can review it manually after this handoff.

No `sounds.json`, language file, existing manifest/script, runtime file, test or main-owned file was edited. No reset, commit, push, Gradle invocation, native app launch or audio playback was performed.
