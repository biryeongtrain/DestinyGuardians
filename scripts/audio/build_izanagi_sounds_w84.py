#!/usr/bin/env python3
"""Offline W84 audio sidecar. No shared manifest/resource edits or playback.

rtk proxy python3 -B scripts/audio/build_izanagi_sounds_w84.py [--verify]
    [--normal-ticks 61] [--special-ticks 61]
--verify regenerates in disposable temporary storage and compares exact bytes.
Only user-authorized, locally cached, SHA256-pinned recordings are accepted.
61 ticks is confirmed simulation policy, not exact observed Destiny timing.
"""
from __future__ import annotations

import argparse
import array
from collections import defaultdict
import hashlib
import html
import importlib.util
import io
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import wave

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "art/weapons/w84/audio"
PRIVATE = ROOT / "run/private-sources/w84"
PACK = ROOT / "src/main/resources/assets/destiny/sounds/w84/izanagis_burden"
RELOAD_PACK = PACK.parent / "reload"
PREFIX = "weapon.izanagis_burden."
FOLDER_ID = "1X4uYm_HbymReNWlq6OTD433xU6jhzwNC"
HELPER_PATH = ROOT / "scripts/audio/import_sounds_w33.py"
HELPER_SHA256 = "e3f1dd846b69dcb5a5cad685f310ffb9a6b6a7d1ab7fbc1d11851557bca6911e"
FFMPEG_PATH = ROOT / "run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
FFMPEG_SHA256 = "6d175a4743ca50256e89a8cdd731100f9cee33bd79aeea46894d209410dc6617"
ACTION_PATTERNS = {"fire": r"Fire_Reg_(\d+)\.mp3", "reload": r"Reload_(\d+)\.mp3",
                   "honed_fire": r"Fire_Honed_(\d+)\.mp3", "honed_reload": r"Reload_Honed_(\d+)\.mp3"}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def enc(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def checked(path, expected):
    require(path.is_file(), f"Missing pinned input: {path}")
    require(sha(path.read_bytes()) == expected, f"SHA256 mismatch: {path}")
    return path


def load_inputs():
    checked(HELPER_PATH, HELPER_SHA256)
    checked(FFMPEG_PATH, FFMPEG_SHA256)
    spec = importlib.util.spec_from_file_location("w84_w33_audio_helpers", HELPER_PATH)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    pins = json.loads((ART / "source-pins.json").read_text())
    discovery = json.loads((ART / "folder-discovery.json").read_text())
    require(discovery["folderId"] == FOLDER_ID, "Unexpected source folder")
    require(discovery["sourceRoot"] == helper.ROOT_FOLDER, "Unexpected authorization root")
    listed = {row["id"]: row for row in discovery["rows"] if row["selected"]}
    require(len(pins) == len(listed) == 10, "Source selection changed; review named source evidence")
    require(len({p["id"] for p in pins}) == len(pins), "Duplicate Drive source ID")
    for pin in pins:
        match = re.fullmatch(ACTION_PATTERNS[pin["action"]], pin["originalName"])
        require(match is not None and int(match[1]) == pin["variant"], "Action/variant disagrees with uploader label")
        row = listed[pin["id"]]
        require(row["name"] == pin["originalName"] == pin["uploaderLabel"], "Uploader label drift")
        require(row["parents"] == [FOLDER_ID] and row["mime"] == "audio/mpeg", "Source outside named folder")
        require(pin["folderId"] == FOLDER_ID and pin["folder"] == discovery["folder"], "Source folder drift")
        source = ROOT / pin["privatePath"]
        require(source == PRIVATE / (pin["id"] + ".mp3"), "Source outside W84 private cache")
        checked(source, pin["sourceSha256"])
        require(source.stat().st_size == pin["bytes"] == row["bytes"], "Source byte length drift")
    return helper, pins, discovery


def transform(helper, source, target):
    """W33 silence/gain/fade policy, retaining each complete labeled action tail.

    Unlike W33's family-fire policy, no three-second hard cap is applied here.
    No time stretch, pitch change, layering, looping, or semantic segmentation.
    """
    rate = helper.RATE
    original = helper.decode(str(FFMPEG_PATH), source)
    hop = rate // 100
    envelope = [math.sqrt(sum(x * x for x in original[i:i + hop]) / len(original[i:i + hop]))
                for i in range(0, len(original), hop)]
    threshold = max(10 ** (-58 / 20), max(envelope) * 10 ** (-38 / 20))
    active = [i for i, rms in enumerate(envelope) if rms >= threshold]
    require(bool(active), f"Silent source: {source}")
    start = max(0, active[0] * hop - round(.02 * rate))
    end = min(len(original), (active[-1] + 1) * hop + round(.12 * rate))
    samples = array.array("f", original[start:end])
    pre = helper.stats(samples)
    gain = min(12.0, -21.0 - pre["rms_dbfs"], -6.0 - pre["sample_peak_dbfs"])
    fade_in = min(round(.002 * rate), len(samples) // 4)
    fade_out = min(round(.008 * rate), len(samples) // 4)
    for i in range(len(samples)):
        fade = min(1.0, i / max(1, fade_in), (len(samples) - 1 - i) / max(1, fade_out))
        samples[i] *= 10 ** (gain / 20) * fade
    command = [str(FFMPEG_PATH), "-hide_banner", "-v", "error", "-y", "-f", "f32le",
               "-ar", str(rate), "-ac", "1", "-i", "pipe:0", "-map_metadata", "-1",
               "-c:a", "libvorbis", "-q:a", "4", "-fflags", "+bitexact", "-flags:a", "+bitexact",
               "-threads", "1", "-ac", "1", "-ar", str(rate), str(target)]
    for _ in range(3):
        subprocess.run(command, input=samples.tobytes(), check=True, capture_output=True)
        decoded = helper.decode(str(FFMPEG_PATH), target)
        metrics = helper.stats(decoded)
        if metrics["sample_peak_dbfs"] <= -1 and metrics["clipped_samples"] == 0:
            break
        correction = -3.0 - metrics["sample_peak_dbfs"]
        samples = array.array("f", (x * 10 ** (correction / 20) for x in samples))
        gain += correction
    else:
        raise RuntimeError(f"Decoded Vorbis peak check failed: {source}")
    ogg = target.read_bytes()
    pos = ogg.index(b"\x01vorbis")
    channels, sample_rate = ogg[pos + 11], struct.unpack_from("<I", ogg, pos + 12)[0]
    require(channels == 1 and sample_rate == rate, "Expected mono 32000 Hz Vorbis")
    require(abs(len(decoded) - len(samples)) <= 1, "Vorbis duration changed")
    wav = io.BytesIO()
    with wave.open(wav, "wb") as preview:
        preview.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        preview.writeframes(struct.pack("<" + "h" * len(decoded), *(round(x * 32767) for x in decoded)))
    record = dict(sourcePcmSha256=sha(original.tobytes()), sourceAudio=helper.stats(original),
                  transforms=dict(decode="W33 helper: mono float32 at 32000 Hz",
                                  trimStartSample=start, trimEndSample=end,
                                  trimStartSeconds=round(start / rate, 6), trimEndSeconds=round(end / rate, 6),
                                  silenceRmsThresholdDbfs=round(20 * math.log10(threshold), 4),
                                  silencePolicy="10 ms RMS windows, -58 dBFS or 38 dB below peak window; 20 ms lead and 120 ms tail",
                                  hardDurationCapSeconds=None, gainDb=round(gain, 6),
                                  gainPolicy="W33: RMS aim -21 dBFS; sample peak <= -6 dBFS; boost <= 12 dB",
                                  fadeInMs=2, fadeOutMs=8, fadeEndpoints="zero-valued PCM endpoints before encoding",
                                  tempo=1.0, pitch=1.0,
                                  encoder="libvorbis quality 4, bitexact flags, one thread, metadata stripped"),
                  output=dict(metrics, codec="vorbis", channels=channels, sampleRateHz=sample_rate,
                              bytes=len(ogg), sha256=sha(ogg)),
                  preview=dict(codec="pcm_s16le", channels=1, sampleRateHz=rate,
                               bytes=len(wav.getvalue()), sha256=sha(wav.getvalue())))
    return ogg, wav.getvalue(), record


def timed_reload(helper, base_bytes, target, ticks):
    """Pitch-preserving atempo, exact sample duration, post-stretch safe fades."""
    rate = helper.RATE
    source = target.with_name(target.stem + "-source.ogg")
    source.write_bytes(base_bytes)
    original = helper.decode(str(FFMPEG_PATH), source)
    target_samples = ticks * (rate // 20)
    factor = len(original) / target_samples
    require(.5 <= factor <= 2, f"Reload atempo {factor:.6f} outside supported 0.5..2 range")
    filters = (f"atempo={factor:.12f},apad,atrim=end_sample={target_samples},"
               f"afade=t=in:ss=0:ns={round(.002 * rate)},"
               f"afade=t=out:ss={target_samples - round(.008 * rate)}:ns={round(.008 * rate)}")
    gain = 0.0
    for _ in range(3):
        command = [str(FFMPEG_PATH), "-hide_banner", "-v", "error", "-y", "-i", str(source),
                   "-af", filters + f",volume={gain:.12f}dB", "-ac", "1", "-ar", str(rate),
                   "-map_metadata", "-1", "-c:a", "libvorbis", "-q:a", "4",
                   "-fflags", "+bitexact", "-flags:a", "+bitexact", "-threads", "1", str(target)]
        subprocess.run(command, check=True, capture_output=True)
        decoded = helper.decode(str(FFMPEG_PATH), target)
        metrics = helper.stats(decoded)
        if metrics["sample_peak_dbfs"] <= -1 and metrics["clipped_samples"] == 0:
            break
        gain += -3.0 - metrics["sample_peak_dbfs"]
    else:
        raise RuntimeError("Timed reload decoded Vorbis peak check failed")
    require(len(decoded) == target_samples, "Timed reload must match exact 20 Hz tick duration")
    ogg = target.read_bytes()
    pos = ogg.index(b"\x01vorbis")
    channels, sample_rate = ogg[pos + 11], struct.unpack_from("<I", ogg, pos + 12)[0]
    require(channels == 1 and sample_rate == rate, "Timed reload must be mono 32000 Hz Vorbis")
    wav = io.BytesIO()
    with wave.open(wav, "wb") as preview:
        preview.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        preview.writeframes(struct.pack("<" + "h" * len(decoded), *(round(x * 32767) for x in decoded)))
    return ogg, wav.getvalue(), dict(
        sourceDurationSeconds=len(original) / rate, targetDurationSeconds=ticks / 20,
        targetSamples=target_samples,
        transforms=dict(atempo=factor, filter=filters, postEncodeGainDb=gain, pitch=1.0,
                        pitchPolicy="ffmpeg atempo preserves pitch; no sample-rate pitch shift",
                        durationPolicy="Pad/trim to exact ticks at 20 Hz after atempo",
                        fadeInMs=2, fadeOutMs=8,
                        encoder="libvorbis quality 4, bitexact flags, one thread, metadata stripped"),
        output=dict(metrics, codec="vorbis", channels=channels, sampleRateHz=sample_rate,
                    bytes=len(ogg), sha256=sha(ogg)),
        preview=dict(codec="pcm_s16le", channels=1, sampleRateHz=rate,
                     bytes=len(wav.getvalue()), sha256=sha(wav.getvalue())))


def audition(records, timed_records):
    cards = []
    for row in records:
        preview = "preview/" + Path(row["preview"]["path"]).name
        asset = "../../../../" + row["asset"]
        status = "Mapped named-action candidate" if row["includedInEvent"] else "Candidate only: conflicting normal/Honed labels on identical decoded audio"
        cards.append(f'<article><h2>{html.escape(row["originalName"])}</h2><p>{html.escape(status)}</p>'
                     f'<audio controls preload="none" src="{preview}"></audio>'
                     f'<p><a href="{preview}">WAV preview</a> · <a href="{asset}">Pack OGG</a></p>'
                     f'<p>{row["output"]["duration_seconds"]:.3f} s · {row["output"]["sample_peak_dbfs"]:.2f} dBFS peak</p></article>')
    for row in timed_records:
        preview = "preview/" + Path(row["preview"]["path"]).name
        asset = "../../../../src/main/resources/" + row["asset"]
        cards.append(f'<article><h2>{html.escape(row["label"])}</h2>'
                     f'<p>{row["ticks"]} simulation ticks · pitch-preserving atempo from {html.escape(row["originalName"])}</p>'
                     f'<audio controls preload="none" src="{preview}"></audio>'
                     f'<p><a href="{preview}">Timed WAV preview</a> · <a href="{asset}">Timed pack OGG</a></p>'
                     f'<p>{row["output"]["duration_seconds"]:.3f} s · {row["output"]["sample_peak_dbfs"]:.2f} dBFS peak</p></article>')
    return ('''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>W84 Izanagi's Burden supplied audio</title><style>
body{font:16px system-ui;max-width:1000px;margin:40px auto;padding:0 20px;background:#15191e;color:#edf0f4}
main{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px}article{padding:20px;background:#242b33;border-radius:10px}
h2{font-size:18px}a{color:#9acbff}audio{width:100%}p{line-height:1.5}</style>
<h1>W84 · Izanagi's Burden</h1><p>Supplied uploader labels, not independently audition verified. Controls play only when you press them.
All ten labeled action variants retain their base source tempo. Two additional timed reloads use the requested simulation ticks.
The confirmed default is 61 ticks (3.05 s), derived by ceil at 20 Hz from the historical Sniper/defaultReload curve at stat 40
(3.02015168 s). This is simulation policy, not exact observed Destiny reload timing.
Reload_3 and Reload_Honed_1 decode identically and are excluded from the proposed event pools.</p><main>
''' + "\n".join(cards) + "\n</main></html>\n").encode()


def generate(normal_ticks=61, special_ticks=61):
    require(normal_ticks > 0 and special_ticks > 0, "Reload ticks must be positive")
    helper, pins, discovery = load_inputs()
    outputs, records = {}, []
    with tempfile.TemporaryDirectory(prefix="destiny-w84-audio-") as directory:
        for pin in pins:
            stem = Path(pin["originalName"]).stem.lower()
            ogg, wav, record = transform(helper, ROOT / pin["privatePath"], Path(directory) / (stem + ".ogg"))
            asset, preview = PACK / (stem + ".ogg"), ART / "preview" / (stem + ".wav")
            outputs[asset], outputs[preview] = ogg, wav
            record.update(action=pin["action"], originalName=pin["originalName"], driveId=pin["id"],
                          sourceSha256=pin["sourceSha256"], privatePath=pin["privatePath"],
                          proposedEvent=PREFIX + pin["action"],
                          sound="destiny:w84/izanagis_burden/" + stem,
                          asset=str(asset.relative_to(ROOT)))
            record["preview"]["path"] = str(preview.relative_to(ROOT))
            records.append(record)
    groups = defaultdict(list)
    for record in records:
        groups[record["sourcePcmSha256"]].append(record)
    collisions = []
    for group in groups.values():
        conflict = len({r["action"] for r in group}) > 1
        for row in group:
            row["includedInEvent"] = not conflict
            row["classification"] = ("candidate_only_conflicting_uploader_labels" if conflict else "named_uploader_action_candidate")
            row["identityEvidence"] = "Izanagis_Burden/" + row["originalName"]
            row["limitations"] = "Uploader folder/filename evidence only; no acoustic listening or gameplay verification. Numeric suffix is an uploader variant, not a perk stack or reload timing."
        if conflict:
            native = []
            for row in group:
                pcm = subprocess.run([str(FFMPEG_PATH), "-hide_banner", "-v", "error",
                                      "-i", str(ROOT / row["privatePath"]), "-map", "0:a:0",
                                      "-c:a", "pcm_f32le", "-f", "f32le", "pipe:1"],
                                     check=True, capture_output=True).stdout
                native.append(dict(source=row["originalName"], rawSha256=row["sourceSha256"],
                                   pcmSha256=sha(pcm), pcmBytes=len(pcm)))
            collisions.append(dict(sourcePcmSha256=group[0]["sourcePcmSha256"],
                                   sources=[r["originalName"] for r in group],
                                   nativeDecodeComparison="float32 PCM at original sample rate and channel count, without resampling or downmix",
                                   identicalNativeDecodedContent=len({r["pcmSha256"] for r in native}) == 1,
                                   nativeDecodedSources=native,
                                   policy="Keep both listenable candidates; exclude from parent event pools because action labels conflict."))
    events = {PREFIX + action: dict(sounds=[dict(name=r["sound"], stream=False, attenuation_distance=32)
                                          for r in records if r["action"] == action and r["includedInEvent"]])
              for action in ACTION_PATTERNS}
    require(all(event["sounds"] for event in events.values()), "Missing unambiguous named action pool")
    clips, timed_records = {}, []
    with tempfile.TemporaryDirectory(prefix="destiny-w84-timed-reload-") as directory:
        for action, ticks, suffix, label in (
                ("reload", normal_ticks, "", "Normal reload"),
                ("honed_reload", special_ticks, ".honed", "Honed reload")):
            # Stable first uploader variant from the already unambiguous action pool.
            # Numeric suffix orders variants only; action identity comes from its label.
            candidates = [r for r in records if r["action"] == action and r["includedInEvent"]]
            source = min(candidates, key=lambda r: int(Path(r["originalName"]).stem.rsplit("_", 1)[1]))
            stem = f"izanagis_burden{'_honed' if suffix else ''}_{ticks}"
            event = f"weapon.reload_w84.izanagis_burden{suffix}.{ticks}"
            base_bytes = outputs[ROOT / source["asset"]]
            ogg, wav, record = timed_reload(helper, base_bytes, Path(directory) / (stem + ".ogg"), ticks)
            asset = RELOAD_PACK / (stem + ".ogg")
            preview = ART / "preview" / (stem + ".wav")
            outputs[asset], outputs[preview] = ogg, wav
            clip = dict(id="izanagis_burden", ticks=ticks, event=event,
                        sourceEvent=PREFIX + action, sourceSha256=sha(base_bytes),
                        asset=str(asset.relative_to(ROOT / "src/main/resources")))
            clips[action] = clip
            sound = "destiny:w84/reload/" + stem
            events[event] = dict(sounds=[dict(name=sound, stream=False, attenuation_distance=32)])
            record.update(clip, kind="timed_reload", action=action, label=label,
                          originalName=source["originalName"], driveId=source["driveId"],
                          rawSourceSha256=source["sourceSha256"], sourceAsset=source["asset"], sound=sound,
                          sourceSelection="First uploader variant in the unambiguous named-action pool; conflicting Reload_3 / Reload_Honed_1 excluded")
            record["preview"]["path"] = str(preview.relative_to(ROOT))
            timed_records.append(record)
    outputs[ART / "event-definitions.json"] = enc(events)
    outputs[ART / "source-content-duplicates.json"] = enc(collisions)
    outputs[ART / "audition.html"] = audition(records, timed_records)
    manifest = dict(schemaVersion=1, stage="W84", weapon="izanagis_burden",
                    sourceRoot=discovery["sourceRoot"], sourceFolder=discovery["folderUrl"],
                    authorization="User-authorized supplied Drive folder. No redistribution license inferred.",
                    sourcePins=pins, discoverySha256=sha((ART / "folder-discovery.json").read_bytes()),
                    sourcePinsSha256=sha((ART / "source-pins.json").read_bytes()),
                    toolchain=dict(ffmpegPath=str(FFMPEG_PATH.relative_to(ROOT)), ffmpegSha256=FFMPEG_SHA256,
                                   w33HelperPath=str(HELPER_PATH.relative_to(ROOT)), w33HelperSha256=HELPER_SHA256,
                                   generatorSha256=sha(Path(__file__).read_bytes())),
                    events=events, eventDefinitions="art/weapons/w84/audio/event-definitions.json",
                    reloadAudio=[clips["reload"]], honedReloadAudio=clips["honed_reload"],
                    timedReloadRecords=timed_records,
                    reloadTiming=dict(status="confirmed_simulation_policy" if (normal_ticks, special_ticks) == (61, 61) else "explicit_generator_override",
                                      normalTicks=normal_ticks, specialTicks=special_ticks,
                                      normalDurationSeconds=normal_ticks / 20, specialDurationSeconds=special_ticks / 20,
                                      timedVariantsGenerated=True, pitchPreserving=True, baseEventTempo=1.0,
                                      confirmedPolicy=dict(normalTicks=61, specialTicks=61, curve="historical Sniper/defaultReload",
                                                           reloadStat=40, historicalSeconds=3.02015168,
                                                           quantization="ceil(seconds * 20)", exactObservedDestinyTiming=False)),
                    audition="art/weapons/w84/audio/audition.html", records=records, duplicatePcmGroups=collisions,
                    integration="Parent may merge event-definitions.json into shared sounds.json. reloadAudio contains only the normal Clip to keep id/ticks unique. honedReloadAudio is a separate Clip for the dedicated exact-start path. This builder writes only W84 sidecars and W84 OGG assets.",
                    limitations=["Named uploader action candidates; no listening, native app, Java, Gradle, or runtime validation performed.",
                                 "No synthetic Honed Edge layers, surrogates, or arbitrary numeric action guesses. Timed reloads implement confirmed simulation policy, not exact observed Destiny timing.",
                                 "atempo preserves pitch algorithmically; transient alignment remains an approximation.",
                                 "Complete labeled action tails retained after W33 silence trimming; no family-fire three-second hard cap.",
                                 "Sample peak headroom is checked after Vorbis decoding; not an intersample true-peak measurement."],
                    outputs={str(path.relative_to(ROOT)): sha(data) for path, data in outputs.items()})
    outputs[ART / "implementation.json"] = enc(manifest)
    return outputs, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Offline byte-for-byte verification; no persistent writes")
    parser.add_argument("--normal-ticks", type=int, default=61, help="Normal reload simulation ticks at 20 Hz (default: 61)")
    parser.add_argument("--special-ticks", "--honed-ticks", type=int, default=61, help="Honed reload simulation ticks at 20 Hz (default: 61)")
    args = parser.parse_args()
    outputs, manifest = generate(args.normal_ticks, args.special_ticks)
    for path in outputs:
        allowed = path.is_relative_to(ART) or (path.parent in (PACK, RELOAD_PACK) and path.suffix == ".ogg")
        require(allowed, f"Output outside W84 write scope: {path}")
    if args.verify:
        for path, data in outputs.items():
            require(path.is_file() and path.read_bytes() == data, f"Generated output drift: {path}")
    else:
        for path, data in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(json.dumps(dict(verified=args.verify, sourceFiles=len(manifest["sourcePins"]),
                          newOgg=sum(p.suffix == ".ogg" for p in outputs),
                          events={key: len(value["sounds"]) for key, value in manifest["events"].items()},
                          candidateOnly=sum(not r["includedInEvent"] for r in manifest["records"]),
                          timedReloadVariants=len(manifest["timedReloadRecords"]),
                          normalTicks=args.normal_ticks, specialTicks=args.special_ticks, sharedFilesEdited=False)))


if __name__ == "__main__":
    main()
