# W270 class/jump audio handoff

## Integration contract

Owned delta only. No main checkout edits, runtime changes, alias definitions, client/server launch, build, or commit. Import 11 mono Vorbis files and merge the 11 root events from `sounds-fragment.json`; preserve the existing registry and check collisions before merge.

- Manifest: `docs/qa/2026-10-30/w270/audio-import.json`; schema `1`; SHA-256 `2c2f4cdc7956acc10d68b3602c5919f3238ca89ffab051565c7c6b25ff56ca8a`.
- Fragment: `sounds-fragment.json`; SHA-256 `d7f1c9db0adc28daa04a9efb92a087b7be4bdebcf8063fdcd9458de79f9deaab`.
- `entries` is the per-output array. Required integration fields: `output` (resource-root-relative `assets/destiny/sounds/...ogg`), `sha256` (output file SHA-256), `bytes` (output bytes), `event` (unprefixed event key). `path` is delta/repository-relative and includes `src/main/resources/`; `resource` is the `destiny:` sound resource identifier.
- Each entry also includes canonical OGG/raw WEM/BNK/sound.bin source paths and SHA-256s, source tag, sequence timing evidence, decoded PCM duration and peak, gain, playback recommendation, approximation, and verification flags.
- Top-level `fragment` contains path/hash/keys; `summary` contains counts/bytes/peak; `banks` contains partial HIRC inspection. Output SHA-256s are not source hashes.
- Master owns ReviewedAudioW234 pinning, fragment merge, 32 owner-slot aliases, and entity-attached playback. No `.sustain` keys or alias definitions are supplied.

## Runtime timing recommendations

All values below are decoded output lengths at pitch 1.0, not ability durations or scheduling delays. Preserve the original attack/tail; do not wait for an audio file to end before advancing gameplay. Offsets are 0 seconds relative to the semantic events below as a port recommendation. Source sequence `start=0` does not establish a keypress-relative or FBX-relative time, and source sequence `duration=0` does not mean zero-length audio.

| Event | WEM tag | Decoded seconds | Trigger |
|---|---|---:|---|
| `class.hunter.dodge.gambler` | `80D66B88` | 1.709771 | Accepted gambler dodge activation; once at the motion start. |
| `class.hunter.dodge.marksman` | `80D665BA` | 1.393000 | Accepted marksman dodge activation; once at the motion start. |
| `class.warlock.rift.precast` | `80D665A0` | 0.946792 | Accepted rift cast start; once, before field creation. |
| `class.warlock.rift.healing` | `80D665A3` | 2.836917 | Actual healing field creation; once at field position. |
| `class.warlock.rift.empowering` | `80D66BAB` | 4.551146 | Actual empowering field creation; once at field position. |
| `class.warlock.rift.end` | `80D665A6` | 3.488979 | Actual field removal/expiry; once at field position, only if a field existed. |
| `jump.hunter` | `80D64F18` | 1.941333 | Each accepted airborne extra jump; not the grounded vanilla takeoff. |
| `jump.blink.out` | `80D64F24` | 2.133333 | Successful blink departure; once at the departure position. |
| `jump.blink.in` | `80D64F27` | 2.299583 | Successful blink arrival; once at the arrival position. |
| `jump.warlock.glide` | `80D64D68` | 2.387313 | Glide inactive-to-active transition; entity-attached, finite once; stop owner slot on exit. |
| `jump.titan.lift` | `80D650F3` | 3.612062 | Lift inactive-to-active transition; entity-attached, finite once; stop owner slot on exit. |

Rift: precast follows accepted cast start, healing/empowering follows actual field creation, and end follows actual removal. Choose healing or empowering according to the actual rift type. Do not add an arbitrary 0.95-second precast timer or emit field/end audio for a cast cancelled before field creation.

Blink: play out at the departure location and in at the successful destination at the runtime transition boundaries. Their two-second tails do not define the teleport gap. Avoid attaching the departure tail to an entity that immediately teleports.

Glide/lift: finite once per inactive-to-active transition, attached to the player through the master-owned slot event. Never replay per tick or at sample EOF. Stop only that owner slot on cancel, landing, death, disconnect, replacement or slot reuse; reset ownership before reuse. No sustain or separate jump-end sound is supplied. If the activation lasts longer than the representative, the remaining interval is intentionally silent. Prevent duplicate start playback from state refreshes.

## BNK HIRC evidence and limits

Both movement banks are Wwise version 150 with 35 HIRC objects. The script validates chunk and object bounds, sound source IDs, event action lists, action targets, and unique random/sequence footer layouts including child IDs, playlist IDs/weights, loop count, transition mode and continuous flag. Switch routing, RTPC behavior and media-ID-to-package-tag binding are not fully decoded. Parser layout reference: https://github.com/bnnm/wwiser/blob/master/wwiser/parser/wparser.py (`CAkRanSeqCntr__SetInitialValues`, `CAkRanSeqCntr__SetPlaylistWithoutCheck`, `CAkBankMgr__LoadSource`); the importer is self-contained and makes no network requests.

**Glide `80D4B295`:** entry event `AF7A7E7C` calls action `10B1E7FF` (type `0403`) targeting `201B44D9`. Sequence `2A37EE3D` lists random container `1E243043`, then continuous loop container `27896C8B`. The former has three source IDs (`256AAB63`, `0FD5B735`, `2AC358C1`), loop count 1, random mode; the latter has loop count 0 (unlimited), transition mode 4 (sample accurate), continuous flag, and source ID `299BCFB7`. Another switch branch repeats this pattern (`37859BF4`, `22F88FC7`, `39D74A59`). Additional three-source random containers use different IDs. Sequence transition mode 5 (trigger rate) stores 300 ms; this is a container parameter, not a proven ability start-to-sustain delay.

**Lift `80D4B4C0`:** entry event `F982FC8F` calls action `22A3A5C1` (type `0403`) targeting `3008B774`. Continuous sequence `2BA7186F` lists three-source random container `0F1BEDD7`, then loop container `30DA8690`. Sequence `30795CAF` has the opposite listed ordering (`0B41D169`, `3178B6F0`), reinforcing that flattened WEM lists cannot be randomized safely. The loop containers have loop count 0, sample-accurate transitions and media ID `299BCFB7`. Source IDs in the random branch are `138A2ACF`, `2A94E3D8`, `17F51CB7`. Additional three-source random containers use different IDs. Gameplay switch selection is unresolved.

**Decision:** there is structural evidence of an internally looping branch. Both exported WEM sets share only `80D64E8E` (7.383979 s), suggesting a binding to the common `299BCFB7` media ID, but no explicit ID-to-tag map was delivered. No looping WEM or sustain event is imported from that inference. Glide `80D64D68` and lift `80D650F3` are confirmed members of their classified banks, selected as conservative finite representatives. Their precise start-versus-end roles remain unresolved; neither is certified as the exact original start layer. The selected samples are not randomized with the other six.

Other events also use one representative each. Names/sequence references establish event classification, not full Wwise random/layer/switch behavior. Marksman `80D66B77` is not imported as a random variant: its bank contains an additional separate sound/action branch. No uncertain barricade, thruster, Phoenix Dive, acrobat, or candidate banks are imported.

## Processing and checks

- 11 files / 11 root events; total 261,649 bytes (255.52 KiB). Mono, 48 kHz, libvorbis quality 4.
- Explicit downmix `0.5*L + 0.5*R`; attenuation only, target -4 dBFS, verify decoded peak at or below -3 dBFS. Highest measured output sample peak: -3.031190 dBFS. This is not true-peak/loudness certification.
- Every source OGG decoded to EOF; every result decoded in memory and again from the written file to EOF with FFmpeg error-fatal mode. All PCM finite. Vorbis identification verifies one channel and 48 kHz. Sample counts checked against decoded sources. Each output independently re-encoded and compared byte-for-byte.
- All 393 supplied manifest hashes verified. All 394 source files hashed before and after; no source drift. Each selected OGG and raw WEM also matches `audio-conversion.json` hashes.
- Supplied canonical OGGs are already derived from Opus WEMs; this adds a mono Vorbis encode. No trimming, looping, time-stretch or guessed attack placement. Source precast metadata reports 0.952125 s while the canonical OGG decodes to 0.946792 s; the output preserves that decoded source length, with no manual shortening.
- The `first_sample_above_minus60_dbfs_seconds` fields are measured sample-threshold crossings, not perceptual or animation onset markers.
- Main sounds.json before integration had none of these 11 keys; read-only baseline SHA-256 was `7f472641829f25a3ceba0ce8f764e79cb231576e1d17e24734099c2c4d77af2b`. Master may modify it concurrently; do not overwrite it from this delta.
- No listening, vanilla-client attenuation, owner-stop, resource-pack runtime, animation alignment, or server/gameplay QA was performed. Those remain master integration checks.

## Reproduction

Run from any directory; writes are limited to selected owned assets, root fragment and manifest. Use an isolated output root; main checkout and source-overlapping roots are rejected. Exact byte reproduction requires the FFmpeg binary recorded in the manifest.

```sh
rtk proxy python3 /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1/w270-delta/scripts/audio/import_class_jump_w270.py \
  --output-root /Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1/w270-delta \
  --ffmpeg /tmp/w262-audio-research-tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1
```

Importer source and this analysis are handoff files; the importer regenerates the OGGs, fragment and JSON manifest. It does not regenerate this analysis or edit any sound registry.
