#!/usr/bin/env python3
"""Prepare W262's six streamed music assets, without changing existing outputs.

Requires Python 3.10+, rtk, and FFmpeg with libvorbis and ebur128.
Run via: rtk proxy python3 scripts/audio/prepare_w262_music.py --ffmpeg /path/to/ffmpeg
Use --output-root /new/staging/root to regenerate without overwriting the checkout.
Source exports are read-only. Only eight generated owned files are written; this
script is the ninth owned file. No game, build, audio-device, or Git commands run.
Exact output hashes depend on the recorded FFmpeg binary/version.
"""
from __future__ import annotations
import argparse
import array
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

RATE = 48000
ASSETS = Path("src/main/resources/assets/destiny_music")
SCRIPT = Path("scripts/audio/prepare_w262_music.py")
PROVENANCE = Path("art/audio/w262/provenance.json")
EVENTS = ("tower_80d73421", "tower_80d7341d", "tower_80d73424", "tower_80d73419", "crucible_intro", "crucible_result")
OUTPUTS = [ASSETS / "sounds.json", *[ASSETS / "sounds" / (e + ".ogg") for e in EVENTS], PROVENANCE]
# Pin the delivered OGG and original WEM, not just filenames or manifest claims.
PINNED = {
    "80D73421": ("561c742a26c8c0f123c64cacc286af139ceacf0b6c581cf05a4c6c55a6d9bb8a", "e4fe278e96322f0dd7cce5da4bbf87641a38a0cfab71ded91ca693da9d929f1e"),
    "80D7341D": ("c733063ec46ff36b8af4271d5f2583c20d1874ae459f1d2f45f48d380f763a8f", "73e9b833500bf6bc8840778a98f8052b77ab79e8abfebf895f06956d444cc25c"),
    "80D73424": ("19bfffeb87377057e2e34461cb9fb4d67ca28e3b15f588312c4b9f66324f6d78", "66de7e40681dac4a557921183beed056b7a3a3693fa5f61a6a934b21f42bcb43"),
    "80D73419": ("906b493d416def70bf997518246d9c3ee4200fba2e3f894120b9bbb5472bb294", "371dfbe24c02c09f209e87d65d07c74b98db54f4fb56b24523417eb1fdcad5c6"),
    "80D725C1": ("a05835f29a705dc04091cabc97af235ac224a8d299cd91305b5fcada20b0727f", "0c0860dacc8a8b6529e5a69daefd320187097270d318d572b13fe0183a0e1e4d"),
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def json_bytes(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()

def require(condition, message):
    if not condition:
        raise RuntimeError(message)

def ogg_info(data):
    """Read Vorbis identification and EOS granule; do not trust rounded log duration."""
    offset, samples, packet, header, serial = 0, None, bytearray(), None, None
    while offset < len(data):
        require(data[offset:offset + 4] == b"OggS", "Invalid OGG page")
        require(offset + 27 <= len(data), "Truncated OGG header")
        require(data[offset + 4] == 0, "Unsupported OGG version")
        flags = data[offset + 5]
        granule = struct.unpack_from("<Q", data, offset + 6)[0]
        page_serial = struct.unpack_from("<I", data, offset + 14)[0]
        if serial is None:
            serial = page_serial
        require(page_serial == serial, "Chained/multiple OGG streams are not supported")
        count = data[offset + 26]
        laces = data[offset + 27:offset + 27 + count]
        require(len(laces) == count, "Truncated segment table")
        pos = offset + 27 + count
        for size in laces:
            require(pos + size <= len(data), "Truncated OGG packet")
            if header is None:
                packet.extend(data[pos:pos + size])
                if size < 255:
                    require(packet[:7] == b"\x01vorbis", "Expected Ogg Vorbis")
                    header = {"codec": "vorbis", "channels": packet[11], "sample_rate": struct.unpack_from("<I", packet, 12)[0]}
            pos += size
        if flags & 4:
            samples = granule
        offset = pos
    require(header is not None and samples is not None, "Missing Vorbis header/EOS")
    require(header["channels"] == 2 and header["sample_rate"] == RATE, "Expected stereo 48 kHz")
    return {**header, "samples_per_channel": samples, "duration_exact": f"{samples}/{RATE}", "duration_seconds": samples / RATE}

def run(ffmpeg, arguments, data=None):
    result = subprocess.run(["rtk", "proxy", ffmpeg, "-hide_banner", "-nostdin", "-xerror", *arguments], input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    require(result.returncode == 0, result.stderr.decode(errors="replace"))
    return result

def measure(ffmpeg, data, filters="asetpts=N/SR/TB"):
    info = ogg_info(data)
    result = run(ffmpeg, ["-i", "pipe:0", "-map", "0:a:0", "-af", filters + ",ebur128=peak=true", "-c:a", "pcm_f32le", "-f", "f32le", "pipe:1"], data)
    pcm = array.array("f")
    pcm.frombytes(result.stdout)
    if sys.byteorder != "little":
        pcm.byteswap()
    require(len(pcm) % 2 == 0 and len(pcm) > 0, "Invalid stereo PCM length")
    require(all(math.isfinite(x) for x in pcm), "Non-finite decoded sample")
    peak = max(abs(x) for x in pcm)
    require(peak > 0, "Silent selection")
    summary = result.stderr.decode(errors="replace").rsplit("Summary:", 1)[-1]
    def field(pattern):
        found = re.search(pattern, summary)
        require(found is not None, "Missing EBU R128 measurement: " + summary)
        return float(found.group(1))
    frames = len(pcm) // 2
    return {"sample_rate": info["sample_rate"], "channels": info["channels"], "samples_per_channel": frames,
            "duration_exact": f"{frames}/{RATE}", "duration_seconds": frames / RATE,
            "integrated_lufs": field(r"I:\s+([-\d.]+) LUFS"), "loudness_range_lu": field(r"LRA:\s+([-\d.]+) LU"),
            "true_peak_dbtp": field(r"Peak:\s+([-\d.]+) dBFS"), "sample_peak_dbfs": 20 * math.log10(peak),
            "samples_at_or_above_full_scale": sum(abs(x) >= 1 for x in pcm), "full_decode_passed": True}

def check_absent(root):
    for path in OUTPUTS:
        require(not os.path.lexists(root / path), "Refusing existing output: " + str(root / path))
        require((root / path).resolve().is_relative_to(root), "Output parent escapes root: " + str(path))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    parser.add_argument("--output-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--tower-source", type=Path, default=Path("/Volumes/qf-ssd/Destiny-Tower-BGM-2026-10-29"))
    parser.add_argument("--intro-source", type=Path, default=Path("/Volumes/qf-ssd/Destiny-Crucible-Intro-Handoff-2026-10-29"))
    parser.add_argument("--crucible-source", type=Path, default=Path("/Volumes/qf-ssd/Crucible-Assets-2026-10-28"))
    args = parser.parse_args()
    require(shutil.which("rtk") is not None, "rtk is required")
    require(args.ffmpeg is not None, "Supply --ffmpeg or install FFmpeg on PATH")
    ffmpeg = shutil.which(args.ffmpeg) or args.ffmpeg
    root = args.output_root.resolve()
    for source_root in [args.tower_source, args.intro_source, args.crucible_source]:
        require(not root.is_relative_to(source_root.resolve()), "Output root cannot be inside read-only source")
    check_absent(root)
    version = run(ffmpeg, ["-version"]).stdout.decode().splitlines()[0]
    evidence_files = [(args.tower_source, name) for name in ["PROVENANCE.json", "TRACKS.json", "audio-conversion.json", "FILE_HASHES.json", "README.md"]]
    evidence_files += [(args.intro_source, name) for name in ["PROVENANCE.json", "AUDIO-CUES.json", "audio-conversion.json", "FILE_HASHES.json", "HANDOFF.md", "intro-package-graph.json", "cinematic-intro-labels.json", "intro-worldid-labels.json"]]
    evidence_files += [(args.crucible_source, name) for name in ["README.md", "audio-index.json", "provenance/music-index.json", "provenance/music-banks.json", "provenance/game-build.json"]]
    evidence = [{"root": str(base), "file": name, "sha256": sha((base / name).read_bytes())} for base, name in evidence_files]
    source_data, source_details = {}, {}
    for tag, pins in PINNED.items():
        base = args.intro_source if tag == "80D725C1" else args.tower_source
        ogg_path, raw_path = f"audio/ogg/{tag.lower()}.ogg", f"audio/raw/{tag}.wem"
        data, raw = (base / ogg_path).read_bytes(), (base / raw_path).read_bytes()
        require(sha(data) == pins[0] and sha(raw) == pins[1], "Source SHA mismatch: " + tag)
        conversion = next(x for x in json.loads((base / "audio-conversion.json").read_text()) if x["tag"] == tag)
        require(conversion["sha256"] == pins[0] and conversion["rawSha256"] == pins[1], "Conversion manifest mismatch")
        hashes = {x["file"]: x["sha256"] for x in json.loads((base / "FILE_HASHES.json").read_text())}
        require(hashes[ogg_path] == pins[0] and hashes[raw_path] == pins[1], "File manifest mismatch")
        info, metrics = ogg_info(data), measure(ffmpeg, data)
        require(info["samples_per_channel"] == metrics["samples_per_channel"], "Source granule/decode mismatch")
        source_data[tag] = data
        source_details[tag] = {"root": str(base), "ogg": ogg_path, "ogg_sha256": pins[0], "raw_wem": raw_path,
                               "raw_wem_sha256": pins[1], "bytes": len(data), "container": info,
                               "measurement": metrics, "manifest_hashes_match": True}
    tower_records = {x["tag"]: x for x in json.loads((args.tower_source / "TRACKS.json").read_text())}
    cue_records = [x for x in json.loads((args.intro_source / "AUDIO-CUES.json").read_text()) if x["maps"] == "Javelin-4"]
    intro_record = next(x for x in cue_records if x["wem"] == "80D725C1")
    blobs, tracks = {}, []
    for event in EVENTS:
        tower = event.startswith("tower_")
        tag = event[6:].upper() if tower else "80D725C1"
        total = source_details[tag]["container"]["samples_per_channel"]
        result = event == "crucible_result"
        start, end = (total - 8 * RATE if result else 0), total
        frames = end - start
        fade_in, fade_out = (12000, 48000) if tower else ((14400, 60000) if result else (1440, 16800))
        target = -23.0 if tower or result else -20.0
        treatment = (f"atrim=start_sample={start}:end_sample={end},asetpts=N/SR/TB,"
                     f"afade=t=in:ss=0:ns={fade_in}:curve=tri,afade=t=out:ss={frames-fade_out}:ns={fade_out}:curve=tri")
        before = measure(ffmpeg, source_data[tag], treatment)
        require(before["samples_per_channel"] == frames, "Trim/fade changed sample count")
        gain = round(min(target - before["integrated_lufs"], 3.0, -2.5 - before["true_peak_dbtp"]), 3)
        filters = treatment + f",volume={gain}dB:precision=double"
        arguments = ["-i", "pipe:0", "-map", "0:a:0", "-map_metadata", "-1", "-af", filters,
                     "-ar", str(RATE), "-ac", "2", "-c:a", "libvorbis", "-q:a", "3",
                     "-fflags", "+bitexact", "-flags:a", "+bitexact", "-f", "ogg", "pipe:1"]
        encoded = run(ffmpeg, arguments, source_data[tag]).stdout
        info, after = ogg_info(encoded), measure(ffmpeg, encoded)
        require(info["samples_per_channel"] == frames == after["samples_per_channel"], "Encoded duration mismatch")
        require(after["true_peak_dbtp"] <= -2.0 and after["samples_at_or_above_full_scale"] == 0, "Encoded peak exceeds ceiling")
        path = ASSETS / "sounds" / (event + ".ogg")
        blobs[path] = encoded
        tracks.append({"event": "destiny_music:" + event, "output": str(path), "sha256": sha(encoded), "bytes": len(encoded),
                       "encoded": info, "source_tag": tag, "source": source_details[tag],
                       "source_usage": "tower descent bank segment" if tower else "Javelin-4 map descent",
                       "source_link": tower_records[tag] if tower else intro_record,
                       "editorial_reuse": result, "official_victory_music": False,
                       "intended_use": "editorial results outro, not identified as original result/victory music" if result else ("editorial tower playlist selection" if tower else "single selected Javelin-4 descent variant for intro"),
                       "edit": {"start_sample_inclusive": start, "end_sample_exclusive": end, "sample_rate": RATE,
                                "start_seconds": start / RATE, "end_seconds": end / RATE,
                                "fade_in_samples": fade_in, "fade_out_samples": fade_out, "fade_curve": "linear",
                                "target_lufs": target, "gain_db": gain, "max_positive_gain_db": 3,
                                "pre_encode_true_peak_ceiling_dbtp": -2.5, "filter": filters,
                                "timestamps": "Rebuilt from sample number (N/SR/TB); supplied OGG timestamps produced non-monotonic DTS on direct encode. No samples removed or resampled.",
                                "compressor_or_dynamic_limiter": False},
                       "measurement_after_trim_and_fades_before_gain": before, "measurement_encoded_full_decode": after})
        print(f"{event}: {frames}/{RATE} s, {len(encoded)} bytes, {after['integrated_lufs']} LUFS, {after['true_peak_dbtp']} dBTP", flush=True)
    sounds = {event: {"sounds": [{"name": "destiny_music:" + event, "stream": True}]} for event in EVENTS}
    blobs[ASSETS / "sounds.json"] = json_bytes(sounds)
    total_bytes = sum(len(data) for path, data in blobs.items() if path.suffix == ".ogg")
    require(total_bytes < 7_000_000, "Audio exceeds 7 MB budget")
    provenance = {
        "schema_version": 1, "batch": "W262", "namespace": "destiny_music",
        "scope": {"owned_paths": [str(p) for p in [*OUTPUTS, SCRIPT]],
                  "integration_precondition_sha256": {str(p): None for p in [*OUTPUTS, SCRIPT]},
                  "precondition_meaning": "All nine paths were absent before W262 edits; integration must require absence. Generator refuses existing generated outputs.",
                  "full_worktree_refresh_completed": False, "existing_worktree_metadata_modified": False,
                  "note": "Scoped new assets only. Full refresh blocked by preserved out-of-scope WeaponListenerResendW93GameTests.java; no reset/export/build."},
        "tool": {"ffmpeg_version": version, "ffmpeg_binary_sha256": sha(Path(ffmpeg).read_bytes()),
                 "encoder": "libvorbis", "quality": 3, "sample_rate": RATE, "channels": 2,
                 "ogg_bitexact_flags": True, "source_decode": "Delivered OGG decoded to floating-point PCM; one additional lossy Vorbis encode. Original WEM retained read-only, hashed but not re-decoded here.",
                 "measurement": "FFmpeg ebur128=peak=true; LUFS/LRA/true peak rounded by FFmpeg to 0.1; exact sample count independently checked against Vorbis EOS granule.",
                 "script": str(SCRIPT), "script_sha256": sha(Path(__file__).read_bytes())},
        "source_evidence": evidence,
        "selection": {"tower": "Four longest stereo sources in TRACKS.json, in requested order. Original sequence/random rules and continuous residence trigger are not reconstructed.",
                      "intro": "80D725C1: documented Javelin-4 descent candidate, 12.3821041667 seconds. Selection is editorial, not a claim that this variant is always chosen in Destiny.",
                      "javelin_candidates": cue_records,
                      "result_research": {"genuine_result_cue_identified": False, "scope": "632 music entries, bank and sequence indexes in Crucible-Assets; intro cue/label/world-id indexes and 556957-node intro-package-graph.",
                                          "finding": "No authenticated result/victory-to-WEM mapping found. Iron Banner and racing banks contain unclassified segments, not proof of victory usage. Absence of mapping is not proof the original game lacks result music.",
                                          "chosen_fallback": "Final 384000 samples of Javelin-4 80D725C1, with 0.30s fade-in and 1.25s fade-out; explicitly editorial results outro.",
                                          "original_semantic_role": "map descent", "official_victory_music": False}},
        "runtime_handoff": {"tower_order": list(EVENTS[:4]), "natural_gap_seconds": 3,
                            "intro": "once at start of 20-second cutscene", "result": "once at start of 10-second results screen",
                            "runtime_volumes": {"tower": 0.5, "intro": 0.45, "result": 0.4},
                            "note": "Scheduling, music category, runtime gain, stop/lifecycle, and catalog are master-owned. Runtime gain is not baked into assets. stream:true is set for each event."},
        "tracks": tracks, "audio_total_bytes": total_bytes,
        "sounds_json_sha256": sha(blobs[ASSETS / "sounds.json"]),
        "validation": {"all_sources_pinned_and_manifest_verified": True, "all_six_full_decodes_passed": True,
                       "all_six_stereo_48000_vorbis": True, "all_exact_duration_checks_passed": True,
                       "encoded_true_peak_ceiling_dbtp": -2.0, "under_7000000_audio_bytes": True,
                       "auditory_listening_performed": False, "os_audio_playback_performed": False,
                       "client_or_server_control_performed": False, "minecraft_resource_pack_load_test_performed": False,
                       "build_performed": False,
                       "limits": "Decode/loudness/manifest/reference checks only; no auditory, musical-transition, in-game scheduling or pack-acceptance claim."}}
    blobs[PROVENANCE] = json_bytes(provenance)
    require(set(blobs) == set(OUTPUTS), "Unexpected write scope")
    check_absent(root)
    for path in OUTPUTS:
        target_path = root / path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        with target_path.open("xb") as handle:
            handle.write(blobs[path])
    for path in OUTPUTS:
        require(sha((root / path).read_bytes()) == sha(blobs[path]), "Written output hash mismatch")
    print(json.dumps({"audio_total_bytes": total_bytes, "output_sha256": {str(p): sha(b) for p, b in blobs.items()}, "script_sha256": provenance["tool"]["script_sha256"]}, indent=2))

if __name__ == "__main__":
    main()
