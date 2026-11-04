#!/usr/bin/env python3
"""Build W63 full-magazine audio; --verify is offline/read-only, --check uses private temp.

rtk proxy python3 scripts/audio/build_reload_sounds_w63.py [--verify | --check]
Only the W63 owned resources and additive sounds.json entries are published. No downloads.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = "scripts/audio/build_reload_sounds_w63.py"
RES = "src/main/resources/"
SOUNDS = RES + "assets/destiny/sounds.json"
CONFIG = RES + "destiny/sounds/w63-reload.json"
MANIFEST = "art/weapons/w63/audio-manifest.json"
NOTES = "art/weapons/w63/audio-notes.md"
OUTPUT = RES + "assets/destiny/sounds/w63/reload/"
PREFIX = "weapon.reload_w63."
RATE = 32000
GRANULE_TOLERANCE = 1024  # Maximum Vorbis long-block overlap at this sample rate.
MAX_PEAK = 10 ** (-1 / 20)
JAVA = "src/main/java/kim/biryeong/destiny/"
PINS = {
    RES + "destiny/weapons/w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    RES + "destiny/weapons/w46-timing.json": "e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07",
    RES + "destiny/weapons/w62-outlaw.json": "5188d73a271b0a5080eb99d47c50a6d37ccae11fe756ebd2893c70499f3637bc",
    RES + "destiny/sounds/w33.json": "7bd79392bc81e821a1ec1b4d3154986e3cd9c09362cef9fe1c1bcfc0befe333b",
    JAVA + "weapon/WeaponReloadPolicy.java": "44fa1ae11e09f67371383cb82112fa0a3fe57b58a003441abade833173a43f54",
    JAVA + "weapon/WeaponProfile.java": "4c03a0e23b92c4b3e73399c6f33d45850688075a0cd278540f8bda79c8d50bd9",
    JAVA + "weapon/WeaponTiming.java": "978b7342a664f2da569131209da048698563d7c26af76e778b0ef5f85dcdecd3",
    JAVA + "weapon/OutlawProfile.java": "6974b20c2beed782c312153efab8fbe21683291f2248e37502a9f381bd5b1c13",
}
ORIGINAL_EVENTS_SHA = "f3221d89106a442192b533225cc4d6019c77317a55aa5cb82c7dc0ca96f4dff4"
WEAPON_KEY_SHA = "72b63f29412e695d2db45e4e843c1fce13d66507231f965b0c31139aa8e2dde5"
FFMPEG_SHA = "6d175a4743ca50256e89a8cdd731100f9cee33bd79aeea46894d209410dc6617"
FFMPEG_VERSION = "ffmpeg version 7.1 Copyright (c) 2000-2024 the FFmpeg developers"
LIMITATIONS = [
    "W46 historical community reload curves and W62 Outlaw timings are the current server's authored/approximate durations, not official original-game measurements.",
    "Original animation endpoint, ammo insertion endpoint, acoustic endpoint and any original post-insertion tail have unknown equivalence. W63 fits the entire already-trimmed W33 clip to the server phase; it establishes no original endpoint semantics.",
    "Family representatives remain representatives; exact event aliases identify only the documented named uploader source, not independently verified per-weapon acoustic identity. Apostate still uses the sniper family source with W33's unverified Aprostate identity.",
    "Pitch is preserved algorithmically by ffmpeg atempo at a fixed sample rate. Time stretching can change transients; final apad/atrim handles sample rounding and algorithm tail differences. No new silence analysis, action segmentation, looping, concatenation or loudness boost is applied.",
    "W33 authorization and provenance are inherited. No new download or redistribution permission is inferred. Original private source files are neither required nor published.",
    "These are offline resource/PCM checks only. No native playback, original-game animation synchronization, acoustic-output proof or independent audition is claimed.",
    "Shotguns, canonical Long Arm, bows, swords and every incremental reload are excluded. A full reload source must never stand in for a single-shell insert.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def document(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "Duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(path):
    return json.loads((ROOT / path).read_bytes(), object_pairs_hook=unique_pairs)


def keyed(rows, label):
    result = {}
    for row in rows:
        require(row["id"] not in result, "Duplicate " + label + ": " + row["id"])
        result[row["id"]] = row
    return result


def method_pin(path, signature):
    text = (ROOT / path).read_text()
    start = text.index(signature)
    end = text.index("\n    }", start) + 6
    return {"path": path, "selector": signature.strip(), "sha256": sha(text[start:end].encode())}


def inputs():
    for path, expected in PINS.items():
        require(sha((ROOT / path).read_bytes()) == expected, "Consumed source drift: " + path)
    selection = method_pin(JAVA + "sound/DestinySounds.java", "    public static String weaponKey(")
    require(selection["sha256"] == WEAPON_KEY_SHA, "DestinySounds.weaponKey selection changed")
    # Pin the actual phase/Outlaw methods, without pinning unrelated runtime lifecycle edits.
    phase = method_pin(JAVA + "weapon/WeaponCycle.java", "    public boolean startReload(long tick, WeaponProfile p, WeaponMagazine magazine, WeaponReloadPolicy.Plan plan)")
    outlaw_plan = method_pin(JAVA + "weapon/WeaponOutlaw.java", "    public static WeaponReloadPolicy.Plan plan(")
    definitions = read_json(SOUNDS)
    original = {k: v for k, v in definitions.items() if not k.startswith(PREFIX)}
    require(len(original) == 99 and sha(canonical(original)) == ORIGINAL_EVENTS_SHA,
            "The original 99 sound event definitions changed")
    catalog = keyed(read_json(RES + "destiny/weapons/w30.json"), "catalog ID")
    timings = keyed(read_json(RES + "destiny/weapons/w46-timing.json"), "timing ID")
    outlaw = read_json(RES + "destiny/weapons/w62-outlaw.json")
    reloads = keyed(outlaw["reloads"], "Outlaw reload ID")
    require(len(catalog) == 63 and catalog.keys() == timings.keys(), "Expected complete current 63-entry catalog")
    require(set(reloads) == {r["id"] for r in outlaw["weapons"]}, "Outlaw support/reload mismatch")
    require(set(reloads) <= catalog.keys(), "Unknown Outlaw ID")
    w33 = read_json(RES + "destiny/sounds/w33.json")
    source_by_sound = {v["sound"]: v for v in w33["events"].values() if v["event"].endswith(".reload")}
    entries, exclusions, sources, variants = [], [], {}, []
    for id_, entry in catalog.items():
        timing = timings[id_]["timing"]
        family = entry["family"]
        reason = ("excluded_" + family if family in {"shotgun", "bow", "sword"}
                  else "incremental_WeaponReloadPolicy_Long_Arm" if id_ == "long_arm"
                  else "incremental_W46" if timing["shellReload"] else None)
        if reason:
            exclusions.append({"id": id_, "reason": reason})
            continue
        ticks = timing["reloadTicks"]
        require(timing["supported"] and isinstance(ticks, int) and ticks > 0,
                "Unresolved full-magazine phase: " + id_)
        exact = "weapon." + id_ + ".reload"
        event = exact if exact in original else "weapon." + family + ".reload"
        definition = original[event]
        require(len(definition["sounds"]) == 1, "Ambiguous selected source: " + event)
        sound = definition["sounds"][0]
        require(isinstance(sound, dict) and "pitch" not in sound and "type" not in sound,
                "Unsupported selected event transform: " + event)
        source = source_by_sound[sound["name"]]
        path = source["asset_path"]
        require(path == RES + "assets/destiny/sounds/" + sound["name"].split(":", 1)[1] + ".ogg",
                "W33 event/asset mismatch: " + event)
        require(sha((ROOT / path).read_bytes()) == source["output"]["sha256"], "W33 Ogg hash drift: " + path)
        if event not in sources:
            sources[event] = {
                "sourceEvent": event, "w33Event": source["event"], "asset": path,
                "sha256": source["output"]["sha256"], "definition": definition,
                "selection": "named_source_alias" if event == exact else "family_representative",
                "provenance": {k: source[k] for k in (
                    "drive_id", "original_name", "source_folder", "source_folder_id", "match",
                    "limitations", "source_sha256", "source_url", "source_folder_url",
                    "status", "source_identity_confidence", "action_confidence", "transforms", "output")},
            }
        plans = [("base", ticks)]
        if id_ in reloads:
            boosted = reloads[id_]
            require(0 < boosted["firstTicks"] == boosted["intervalTicks"] <= ticks,
                    "Unexpected full-magazine Outlaw timing: " + id_)
            plans.append(("outlaw", boosted["firstTicks"]))
        for mode, duration in plans:
            # Sanitize the entire selected event: named aliases must not collapse into families.
            token = re.sub(r"[^a-z0-9_.]", "_", event)
            key = PREFIX + token + "." + str(duration)
            asset = "assets/destiny/sounds/w63/reload/" + token.replace(".", "_") + "_" + str(duration) + ".ogg"
            row = {"id": id_, "ticks": duration, "event": key, "sourceEvent": event,
                   "sourceSha256": source["output"]["sha256"], "asset": asset}
            require(not any(x["id"] == id_ and x["ticks"] == duration for x in entries), "Duplicate id/ticks")
            entries.append(row)
            variants.append({"id": id_, "mode": mode, "ticks": duration})
    entries.sort(key=lambda e: (e["id"], e["ticks"]))
    require(len(entries) == 61 and sum(v["mode"] == "outlaw" for v in variants) == 11,
            "Expected 50 base and 11 non-shell Outlaw entries")
    subset = {k: original[k] for k in sorted(sources)}
    consumed = {
        "repositoryFiles": {**PINS, SCRIPT: sha((ROOT / SCRIPT).read_bytes())},
        "javaMethods": [selection, phase, outlaw_plan],
        "sourceEventDefinitions": {"path": SOUNDS, "sha256": sha(canonical(subset)), "definitions": subset},
        "originalEventDefinitions": {"path": SOUNDS, "count": 99, "sha256": ORIGINAL_EVENTS_SHA,
                                     "definitions": original},
    }
    return {"config": {"stage": "W63", "entries": entries}, "sources": sources,
            "exclusions": exclusions, "variants": variants, "consumed": consumed,
            "w33Authorization": {k: w33[k] for k in ("source_root", "authorization", "cache_policy", "identity_policy", "release_status")}}


def run(command, data=None):
    result = subprocess.run(command, input=data, capture_output=True, timeout=120)
    require(result.returncode == 0, "ffmpeg failed: " + result.stderr.decode(errors="replace")[-2000:])
    return result.stdout


def tool(explicit):
    cached = ROOT / "run/private-sources/w33/tools/imageio_ffmpeg/binaries"
    candidates = [Path(explicit)] if explicit else list(cached.glob("ffmpeg-*"))
    if not candidates and shutil.which("ffmpeg"):
        candidates = [Path(shutil.which("ffmpeg"))]
    matches = [p.resolve() for p in candidates if p.is_file() and sha(p.read_bytes()) == FFMPEG_SHA]
    require(len(matches) == 1, "Supply the pinned offline W33 ffmpeg 7.1 binary via --ffmpeg")
    ffmpeg = str(matches[0])
    version = run([ffmpeg, "-version"]).decode().splitlines()[0]
    require(version == FFMPEG_VERSION, "ffmpeg version drift")
    return ffmpeg


def decode(ffmpeg, path):
    return run([ffmpeg, "-nostdin", "-hide_banner", "-v", "error", "-protocol_whitelist", "file,pipe",
                "-i", str(path), "-map", "0:a:0", "-f", "f32le", "-acodec", "pcm_f32le",
                "-ac", "1", "-ar", str(RATE), "pipe:1"])


def pcm_stats(raw):
    require(len(raw) > 0 and len(raw) % 4 == 0, "Invalid decoded float32 PCM")
    samples = array.array("f")
    samples.frombytes(raw)
    if sys.byteorder != "little":
        samples.byteswap()
    require(all(math.isfinite(s) for s in samples), "Nonfinite PCM")
    peak = max(abs(s) for s in samples)
    rms = math.sqrt(math.fsum(s * s for s in samples) / len(samples))
    require(rms > 0 and peak <= MAX_PEAK and all(abs(s) < 1 for s in samples),
            "Silent, clipped or insufficient-headroom audio")
    return {"decodedSamples": len(samples), "decodedSeconds": len(samples) / RATE,
            "samplePeakDbfs": round(20 * math.log10(peak), 6),
            "rmsDbfs": round(20 * math.log10(rms), 6), "clippedSamples": 0}


def ogg_info(path):
    data = path.read_bytes()
    pos, serial, sequence, granule, header = 0, None, 0, 0, None
    while pos < len(data):
        require(data[pos:pos + 4] == b"OggS" and data[pos + 4] == 0, "Invalid Ogg page")
        count = data[pos + 26]
        body = pos + 27 + count
        end = body + sum(data[pos + 27:body])
        require(end <= len(data), "Truncated Ogg")
        page_serial, page_sequence = struct.unpack_from("<II", data, pos + 14)
        serial = page_serial if serial is None else serial
        require(page_serial == serial and page_sequence == sequence, "Unexpected chained/reordered Ogg")
        sequence += 1
        if header is None:
            header = data[body:end]
        granule = struct.unpack_from("<Q", data, pos + 6)[0]
        final_flag = data[pos + 5]
        pos = end
    require(header is not None and header[:7] == b"\x01vorbis" and final_flag & 4, "Expected complete Vorbis Ogg")
    channels = header[11]
    rate = struct.unpack_from("<I", header, 12)[0]
    require(channels == 1 and rate == RATE, "Expected mono 32000 Hz Vorbis")
    return {"codec": "vorbis", "channels": channels, "sampleRateHz": rate,
            "granuleSamples": granule, "granuleSeconds": granule / rate,
            "bytes": len(data), "sha256": sha(data)}


def inspect(ffmpeg, path, target=None):
    info = {**ogg_info(path), **pcm_stats(decode(ffmpeg, path))}
    if target is not None:
        require(abs(info["granuleSamples"] - target) <= 1, "Container duration differs by more than one sample")
        require(abs(info["decodedSamples"] - target) <= GRANULE_TOLERANCE,
                "Decoded duration exceeds Vorbis overlap tolerance")
    return info


def atempo_chain(ratio):
    factors = []
    while ratio < 0.5:
        factors.append(0.5)
        ratio /= 0.5
    while ratio > 2:
        factors.append(2.0)
        ratio /= 2.0
    factors.append(ratio)
    return ["atempo=" + format(f, ".15g") for f in factors]


def sound_definitions(data):
    result = {}
    for row in data["config"]["entries"]:
        definition = data["sources"][row["sourceEvent"]]["definition"]
        value = {"subtitle": definition["subtitle"], "sounds": [{
            "name": "destiny:" + row["asset"].removeprefix("assets/destiny/sounds/").removesuffix(".ogg"),
            "stream": False, "attenuation_distance": 32}]}
        require(row["event"] not in result or result[row["event"]] == value, "Event collision")
        result[row["event"]] = value
    return dict(sorted(result.items()))


def sounds_bytes(data):
    # Keep all original entry bytes as-is, including numeric lexical values/ordering.
    raw = (ROOT / SOUNDS).read_bytes()
    current = read_json(SOUNDS)
    added = sound_definitions(data)
    existing = {k: v for k, v in current.items() if k.startswith(PREFIX)}
    if existing:
        require(existing == added, "Existing W63 definitions differ; refusing to replace entries")
        return raw
    end = raw.rfind(b"}")
    require(end >= 0 and not raw[end + 1:].strip(), "Unexpected sounds.json suffix")
    addition = document(added).rstrip()[1:-1].strip(b"\n")
    return raw[:end].rstrip() + b",\n" + addition + b"\n" + raw[end:]


def notes(data, assets):
    peak = max(a["output"]["samplePeakDbfs"] for a in assets)
    max_delta = max(abs(a["output"]["decodedSamples"] - a["targetSamples"]) for a in assets)
    return ("# W63 reload audio resources\n\n"
            "The current 63-entry resource catalog yields 50 full-magazine base entries and 11 supported non-shell Outlaw variants (61 unique id/ticks rows). "
            f"Deduplication by sourceEvent + ticks produces {len(assets)} Ogg assets/events. All 99 previous sounds.json key/value definitions are preserved.\n\n"
            "Runtime resource: `src/main/resources/destiny/sounds/w63-reload.json`. Exact schema:\n\n"
            '```json\n{"stage":"W63","entries":[{"id":"weaponCatalogId","ticks":59,"event":"weapon.reload_w63.weapon.hand_cannon.reload.59","sourceEvent":"weapon.hand_cannon.reload","sourceSha256":"<W33 Ogg SHA-256>","asset":"assets/destiny/sounds/w63/reload/weapon_hand_cannon_reload_59.ogg"}]}\n```\n\n'
            "`id` is the catalog weapon ID, never a mode suffix. Lookup uses (id, actual captured full-magazine phase ticks); there is no duplicate id/ticks. "
            "Base ticks come from W46 after respecting WeaponReloadPolicy: canonical Long Arm is incremental even though W46 still lists a whole-magazine estimate. "
            "Outlaw firstTicks comes from W62 only for its 11 eligible full-magazine entries. The two shell Outlaw entries are excluded. "
            "WeaponCycle captures firstTicks at reload start; expiry of Outlaw does not retime an active clip. "
            "Runtime lifecycle, cancellation, emitter behavior and fallback are integrated separately by the main task.\n\n"
            "`sourceEvent` follows DestinySounds.weaponKey exactly: choose a present weapon-ID reload event, otherwise family.reload. "
            "Named aliases share W33 family-file bytes but retain distinct sourceEvent/ticks deduplication identity. "
            "`sourceSha256` pins the consumed W33 Ogg bytes, not the original WAV/MP3; original hashes, URLs, trims, confidence and limitations are in the audio manifest. "
            "No original source cache is read. Event names contain only lowercase letters, digits, dots and underscores.\n\n"
            "Processing decodes the hash-verified W33 Ogg to mono float32 at 32000 Hz. Tempo = decoded source sample count / target sample count, "
            "factored into atempo stages between 0.5 and 2.0. apad=whole_len and atrim=end_sample set exactly ticks*1600 samples, "
            "then libvorbis q4 encodes with one thread, stripped metadata/chapters and bitexact flags. Playback pitch must remain 1.0. "
            "There is no asetrate, resampling-based pitch shift, boost or new download.\n\n"
            f"Offline validation: container EOS granule is within 1 sample of ticks/20; decoded PCM tolerance is {GRANULE_TOLERANCE} samples "
            f"({GRANULE_TOLERANCE / RATE:.3f} s) for Vorbis long-block overlap. Observed maximum decoded delta: {max_delta} samples. "
            f"All outputs are mono 32000 Hz Vorbis, non-silent, finite, zero clipped samples; worst sample peak {peak:.6f} dBFS "
            "(required <= -1 dBFS). The manifest records each duration, hash, peak, RMS and filter.\n\n"
            "Commands (no Gradle):\n\n"
            "- `rtk proxy python3 scripts/audio/build_reload_sounds_w63.py --verify`: offline/read-only, no mkdir, temporary files, encoding or writes; checks pins, coverage, definitions, hashes and decoded PCM.\n"
            "- `rtk proxy python3 scripts/audio/build_reload_sounds_w63.py --check`: runs verification, regenerates every Ogg twice in a private system temporary directory and compares bytes with repository assets; compares regenerated config/manifest/notes and sound definitions too. No repository writes.\n"
            "- `rtk proxy python3 scripts/audio/build_reload_sounds_w63.py`: renders in private temporary storage, then publishes only owned W63 paths and appends missing sound events. Existing W63 mismatches fail instead of replacing old events.\n\n"
            "The cached W33 ffmpeg 7.1 binary is hash-pinned; `--ffmpeg` may supply an identical local binary. "
            "The manifest pins the generator itself and all consumed repository inputs. Sound definitions are pinned as an original-event snapshot and selected-event subset; "
            "the whole evolving sounds.json file is deliberately not hashed. A drifted policy/source requires review before changing pins.\n\n"
            "## Evidence limits\n\n" + "\n".join("- " + s for s in LIMITATIONS) + "\n").encode()


def unique_assets(data):
    rows = {}
    for row in data["config"]["entries"]:
        key = (row["sourceEvent"], row["ticks"])
        require(key not in rows or rows[key]["asset"] == row["asset"], "Deduplication mismatch")
        rows[key] = row
    require(len({r["asset"] for r in rows.values()}) == len(rows), "Sanitized asset collision")
    return sorted(rows.values(), key=lambda r: r["event"])


def asset_record(row, source_metrics, output):
    target = row["ticks"] * (RATE // 20)
    ratio = source_metrics["decodedSamples"] / target
    filters = atempo_chain(ratio) + ["apad=whole_len=" + str(target), "atrim=end_sample=" + str(target)]
    return {"event": row["event"], "asset": row["asset"], "sourceEvent": row["sourceEvent"],
            "sourceSha256": row["sourceSha256"], "ticks": row["ticks"],
            "targetSamples": target, "targetSeconds": row["ticks"] / 20,
            "tempoRatio": ratio, "filters": filters, "sourceMetrics": source_metrics, "output": output}


def manifest_document(data, assets):
    return {
        "stage": "W63", "schemaVersion": 1, "runtimeConfig": CONFIG, "consumedSources": data["consumed"],
        "authorization": data["w33Authorization"], "sources": [data["sources"][k] for k in sorted(data["sources"])],
        "toolchain": {"ffmpegVersion": FFMPEG_VERSION, "ffmpegBinarySha256": FFMPEG_SHA,
                      "encoder": "libvorbis q4; mono 32000 Hz; threads 1; metadata/chapters stripped; bitexact",
                      "durationToleranceSamples": {"container": 1, "decoded": GRANULE_TOLERANCE},
                      "maximumSamplePeakDbfs": -1},
        "counts": {"catalog": 63, "baseEntries": 50, "outlawEntries": 11, "runtimeEntries": 61,
                   "excludedEntries": len(data["exclusions"]), "uniqueAssets": len(assets),
                   "selectedSourceEvents": len(data["sources"]), "originalEventsPreserved": 99},
        "variants": sorted(data["variants"], key=lambda r: (r["id"], r["ticks"])),
        "exclusions": sorted(data["exclusions"], key=lambda r: r["id"]),
        "assets": assets, "limitations": LIMITATIONS,
    }


def render(data, ffmpeg, temporary):
    assets, cache = [], {}
    for row in unique_assets(data):
        source = data["sources"][row["sourceEvent"]]
        if source["asset"] not in cache:
            path = ROOT / source["asset"]
            cache[source["asset"]] = (decode(ffmpeg, path), inspect(ffmpeg, path))
        raw, source_metrics = cache[source["asset"]]
        target = row["ticks"] * (RATE // 20)
        filters = asset_record(row, source_metrics, {})["filters"]
        dest = temporary / Path(row["asset"]).name
        run([ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
             "-f", "f32le", "-ar", str(RATE), "-ac", "1", "-i", "pipe:0",
             "-af", ",".join(filters), "-map_metadata", "-1", "-map_chapters", "-1",
             "-c:a", "libvorbis", "-q:a", "4", "-threads", "1", "-fflags", "+bitexact",
             "-flags:a", "+bitexact", "-ar", str(RATE), "-ac", "1", str(dest)], raw)
        assets.append(asset_record(row, source_metrics, inspect(ffmpeg, dest, target)))
    manifest = manifest_document(data, assets)
    return {CONFIG: document(data["config"]), MANIFEST: document(manifest), NOTES: notes(data, assets),
            SOUNDS: sounds_bytes(data)}, assets


def verify(data, ffmpeg):
    saved = read_json(MANIFEST)
    require(saved["consumedSources"] == data["consumed"], "Manifest consumed source pins drifted")
    require(saved["toolchain"]["ffmpegBinarySha256"] == FFMPEG_SHA, "Manifest ffmpeg pin drifted")
    require((ROOT / CONFIG).read_bytes() == document(data["config"]), "Runtime config coverage/schema/byte drift")
    expected = sound_definitions(data)
    actual = {k: v for k, v in read_json(SOUNDS).items() if k.startswith(PREFIX)}
    require(expected == actual, "W63 sound definitions mismatch")
    rows = unique_assets(data)
    require(len(saved["assets"]) == len(rows), "Manifest asset coverage mismatch")
    require({p.name for p in (ROOT / OUTPUT).iterdir()} == {Path(r["asset"]).name for r in rows},
            "Unexpected or missing W63 output file")
    source_metrics, measured_assets = {}, []
    for row in rows:
        source_path = data["sources"][row["sourceEvent"]]["asset"]
        if source_path not in source_metrics:
            source_metrics[source_path] = inspect(ffmpeg, ROOT / source_path)
        measured = inspect(ffmpeg, ROOT / (RES + row["asset"]), row["ticks"] * 1600)
        measured_assets.append(asset_record(row, source_metrics[source_path], measured))
    require((ROOT / MANIFEST).read_bytes() == document(manifest_document(data, measured_assets)),
            "Manifest provenance/filter/measurement/byte drift")
    require((ROOT / NOTES).read_bytes() == notes(data, saved["assets"]), "Audio notes drift")
    return saved["counts"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify", action="store_true")
    modes.add_argument("--check", action="store_true")
    parser.add_argument("--ffmpeg")
    args = parser.parse_args()
    data = inputs()
    ffmpeg = tool(args.ffmpeg)
    if args.verify:
        # This branch has no mkdir/tempfile/encoding/publication calls.
        print(json.dumps({"mode": "verify", "status": "PASS", **verify(data, ffmpeg)}, sort_keys=True))
        return
    if args.check:
        verify(data, ffmpeg)
    with tempfile.TemporaryDirectory(prefix="destiny-w63-") as private:
        temporary = Path(private)
        documents, assets = render(data, ffmpeg, temporary)
        if args.check:
            for path, content in documents.items():
                require((ROOT / path).read_bytes() == content, "Regenerated bytes differ: " + path)
            for asset in assets:
                filename = Path(asset["asset"]).name
                require((temporary / filename).read_bytes() == (ROOT / (RES + asset["asset"])).read_bytes(),
                        "Regenerated Ogg bytes differ: " + filename)
            # A second independent encode also checks determinism/serials, not only saved hashes.
            second = temporary / "repeat"
            second.mkdir()
            repeated_documents, repeated_assets = render(data, ffmpeg, second)
            require(repeated_documents == documents and repeated_assets == assets, "Repeated render differs")
            for asset in assets:
                filename = Path(asset["asset"]).name
                require((temporary / filename).read_bytes() == (second / filename).read_bytes(),
                        "Nondeterministic Ogg bytes: " + filename)
        else:
            # All audio must pass before publishing any owned output.
            output = ROOT / OUTPUT
            if output.exists():
                require({p.name for p in output.iterdir()} <= {Path(a["asset"]).name for a in assets},
                        "Refusing to remove unexpected existing W63 outputs")
            output.mkdir(parents=True, exist_ok=True)
            for asset in assets:
                filename = Path(asset["asset"]).name
                (output / filename).write_bytes((temporary / filename).read_bytes())
            for path, content in documents.items():
                destination = ROOT / path
                destination.parent.mkdir(parents=True, exist_ok=True)
                if not destination.exists() or destination.read_bytes() != content:
                    destination.write_bytes(content)
    print(json.dumps({"mode": "check" if args.check else "build", "status": "PASS", **verify(data, ffmpeg)}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, subprocess.TimeoutExpired) as error:
        print("W63 FAILED: " + str(error), file=sys.stderr)
        sys.exit(1)
