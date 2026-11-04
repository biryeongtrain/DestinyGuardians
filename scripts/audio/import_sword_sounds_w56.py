#!/usr/bin/env python3
"""W56: import exactly 15 named sword actions / 51 pinned clips.

rtk proxy python3 -B scripts/audio/import_sword_sounds_w56.py --offline
rtk proxy python3 -B scripts/audio/import_sword_sounds_w56.py --verify
rtk proxy python3 -B scripts/audio/import_sword_sounds_w56.py --check

Default rebuilds only owned W56 outputs. --fetch allows missing, SHA-pinned
originals to be downloaded; --offline is the default. --verify is read-only and
offline, including no bytecode writes. --check additionally regenerates every
Ogg twice in private temporary storage and compares both to the saved output.
No Gradle, native app, playback, shared-definition edits or source-media export.
"""
from __future__ import annotations

import argparse
import array
import hashlib
import html
import importlib.util
import json
import math
from os.path import relpath
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import urllib.request

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources"
CACHE = ROOT / "run/private-sources/w56"
QA = ROOT / "docs/qa/2026-10-24/w56/audio"
MANIFEST = ROOT / "art/weapons/w56/audio-manifest.json"
SIDECAR = RES / "destiny/sounds/w56.json"
ASSETS = RES / "assets/destiny/sounds/w56"
RATE = 32000
MAX_SOURCE_BYTES = 32 * 1024 * 1024
MAX_OGG_BYTES = 8 * 1024 * 1024
MAX_DURATION = 8.0
# Filled from the original discovery/download evidence; never auto-refresh pins.
EVIDENCE_PINS = {'source-discovery.json': '7c08b48acdd9c66b03d0c9141653c8e137eb585803dcd71935494ae2d6125008', 'source-pins.json': '3aafabd4a641183306ec31825467470cb57f4f16ed3d0e860f244e55e12d7c07', 'shared-baseline.json': '18cac7f5b0ae52fee1b009a9e2513648aa1897ffdd201cd36d33c83217a8ed25'}

GROUPS = [
    ("weapon.sword.light", "Half Truths", "Light_Att", 4),
    ("weapon.sword.uppercut", "Half Truths", "Heavy_Att", 4),
    ("weapon.sword.guard", "Half Truths", "Guard", 3),
    ("weapon.falling_guillotine.light", "Falling Guillotine", "Swing_Reg", 4),
    ("weapon.falling_guillotine.heavy", "Falling Guillotine", "Tornado_Swing", 4),
    ("weapon.falling_guillotine.guard", "Falling Guillotine", "Guard", 3),
    ("weapon.crown_splitter.light", "Throne Cleaver / Crown Splitter", "Light_Att", 4),
    ("weapon.crown_splitter.heavy", "Throne Cleaver / Crown Splitter", "Heavy_Att", 3),
    ("weapon.crown_splitter.heavy_air", "Throne Cleaver / Crown Splitter", "Heavy_Air_Att", 3),
    ("weapon.crown_splitter.guard", "Throne Cleaver / Crown Splitter", "Guard", 3),
    ("weapon.temptation_s_hook.light", "Temptations Hook", "Swing", 4),
    ("weapon.temptation_s_hook.empty_light", "Temptations Hook", "Swing_No_Ammo", 4),
    ("weapon.temptation_s_hook.guard", "Temptations Hook", "Guard", 2),
    ("weapon.sword.caster.release", "_Caster_Frame", "Caster_Swing_Far", 2),
    ("weapon.sword.caster.impact", "_Caster_Frame", "Caster_Proj_Exp_Close", 4),
]
FOLDERS = {
    "Half Truths": "1KX9Xxde9HLz4K9NzOGBMMXmzbfPR79d8",
    "Falling Guillotine": "15o43bw0IHQpNCMxJM4_VY8HcB240TpLC",
    "Throne Cleaver / Crown Splitter": "1KnnoZVYSIZVSKeESmhZUI2aV_roVif2i",
    "Temptations Hook": "1lgjKdvxtirr6VJTHbgohlIPC9H360hZA",
    "_Caster_Frame": "1oYLToTiOjCuLvcZTUFdkjo9O2cOMWL21",
}
LIMITS = {
    "Half Truths": "Uploader Half Truths action labels; proxy for Abide the Return / Goldtusk. No exact weapon match claimed.",
    "Falling Guillotine": "Named uploader Falling Guillotine action labels only; identity and acoustic fit not independently audition verified.",
    "Throne Cleaver / Crown Splitter": "Uploader folder shared by Throne Cleaver and Crown Splitter; individual clip weapon identity unresolved.",
    "Temptations Hook": "Named uploader Temptations Hook action labels only; identity and acoustic fit not independently audition verified.",
    "_Caster_Frame": "Generic caster frame. Far swing release is a candidate, not an exact near release layer; close projectile explosion is a named impact candidate. No exact weapon match claimed.",
}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def relative(path):
    return str(path.relative_to(ROOT))


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def evidence():
    require(len(EVIDENCE_PINS) == 3, "Missing immutable evidence pins")
    for name, digest in EVIDENCE_PINS.items():
        require(sha((QA / name).read_bytes()) == digest, "Changed evidence: " + name)
    discovery = read_json(QA / "source-discovery.json")
    for folder in discovery["folders"]:
        for extension in ("json", "html"):
            path = CACHE / (folder["folder_id"] + "." + extension)
            require(sha(path.read_bytes()) == folder[extension + "_sha256"], "Private listing evidence changed: " + path.name)
    pins = read_json(QA / "source-pins.json")["clips"]
    rows = discovery["selected"]
    expected = [(event, label, f"{prefix}_{i}.mp3", i)
                for event, label, prefix, count in GROUPS for i in range(1, count + 1)]
    require(len(rows) == len(pins) == len(expected) == 51, "Expected exactly 51 source rows/pins")
    require(len({r["id"] for r in rows}) == 51, "Source IDs must be unique")
    by_id = {p["drive_id"]: p for p in pins}
    for row, wanted in zip(rows, expected):
        require((row["event"], row["source_folder"], row["name"], row["variant"]) == wanted,
                "Unexpected source action subset")
        fid = FOLDERS[row["source_folder"]]
        require(row["source_folder_id"] == fid and row["parents"] == [fid], "Source parent mismatch")
        require(row["mimeType"] == "audio/mpeg" and not row["folder"], "Not named MP3 audio")
        pin = by_id[row["id"]]
        require(pin["original_name"] == row["name"] and pin["source_folder_id"] == fid,
                "Source pin identity mismatch")
        require(pin["source_bytes"] == row["size"] <= MAX_SOURCE_BYTES, "Invalid source size")
        require(pin["private_path"] == f"run/private-sources/w56/{row['id']}.mp3", "Unsafe private path")
        row["pin"] = pin
    return rows


def load_helpers():
    path = ROOT / "scripts/audio/import_sounds_w33.py"
    baseline = read_json(QA / "shared-baseline.json")
    require(sha(path.read_bytes()) == baseline["protected_sha256"][relative(path)], "W33 helpers changed")
    spec = importlib.util.spec_from_file_location("w56_readonly_w33_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shared_unchanged():
    """Allow main's new W56 keys, while preserving every pre-W56 definition."""
    baseline = read_json(QA / "shared-baseline.json")
    current = read_json(RES / "assets/destiny/sounds.json")
    for key, definition in baseline["sound_definitions"].items():
        require(current.get(key) == definition, "Pre-W56 sound definition mutated: " + key)
    for name, digest in baseline["protected_sha256"].items():
        require(sha((ROOT / name).read_bytes()) == digest, "Pre-W56 file mutated: " + name)
    for name, old in baseline["language_entries"].items():
        table = read_json(ROOT / name)
        require(all(table.get(k) == v for k, v in old.items()), "Pre-W56 translation mutated: " + name)
    return {"old_sound_definitions_preserved": len(baseline["sound_definitions"]),
            "old_file_hashes_preserved": len(baseline["protected_sha256"]),
            "old_language_tables_preserved": len(baseline["language_entries"]),
            "new_shared_keys_allowed_for_main_integration": True}


def source_path(row, fetch=False):
    pin = row["pin"]
    path = ROOT / pin["private_path"]
    if not path.exists():
        require(fetch, "Missing pinned private original: " + relative(path))
        request = urllib.request.Request(pin["download_url"], headers={"User-Agent": "DestinyGuardians-W56-audio-import/1"})
        with urllib.request.urlopen(request, timeout=45) as response:
            require("html" not in response.headers.get("Content-Type", "").lower(), "HTML rejected")
            length = response.headers.get("Content-Length")
            require(not length or int(length) <= MAX_SOURCE_BYTES, "Download exceeds 32 MiB")
            data = response.read(MAX_SOURCE_BYTES + 1)
        validate_source(data, pin)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as handle:
            handle.write(data)
    validate_source(path.read_bytes(), pin)
    return path


def validate_source(data, pin):
    prefix = data[:512].lstrip().lower()
    require(data and len(data) <= MAX_SOURCE_BYTES, "Empty/oversized original")
    require(b"<html" not in prefix and b"<!doctype html" not in prefix, "HTML payload rejected")
    require(len(data) == pin["source_bytes"], "Original byte count mismatch")
    require(sha(data) == pin["source_sha256"], "Original SHA256 mismatch: " + pin["drive_id"])


def sound_name(row):
    return "destiny:w56/" + row["event"].replace(".", "/") + f"_{row['variant']}"


def asset_path(row):
    return RES / "assets/destiny/sounds" / (sound_name(row).split(":", 1)[1] + ".ogg")


def subtitle(event):
    action = event.rsplit(".", 1)[1]
    kind = "fire" if action in ("light", "empty_light") else "guard" if action == "guard" else "impact" if action == "impact" else "heavy"
    return "subtitles.destiny.weapon.sword." + kind


def definitions(rows):
    return {event: {"subtitle": subtitle(event), "sounds": [
                {"name": sound_name(row), "stream": False, "attenuation_distance": 32}
                for row in rows if row["event"] == event]}
            for event, _, _, _ in GROUPS}


def prepare(row, source, ffmpeg, helper):
    samples = helper.decode(ffmpeg, source)
    require(len(samples) / RATE <= MAX_DURATION, "Source action exceeds 8 seconds; no hard cropping permitted")
    hop = RATE // 100
    threshold = 10 ** (-72 / 20)
    active = [i for i in range(0, len(samples), hop)
              if math.sqrt(sum(x*x for x in samples[i:i+hop]) / len(samples[i:i+hop])) >= threshold]
    require(active, "Silent named source")
    # Only edge silence: keep 30 ms before / 200 ms after active blocks.
    # At most 200 ms leading and 350 ms trailing removed; no action windows.
    start = min(round(.2 * RATE), max(0, active[0] - round(.03 * RATE)))
    end = max(len(samples) - round(.35 * RATE), min(len(samples), active[-1] + hop + round(.2 * RATE)))
    trimmed = samples[start:end]
    peak = max(map(abs, trimmed))
    rms = math.sqrt(sum(x*x for x in trimmed) / len(trimmed))
    gain = min(12., -21. - 20*math.log10(max(rms, 1e-12)), -6. - 20*math.log10(max(peak, 1e-12)))
    pcm = array.array("f", (x * 10 ** (gain / 20) for x in trimmed))
    transforms = {"decode": "W33 decode helper: mono float32 at 32000 Hz; no time/pitch change",
                  "source_samples_32000_mono": len(samples), "start_sample": start, "end_sample_exclusive": end,
                  "leading_trim_seconds": start / RATE, "trailing_trim_seconds": (len(samples)-end) / RATE,
                  "trim_policy": "Only edge silence below -72 dBFS 10 ms RMS; retain 30 ms lead / 200 ms tail; remove at most 200 ms lead / 350 ms tail; no hard duration crop",
                  "silence_rms_threshold_dbfs": -72, "gain_db": gain,
                  "gain_policy": "Aim RMS -21 dBFS, PCM peak <= -6 dBFS, boost <=12 dB; smallest permitted gain",
                  "fade_in_ms": 0, "fade_out_ms": 0,
                  "no_retime_pitch_stretch_concatenation": True}
    return pcm, helper.stats(samples), transforms


def encode(ffmpeg, pcm, path):
    command = [ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-f", "f32le",
               "-ar", str(RATE), "-ac", "1", "-i", "pipe:0", "-map_metadata", "-1", "-map_chapters", "-1",
               "-c:a", "libvorbis", "-q:a", "4", "-threads", "1", "-fflags", "+bitexact",
               "-flags:a", "+bitexact", "-ac", "1", "-ar", str(RATE), str(path)]
    subprocess.run(command, input=pcm.tobytes(), check=True, capture_output=True, timeout=30)
    return command


def ogg_info(data):
    require(data.startswith(b"OggS"), "Not Ogg")
    pos = data.index(b"\x01vorbis")
    channels, rate = data[pos+11], struct.unpack_from("<I", data, pos+12)[0]
    require(channels == 1 and rate == RATE, "Expected mono 32000 Hz Vorbis")
    # Inspect comment packet: only technical encoder comments can survive metadata stripping.
    pos = data.index(b"\x03vorbis") + 7
    size = struct.unpack_from("<I", data, pos)[0]; pos += 4
    vendor = data[pos:pos+size].decode("utf-8"); pos += size
    count = struct.unpack_from("<I", data, pos)[0]; pos += 4
    comments = []
    for _ in range(count):
        size = struct.unpack_from("<I", data, pos)[0]; pos += 4
        value = data[pos:pos+size].decode("utf-8"); pos += size
        require(value.split("=", 1)[0].lower() == "encoder", "Unexpected metadata in Vorbis comments")
        comments.append(value)
    return {"codec": "vorbis", "channels": channels, "sample_rate_hz": rate,
            "vorbis_vendor": vendor, "technical_comments": comments}


def output_stats(ffmpeg, helper, path):
    data = path.read_bytes()
    info = ogg_info(data)
    decoded = helper.decode(ffmpeg, path)
    measurement = helper.stats(decoded)
    require(measurement["sample_peak_dbfs"] <= -1.0 and measurement["clipped_samples"] == 0,
            "Post-Vorbis headroom/clipping failure: " + path.name)
    require(0 < len(decoded) / RATE <= MAX_DURATION, "Output duration exceeds limit")
    return {**measurement, **info, "decoded_samples": len(decoded), "bytes": len(data), "sha256": sha(data)}


def convert(row, ffmpeg, helper, output, fetch=False):
    source = source_path(row, fetch)
    pcm, original_stats, transforms = prepare(row, source, ffmpeg, helper)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Lossy overshoot is checked after every encode. Only reduce scalar gain.
    for attempt in range(3):
        command = encode(ffmpeg, pcm, output)
        measured = helper.stats(helper.decode(ffmpeg, output))
        if measured["sample_peak_dbfs"] <= -1 and measured["clipped_samples"] == 0:
            break
        correction = -3. - measured["sample_peak_dbfs"]
        pcm = array.array("f", (x * 10 ** (correction / 20) for x in pcm))
        transforms["gain_db"] += correction
    else:
        raise RuntimeError("Post-Vorbis headroom failed after three attempts")
    transforms["pcm_after_gain"] = helper.stats(pcm)
    require(transforms["pcm_after_gain"]["sample_peak_dbfs"] <= -6, "PCM headroom failure")
    transforms["encode_attempts"] = attempt + 1
    transforms["encoder"] = "libvorbis q4; mono 32000 Hz; one thread; metadata/chapters removed; bitexact"
    transforms["ffmpeg_command_template"] = ["<ffmpeg>" if i == 0 else "<owned-output.ogg>" if i == len(command)-1 else x for i, x in enumerate(command)]
    return {"event": row["event"], "variant": row["variant"], "original_name": row["name"],
            "drive_id": row["id"], "source_folder": row["source_folder"], "source_folder_id": row["source_folder_id"],
            "source_url": "https://drive.google.com/file/d/" + row["id"] + "/view",
            "source_folder_url": "https://drive.google.com/drive/folders/" + row["source_folder_id"],
            **row["pin"], "source_audio": original_stats, "transforms": transforms,
            "sound": sound_name(row), "asset_path": relative(asset_path(row)),
            "status": "named_uploader_action_candidate", "limitations": LIMITS[row["source_folder"]],
            "output": output_stats(ffmpeg, helper, output)}


def summary(records):
    return {"custom_event_keys": 15, "unique_ogg_files": len(records),
            "ogg_bytes": sum(r["output"]["bytes"] for r in records),
            "source_bytes": sum(r["source_bytes"] for r in records),
            "total_duration_seconds": round(sum(r["output"]["duration_seconds"] for r in records), 6),
            "maximum_duration_seconds": max(r["output"]["duration_seconds"] for r in records),
            "maximum_sample_peak_dbfs": max(r["output"]["sample_peak_dbfs"] for r in records),
            "minimum_headroom_db": -max(r["output"]["sample_peak_dbfs"] for r in records),
            "clipped_samples": sum(r["output"]["clipped_samples"] for r in records),
            "event_clip_counts": {event: count for event, _, _, count in GROUPS}}


def make_preview(manifest):
    rows = []
    for event, record in manifest["events"].items():
        rows.append("<section><h2>" + html.escape(event) + "</h2><p>" + html.escape(record["limitations"]) + "</p>")
        for clip in record["clips"]:
            # Relative URL resolves directly to the CURRENT resource, never an embedded/source copy.
            url = relpath(ROOT / clip["asset_path"], QA)
            label = f"{clip['source_folder']} / {clip['original_name']} — {clip['output']['duration_seconds']:.3f} s, peak {clip['output']['sample_peak_dbfs']:.2f} dBFS"
            rows.append('<article><label>' + html.escape(label) + '</label><audio controls preload="none" src="' + html.escape(url, quote=True) + '"></audio></article>')
        rows.append("</section>")
    document = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; media-src 'self' file:; style-src 'unsafe-inline'">
<title>W56 sword audio — manual review</title><style>body{font:16px system-ui;max-width:960px;margin:2rem auto;padding:0 1rem;background:#111923;color:#e7edf4}h1,h2{color:#b7dcff}h2{font-size:1.1rem}section{margin:2rem 0;border-top:1px solid #455466}article{padding:.6rem 0}label{display:block;margin-bottom:.4rem}audio{width:100%}p{line-height:1.5}</style>
<h1>W56 sword audio: 15 events / 51 clips</h1><p>No acoustic listening or native/game audition has been performed. Uploader action labels are the only identity evidence. Use each control to review the current asset. No autoplay, JavaScript, external scripts, or original source audio.</p>
<p>Half Truths is a proxy for Abide the Return / Goldtusk; the Crown Splitter folder is shared with Throne Cleaver; caster far-swing release is a generic candidate, not an exact near layer. Sample headroom checks do not measure intersample true peak. Final game timing and mix review belongs to the main integration.</p>
''' + "\n".join(rows) + "</html>\n"
    (QA / "audition.html").write_text(document, encoding="utf-8")


def verify(rows, ffmpeg, version, helper):
    manifest = read_json(MANIFEST)
    require(read_json(SIDECAR) == manifest, "Runtime sidecar / art manifest mismatch")
    require(manifest["soundDefinitions"] == definitions(rows), "Sound definition subset/contract mismatch")
    require(manifest["evidence_sha256"] == EVIDENCE_PINS, "Manifest evidence pin mismatch")
    require(manifest["ffmpeg_version"] == version, "Use the pinned ffmpeg version")
    require(manifest["ffmpeg_binary_sha256"] == sha(Path(ffmpeg).read_bytes()), "ffmpeg binary changed")
    require(list(manifest["events"]) == [g[0] for g in GROUPS], "Expected exactly 15 ordered events")
    records = [clip for event in manifest["events"].values() for clip in event["clips"]]
    require(len(records) == 51, "Expected exactly 51 saved clips")
    for row, record in zip(rows, records):
        path = asset_path(row)
        source_path(row)  # Offline, finite size, source SHA256 and HTML rejection.
        for key, value in row["pin"].items():
            require(record.get(key) == value, "Manifest source pin mismatch: " + key)
        require(record["event"] == row["event"] and record["variant"] == row["variant"], "Action mapping changed")
        require(record["sound"] == sound_name(row) and record["asset_path"] == relative(path), "Asset path changed")
        require(record["limitations"] == LIMITS[row["source_folder"]], "Identity limitation missing")
        require(output_stats(ffmpeg, helper, path) == record["output"], "Saved output measurement/hash mismatch: " + path.name)
        pcm, source_stats, transforms = prepare(row, ROOT / row["pin"]["private_path"], ffmpeg, helper)
        require(source_stats == record["source_audio"], "Saved source measurement mismatch")
        for key, value in transforms.items():
            if key != "gain_db":
                require(record["transforms"].get(key) == value, "Saved transform mismatch: " + key)
        saved_gain = record["transforms"]["gain_db"]
        require(saved_gain <= transforms["gain_db"], "Unsafe gain changed")
        if saved_gain != transforms["gain_db"]:
            pcm = array.array("f", (x * 10**((saved_gain-transforms["gain_db"])/20) for x in pcm))
        require(helper.stats(pcm) == record["transforms"]["pcm_after_gain"], "PCM measurement mismatch")
        require(record["output"]["decoded_samples"] == len(pcm), "Encoded action/tail sample count changed")
        require(record["transforms"]["pcm_after_gain"]["sample_peak_dbfs"] <= -6, "PCM peak exceeds -6 dBFS")
    require(set(ASSETS.rglob("*.ogg")) == {asset_path(row) for row in rows}, "Missing/extra W56 Oggs")
    calculated = summary(records)
    require(calculated == manifest["summary"] and calculated["ogg_bytes"] <= MAX_OGG_BYTES, "Summary/budget mismatch")
    preserved = shared_unchanged()
    return {"mode": "read_only_offline", "summary": calculated, "shared_baseline": preserved,
            "native_or_acoustic_audition": "NOT PERFORMED", "sample_peak_not_intersample_true_peak": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--verify", action="store_true")
    mode.add_argument("--check", action="store_true")
    network = parser.add_mutually_exclusive_group()
    network.add_argument("--offline", action="store_true", help="Default: require pinned private originals")
    network.add_argument("--fetch", action="store_true", help="Re-download only missing originals using saved SHA pins")
    parser.add_argument("--ffmpeg")
    args = parser.parse_args()
    require(not (args.fetch and (args.verify or args.check)), "Verification/check are always offline")
    rows = evidence()
    helper = load_helpers()
    ffmpeg = str(Path(helper.ffmpeg_path(args.ffmpeg)).resolve())
    version = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True, check=True, timeout=10).stdout.splitlines()[0]
    if args.verify or args.check:
        report = verify(rows, ffmpeg, version, helper)
        if args.check:
            # Writes only ephemeral files in the authorized private-source tree.
            with tempfile.TemporaryDirectory(prefix="w56-determinism-", dir=CACHE) as temporary:
                for row in rows:
                    expected = sha(asset_path(row).read_bytes())
                    for repeat in range(2):
                        record = convert(row, ffmpeg, helper, Path(temporary) / f"{row['id']}-{repeat}.ogg")
                        require(record["output"]["sha256"] == expected, "Non-deterministic regeneration: " + row["name"])
            report["deterministic_regenerations_per_clip"] = 2
            report["deterministic_comparisons"] = 102
        print(json.dumps(report, indent=2))
        return
    shared_unchanged()
    records = [convert(row, ffmpeg, helper, asset_path(row), args.fetch) for row in rows]
    totals = summary(records)
    require(totals["ogg_bytes"] <= MAX_OGG_BYTES, "W56 Ogg budget exceeded")
    manifest = {"schema_version": 1, "wave": "w56", "source_parent_folder_id": "1YqPN12gGOo__zpxJ-57G4WUCKHaoAzty",
                "authorization": "User-authorized finite 51-clip named action subset; no separate redistribution license inferred",
                "source_media_policy": "Originals stay private under run/private-sources/w56; only intended authorized Ogg assets are distributed",
                "evidence_sha256": EVIDENCE_PINS, "ffmpeg_version": version,
                "ffmpeg_binary_sha256": sha(Path(ffmpeg).read_bytes()),
                "helper": "scripts/audio/import_sounds_w33.py: decode/stats/ffmpeg_path only; importer main never called",
                "soundDefinitions": definitions(rows),
                "events": {event: {"source_folder": label, "limitations": LIMITS[label], "clips": [r for r in records if r["event"] == event]}
                           for event, label, _, _ in GROUPS},
                "runtime_contract": {
                    "namespace": "destiny", "definition_merge": "Main merges soundDefinitions into assets/destiny/sounds.json; this importer never writes shared definitions",
                    "selection": "Each event lists equal-weight variants; one action clip per play; stream=false; attenuation_distance=32; no sound registry registration implied",
                    "call_sites": "Main owns runtime action timing, selection, tests, language additions and final gate",
                    "subtitles_existing": ["subtitles.destiny.weapon.sword.fire"],
                    "subtitles_main_adds": ["subtitles.destiny.weapon.sword.guard", "subtitles.destiny.weapon.sword.heavy", "subtitles.destiny.weapon.sword.impact"],
                    "old_shared_definitions": "Pre-W56 entries and assets preserved, including weapon.sword.fire"},
                "audition_html": relative(QA / "audition.html"), "summary": totals,
                "limits": {"source_max_bytes_each": MAX_SOURCE_BYTES, "output_max_seconds_each": MAX_DURATION,
                           "output_total_budget_bytes": MAX_OGG_BYTES, "download_timeout_seconds": 45,
                           "encode_timeout_seconds": 30, "encode_max_attempts": 3},
                "verification_limits": "No native/game or acoustic audition performed. Uploader folder/filename action evidence only. Decode finite samples, mono/rate, sample peak and clipping checks do not establish intersample true peak, exact weapon identity, spatial mix or runtime sync."}
    dump(MANIFEST, manifest)
    dump(SIDECAR, manifest)
    make_preview(manifest)
    report = verify(rows, ffmpeg, version, helper)
    dump(QA / "measurements.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
