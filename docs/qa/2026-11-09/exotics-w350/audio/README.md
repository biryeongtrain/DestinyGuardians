# W350 exotic action audio

This isolated worker imports source-derived audio for Crimson, Thorn, Outbreak Perfected, Sunshot, Graviton Lance, Jotunn, Gjallarhorn, Whisper of the Worm, and Tractor Cannon. Each of equip, ADS, reload and fire maps to one selected source variant. There are no random variant pools.

## Selection and provenance

`art/weapons/w350/audio/folder-discovery.json` preserves the connector's supplied folder listings, Drive IDs, original names, file lengths and URLs. `source-selection.json` explains each choice; `source-pins.json` pins original SHA-256 and private cache paths. Originals were downloaded from the supplied public Drive files into read-only files outside Git. They were not edited or replaced with synthetic recordings.

The default selection is the lowest numbered uploader-labeled normal action (`Draw_1`, `ADS_1`, `Reload_1`, `Fire_1`) or the sole named action. Tractor uses its labeled switch-in and reload. Multi-fire, loops, catalyst variants and extra alternative source families are not randomly selected.

Three mappings require explicit qualification:

- Graviton ADS reuses its selected `Draw_1` asset as a handling approximation.
- Tractor ADS reuses its selected `TC_Switch_in_1` asset as a handling approximation.
- Tractor fire selects opaque `023D-000005F0.mp3` provisionally after reviewing all eight candidates' waveform/spectrogram. Its transient and low-frequency decay suit an attack cue, but do not prove normal-fire versus impact/effect identity. Source identity and limitations remain explicit in the manifest.

`candidate-review/` contains compact waveform/spectrogram sheets and metadata for every opaque Tractor and Graviton candidate. Independent acoustic identification remains pending.

## Conversion and verification

`scripts/audio/build_exotic_sounds_w350.py` verifies pinned originals and the FFmpeg executable before conversion. It decodes the full source, downmixes to mono at 48,000 Hz, applies the existing conservative RMS/peak gain policy, and encodes Vorbis quality 4. Base recordings have no silence trim, tail cap, added fade, concatenation, looping, pitch shift or time stretch. MP3 frame/container duration and decoded duration are recorded separately.

The generated manifest records original/output hashes, file lengths, sample rate, channels, duration, gain, decoded peak/RMS and clipped sample count. Every output was decoded with FFmpeg; nonfinite/empty audio, clipping, unexpected channel/rate, or a changed source hash fails the import. Base OGG final-granule duration must match the entire resampled source within one sample. FFmpeg raw Vorbis decoding can differ by one codec block through priming/padding; the measured delta is recorded explicitly rather than silently trimming or padding a base recording.

Final dataset: 36 action mappings, 34 unique OGG files, 880,413 bytes. All decoded samples are finite; decoded clipping is zero; highest decoded peak is -5.057546 dBFS. Unretimed Vorbis decoder sample deltas range from -128 to +928 at 48 kHz, while full container duration checks passed. Every timed reload decodes to the exact target sample count.

The nine reload targets from the master are Crimson 48 ticks, Thorn 55, Outbreak 40, Sunshot 45, Graviton 36, Jotunn 49, Gjallarhorn 67, Whisper 62, and Tractor 91. The generator consumes the entire original PCM with pitch-preserving `atempo`, adjusts only the tempo factor to fit its processing window, and adds 2–768 silence samples (at most 16 ms) to reach the exact 20 Hz tick duration. No source or processed samples are trimmed. Full-duration normalized reload references remain outside the pack at `/tmp/exotic-expansion-20261109/audio-full-duration/`, with hashes and metadata retained in `manifest.json`. The pack contains one timed reload file per weapon.

## Integration and remaining acceptance

Merge `sounds-json-snippet.json` into the central sound registry; the worker does not edit it. It contains 36 base action events, nine timed reload events, and 288 direct channel aliases, each with exactly one sound entry. Approximation ADS aliases reuse the selected equip file. Each base reload event and all its timed/direct aliases point to the same single OGG. Append `reload-profile-snippet.json` to the W350 definitions; its nine entries have `id,ticks,event,sourceEvent,sourceSha256,asset`. `sourceSha256` pins the unretimed normalized reference OGG; `sourceOriginalSha256` in the manifest separately pins the original MP3. Master-requested boosted durations reuse the base cue, with no additional alternate recordings.

No client, server, build, Computer Use, audio playback or speaker listening ran in this worker. Source labels do not establish acoustic fidelity. In-game timing, positional attenuation, cancellation, perceived loudness and playback output remain unverified. Full native fire recordings may include a pulse burst or Jotunn charge/discharge; runtime dispatch must respect the action represented instead of assuming every source is a single isolated projectile sound.
