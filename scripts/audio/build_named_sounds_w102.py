#!/usr/bin/env python3
"""W102 exact named uploader audio. Default builds owned files; --verify is offline.

--verify renders twice in private temporary storage and compares every output byte.
--fetch only restores missing hash-pinned payloads through the pinned W33 downloader.
No shared definitions, Java, old assets, tests, build, server or client writes.
"""
from pathlib import Path
from html.parser import HTMLParser
import argparse
import array
import hashlib
import importlib.util
import io
import json
import math
import os
import re
import struct
import sys
import tempfile
import wave

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "art/weapons/w102/audio"
CACHE = ROOT / "run/private-sources/w102"
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/destiny/sounds/w102"
PROFILE = RES / "destiny/sounds/w102-reload.json"
HELPER = ROOT / "scripts/audio/import_sounds_w33.py"
TIMING_HELPER = ROOT / "scripts/audio/build_reload_sounds_w63.py"
FFMPEG = ROOT / "run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
HELPER_SHA = "e3f1dd846b69dcb5a5cad685f310ffb9a6b6a7d1ab7fbc1d11851557bca6911e"
TIMING_SHA = "e7ecfb853a9325d75713496984447870d64fca797217e4b9cbeddf76c9d28ed8"
FFMPEG_SHA = "6d175a4743ca50256e89a8cdd731100f9cee33bd79aeea46894d209410dc6617"
INPUT_PINS = {
    "source-pins.json": "6f7387393467c23171c19236b3fce65915e430b1758fc1e0d73a69f85649471f",
    "folder-discovery.json": "c784105fd9d39a03ad8e599642963647de2e018333917cb4664e89211c010fef",
    "event-contract.json": "a6f30fefa104485399e8b42e0be46ee3efa895fe1965ac6acce0af424eefb43f",
    "preserved-audio.json": "45f4bffbe2cd3915b5b068c517522254692d8f3895283a25cfebce04efaa7b7c",
}
WEAPONS = {
    "blast_furnace": ("pulse_rifle", "1_lzX2VeWtM9APWox0nRDqCbiHoEx65rE"),
    "chattering_bone": ("pulse_rifle", "1ZJiFDuXrgh8QBqaSfSNpEOyTCMBmeiSr"),
    "aishas_embrace": ("scout_rifle", "1cxZNF8D46mAb-iBWbJwxmqYzOu4NGl2g"),
    "long_arm": ("scout_rifle", "1_1pwacAXcVs6wJm7U9OuscnGbrGg9K7p"),
    "whispering_slab": ("bow", "1EnZCnW__Yu5QV3FxG0Ns_fUGCUR502Nk"),
    "retrofit_escapade": ("machine_gun", "1bAwsxY_CNiiiFKC8zzyZlt7UyAav4erF"),
}
TIMED = {"aishas_embrace": [46], "blast_furnace": [24, 43],
         "chattering_bone": [24, 34], "retrofit_escapade": [90]}
LIMITS = [
    "Exact uploader folder and Fire_1/Reload_1 labels establish selection, not independent acoustic identification.",
    "No playback, actual listening, game-session synchronization or client acoustic-output acceptance is claimed.",
    "Public Drive fetching was authorized; no redistribution license is inferred.",
    "Pulse Fire_1 may contain the uploader's native burst; it is not claimed to be a per-projectile isolated recording.",
    "Whole Long Arm Reload_1 is deliberately excluded: incremental insertion cannot use a full-magazine clip.",
    "Whispering Slab has no named Reload_1; Draw is never relabeled as reload.",
    "Timed clips retain existing W63 ticks, which are authored approximations; atempo may change transients.",
    "Audition WAVs are review-only concatenations, not runtime clips; RIFF cue labels and JSON give action/sample positions.",
    "Master must integrate the definition fragment and finite timed overlay; this generator never edits shared definitions or runtime code.",
]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def enc(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def read(path):
    return json.loads(path.read_bytes())


def relative(path):
    return str(path.relative_to(ROOT))


def load_helper(path, expected, name):
    require(sha(path.read_bytes()) == expected, "Helper drift: " + relative(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Rows(HTMLParser):
    """Extract only the visible public folder rows; no hidden application state."""
    def __init__(self):
        super().__init__()
        self.row, self.rows = None, []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("role") == "row":
            if self.row:
                self.rows.append(self.row)
            self.row = {"id": attrs.get("data-id"), "text": ""}

    def handle_data(self, data):
        if self.row:
            self.row["text"] += data + " "

    def close(self):
        super().close()
        if self.row:
            self.rows.append(self.row)
            self.row = None


def check_inputs(helper, fetch=False):
    require(sha(FFMPEG.read_bytes()) == FFMPEG_SHA, "ffmpeg actual payload SHA drift")
    for name, expected in INPUT_PINS.items():
        require(sha((ART / name).read_bytes()) == expected, "Input drift: " + name)
    preserved = read(ART / "preserved-audio.json")
    for path, expected in preserved.items():
        require(sha((ROOT / path).read_bytes()) == expected, "Legacy audio/tool/profile changed: " + path)
    pins, folders = read(ART / "source-pins.json"), read(ART / "folder-discovery.json")
    require(len(pins) == 10 and len(folders) == 6, "Expected 10 sources from six named folders")
    catalog = {x["id"]: x for x in read(RES / "destiny/weapons/w30.json")}
    require(len({p["driveId"] for p in pins}) == 10, "Duplicate payload ID")
    selected = {(id_, action) for id_ in WEAPONS for action in
                (["fire", "reload"] if id_ in TIMED else ["fire"])}
    require({(p["id"], p["action"]) for p in pins} == selected, "Named action coverage drift")
    require({f["id"] for f in folders} == set(WEAPONS), "Folder coverage drift")
    for folder in folders:
        id_ = folder["id"]
        family, fid = WEAPONS[id_]
        require(catalog[id_]["family"] == family and folder["family"] == family
                and folder["folderId"] == fid, "Authoritative family/folder mismatch")
        listing = ROOT / folder["privateHtml"]
        require(listing == CACHE / (fid + ".html"), "Listing path escape")
        require(sha(listing.read_bytes()) == folder["sha256"]
                and listing.stat().st_size == folder["bytes"], "Listing payload drift")
        parser = Rows()
        parser.feed(listing.read_text())
        parser.close()
        require(parser.rows == folder["rows"], "Visible listing extraction drift")
        require(bool(folder["parentEvidence"]), "Missing named parent evidence")
        for parent in folder["parentEvidence"]:
            path = ROOT / parent["path"]
            require(path.parent == CACHE and sha(path.read_bytes()) == parent["sha256"], "Parent evidence drift")
            require(parent["row"] in read(path) and parent["row"]["id"] == fid
                    and parent["row"]["folder"], "Named parent folder identity drift")
    helper.CACHE = CACHE
    for pin in pins:
        family, fid = WEAPONS[pin["id"]]
        action = pin["action"]
        name = action.capitalize() + "_1.mp3"
        require(pin["family"] == family and pin["folderId"] == fid
                and pin["originalName"] == name
                and pin["event"] == "weapon." + pin["id"] + "." + action,
                "Exact selection fields drift")
        folder = next(f for f in folders if f["id"] == pin["id"])
        row = next(r for r in folder["rows"] if r["id"] == pin["driveId"])
        require(row["text"].strip() == pin["uploaderRow"] and
                re.search(r"(?<!\S)" + re.escape(name) + r"(?!\S)", row["text"]), "Exact named row absent")
        require(any(p["row"]["name"] == pin["folder"] for p in folder["parentEvidence"]), "Folder name mismatch")
        source = ROOT / pin["privatePath"]
        require(source == CACHE / (pin["driveId"] + ".mp3"), "Source path escape")
        helper.download({"drive_id": pin["driveId"], "original_name": name,
                         "source_sha256": pin["sourceSha256"]}, offline=not fetch)
        payload = source.read_bytes()
        require(sha(payload) == pin["actualPayloadSha256"] == pin["sourceSha256"]
                and len(payload) == pin["bytes"], "Actual source bytes/hash drift")
        require(payload[:3] == b"ID3" or payload[0] == 255, "Unexpected MP3 payload type")
    old = read(RES / "destiny/sounds/w63-reload.json")["entries"]
    rows = [r for r in old if r["id"] in WEAPONS]
    require(sorted((r["id"], r["ticks"]) for r in rows) ==
            sorted((id_, t) for id_, ticks in TIMED.items() for t in ticks), "Finite W63 key set drift")
    for row in rows:
        family = WEAPONS[row["id"]][0]
        require(row["event"] == f"weapon.reload_w63.weapon.{family}.reload.{row['ticks']}", "W63 event form drift")
    return pins, rows


def definition(id_, action, sound):
    return {"subtitle": "subtitles.destiny.weapon." + WEAPONS[id_][0] + "." + action,
            "sounds": [{"name": sound, "stream": False, "attenuation_distance": 32}]}


def chunk(tag, payload):
    return tag + struct.pack("<I", len(payload)) + payload + (b"\0" if len(payload) % 2 else b"")


def audition(helper, paths):
    parts, positions, offset = array.array("f"), [], 0
    for index, (action, path) in enumerate(paths):
        pcm = helper.decode(str(FFMPEG), path)
        positions.append({"action": action, "label": action.upper(), "startSample": offset,
                          "samples": len(pcm), "startSeconds": offset / 32000})
        parts.extend(pcm)
        offset += len(pcm)
        if index + 1 < len(paths):
            parts.extend([0.] * 32000)
            offset += 32000
    stream = io.BytesIO()
    pcm16 = array.array("h", (round(max(-1., min(1., x)) * 32767) for x in parts))
    if sys.byteorder != "little":
        pcm16.byteswap()
    with wave.open(stream, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(32000)
        wav.writeframes(pcm16.tobytes())
    cue = struct.pack("<I", len(positions))
    labels = b"adtl"
    for i, pos in enumerate(positions, 1):
        cue += struct.pack("<II4sIII", i, pos["startSample"], b"data", 0, 0, pos["startSample"])
        labels += chunk(b"labl", struct.pack("<I", i) + pos["label"].encode() + b"\0")
    raw = stream.getvalue() + chunk(b"cue ", cue) + chunk(b"LIST", labels)
    raw = raw[:4] + struct.pack("<I", len(raw) - 8) + raw[8:]
    return raw, {"rate": 32000, "channels": 1, "sampleWidth": 2,
                 "silenceBetweenActionsSamples": 32000 if len(paths) > 1 else 0,
                 "positions": positions, "listened": False}


def generate(helper, timing, pins, old_rows):
    outputs, definitions, records, timed_records, auditions = {}, {}, [], [], []
    with tempfile.TemporaryDirectory(prefix="destiny-w102-") as temporary:
        scratch = Path(temporary)
        helper.ROOT = helper.RES = scratch
        bases = {}
        for pin in pins:
            id_, action = pin["id"], pin["action"]
            event = pin["event"]
            # Named events avoid the helper's Hammerhead-specific family crop/rationale.
            cfg = dict(event=event, drive_id=pin["driveId"], original_name=pin["originalName"],
                       source_folder=pin["folder"], source_folder_id=pin["folderId"],
                       source_sha256=pin["sourceSha256"], limitations=pin["limitations"])
            record = helper.convert(cfg, ROOT / pin["privatePath"], str(FFMPEG))
            path = scratch / record["asset_path"]
            require(record["output"]["sample_peak_dbfs"] <= -1 and record["output"]["clipped_samples"] == 0,
                    "Base decoded headroom failure")
            sound = f"destiny:w102/{id_}/{action}"
            dest = ASSETS / id_ / (action + ".ogg")
            outputs[dest] = path.read_bytes()
            definitions[event] = definition(id_, action, sound)
            record.update(id=id_, family=pin["family"], action=action, sound=sound,
                          asset_path=relative(dest), actualPayloadSha256=pin["actualPayloadSha256"],
                          conversionPolicyEvent=event)
            records.append(record)
            bases[(id_, action)] = path
        entries = []
        for old in old_rows:
            id_, ticks = old["id"], old["ticks"]
            source = bases[(id_, "reload")]
            source_metrics = timing.inspect(str(FFMPEG), source)
            target = ticks * 1600
            filters = timing.atempo_chain(source_metrics["decodedSamples"] / target)
            filters += [f"apad=whole_len={target}", f"atrim=end_sample={target}"]
            path = scratch / f"{id_}_reload_{ticks}.ogg"
            command = [str(FFMPEG), "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
                       "-f", "f32le", "-ar", "32000", "-ac", "1", "-i", "pipe:0", "-af", ",".join(filters),
                       "-map_metadata", "-1", "-map_chapters", "-1", "-c:a", "libvorbis", "-q:a", "4",
                       "-threads", "1", "-fflags", "+bitexact", "-flags:a", "+bitexact", "-ar", "32000", "-ac", "1", str(path)]
            raw = timing.decode(str(FFMPEG), source)
            timing.run(command, raw)
            measured = timing.inspect(str(FFMPEG), path, target)
            require(measured["granuleSamples"] == target and measured["decodedSamples"] <= target,
                    "Timed duration overshoot")
            event = f"weapon.reload_w102.{id_}.{ticks}"
            sound = f"destiny:w102/{id_}/reload_{ticks}"
            asset = f"assets/destiny/sounds/w102/{id_}/reload_{ticks}.ogg"
            row = {"id": id_, "ticks": ticks, "event": event, "sourceEvent": f"weapon.{id_}.reload",
                   "sourceSha256": sha(source.read_bytes()), "asset": asset}
            entries.append(row)
            definitions[event] = definition(id_, "reload", sound)
            outputs[RES / asset] = path.read_bytes()
            timed_records.append({**row, "replaces": old, "targetSamples": target, "filters": filters,
                                  "sourceMetrics": source_metrics, "output": measured})
        entries.sort(key=lambda r: (r["id"], r["ticks"]))
        profile = {"stage": "W102", "entries": entries}
        outputs[ART / "timed-profile.json"] = enc(profile)
        outputs[PROFILE] = enc(profile)
        for id_ in WEAPONS:
            paths = [(a, bases[(id_, a)]) for a in ["fire", "reload"] if (id_, a) in bases]
            wav, labels = audition(helper, paths)
            wavpath = ART / "audition" / (id_ + ".wav")
            labelpath = wavpath.with_suffix(".labels.json")
            outputs[wavpath], outputs[labelpath] = wav, enc(labels)
            auditions.append({"id": id_, "path": relative(wavpath), "labelsPath": relative(labelpath), **labels})
    outputs[ART / "event-definitions.json"] = enc(definitions)
    manifest = {"stage": "W102", "schemaVersion": 1,
                "counts": {"baseEvents": 10, "timedEvents": 6, "oggAssets": 16, "auditionWav": 6},
                "generatorSha256": sha(Path(__file__).read_bytes()), "inputPins": INPUT_PINS,
                "helperSha256": HELPER_SHA, "timingHelperSha256": TIMING_SHA, "ffmpegSha256": FFMPEG_SHA,
                "basePolicy": "Pinned W33 helper using named event IDs; mono 32000 Hz Vorbis q4/bitexact, envelope trim, fire cap 3s, RMS -21/peak -6 target/boost <=12dB; decoded peak <=-1dBFS.",
                "timedPolicy": "Pinned W63 atempo factorization, pitch preserved, apad/atrim to ticks*1600; threads=1, bitexact; EOS exact, decoded <=target and within 1024 samples; decoded peak <=-1dBFS.",
                "writePolicy": "Allowlisted W102 art/cache/assets/new profile only; private temporary rendering. Shared sounds.json is read-independent and never published.",
                "events": definitions, "records": records, "timedRecords": timed_records,
                "auditions": auditions, "omissions": read(ART / "event-contract.json")["omissions"],
                "limitations": LIMITS, "runtimeAudioAccepted": False,
                "outputs": {relative(p): {"sha256": sha(b), "bytes": len(b)} for p, b in outputs.items()}}
    outputs[ART / "implementation.json"] = enc(manifest)
    outputs[ART / "REPORT.md"] = report(manifest)
    return outputs, manifest


def report(manifest):
    lines = ["# W102 L1 named audio delivery", "",
             "10 named base events and six timed reload events; 16 new Ogg files, six labeled audition WAVs. Offline generation and byte verification only. No listening or runtime acceptance claim.", "",
             "Master integration: merge `event-definitions.json` into shared definitions; overlay the six `timed-profile.json` Clip entries before ReloadAudioProfile validation. `src/main/resources/destiny/sounds/w102-reload.json` is byte-identical to the art table. No Java or shared sound definitions were edited by this task.", "",
             "Timed keys: Aisha's Embrace 46; Blast Furnace 24/43; Chattering Bone 24/34; Retrofit Escapade 90. All ticks come unchanged from exact existing W63 entries. sourceEvent is weapon.<id>.reload and sourceSha256 is its converted base Ogg hash; actual raw MP3 hashes/bytes/type are separately recorded in source-pins.json.", "",
             "Long Arm and Whispering Slab have fire only. Long Arm Reload_1 exists but is not suitable for incremental insertion. Whispering Slab has Draw files but no named reload. Neither gets a reload asset, event or profile entry.", "",
             "Audition: open `audition/<id>.wav`; FIRE then RELOAD (where eligible), separated by exactly 32000 silent samples (one second). RIFF cue/LIST labels and matching .labels.json files identify action positions. Fire-only WAVs contain only FIRE.", "",
             "Reproduce: `rtk proxy python3 scripts/audio/build_named_sounds_w102.py`; verify: same command plus `--verify`. Verification checks all pinned originals and evidence, the 196 preserved audio/tool/profile files, exact output inventory, every generated byte, and two independent reconversions including Ogg serials. It needs private cached originals and the pinned local ffmpeg; it has no network access. Missing payloads can be restored explicitly with `--fetch` through the SHA-checking W33 downloader.", "",
             "Write enforcement: Python audit hook refuses non-owned writes; verify permits only private temporary writes. FFmpeg receives only private temporary output destinations. Existing shared definitions are snapshotted and compared at invocation boundaries; all historical Ogg/tool/profile bytes are checked against preserved-audio.json. No Gradle, jar, server, client or computer-use actions.", "",
             "Native child tool unavailable; no app workaround used.", "",
             "Evidence limits:", ""]
    lines += ["- " + item for item in LIMITS]
    lines += ["", "Generator and full toolchain/input/output hashes, filters, decoded peak/RMS/duration and profile replacement rows: `implementation.json`. Public folder rows and hash-pinned parent name evidence: `folder-discovery.json`. Exact integration names: `event-contract.json` and `event-definitions.json`.", ""]
    return "\n".join(lines).encode()


def allowed(path):
    return path == PROFILE or any(path.is_relative_to(p) for p in [ART, CACHE, ASSETS])


def enforce_writes(verify):
    temporary_root = Path(tempfile.gettempdir()).resolve()

    def check(path):
        if isinstance(path, int):
            return
        p = Path(os.fsdecode(path)).resolve()
        if p.is_relative_to(ROOT):
            require(not verify and allowed(p), "Forbidden repository write: " + str(p))
        else:
            require(p.is_relative_to(temporary_root) and
                    any(part.startswith("destiny-w102-") for part in p.parts), "Forbidden outside write: " + str(p))

    def audit(event, args):
        if event == "open":
            mode, flags = args[1], args[2]
            if (isinstance(mode, str) and any(x in mode for x in "wax+")) or (flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)):
                check(args[0])
        elif event in {"os.mkdir", "os.remove", "os.rmdir", "os.chmod", "os.utime"}:
            # shutil.rmtree emits paths relative to an opened private directory.
            if len(args) > 1 and isinstance(args[-1], int) and args[-1] not in {-1, 0} and not os.path.isabs(args[0]):
                return
            check(args[0])
        elif event in {"os.rename", "os.link", "os.symlink"}:
            check(args[0]); check(args[1])
        elif verify and event.startswith("socket."):
            raise ValueError("Offline verification refuses network access")
    sys.addaudithook(audit)


def inventory(outputs):
    expected = set(outputs) | {ART / p for p in INPUT_PINS}
    actual = {p for parent in [ART, ASSETS] for p in parent.rglob("*") if p.is_file()}
    if PROFILE.exists():
        actual.add(PROFILE)
    require(actual == expected, "Unexpected/missing W102 outputs: " + str(sorted(str(p) for p in actual ^ expected)))
    require(all(allowed(p) for p in outputs), "Output path outside ownership")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--verify", action="store_true")
    modes.add_argument("--fetch", action="store_true")
    args = parser.parse_args()
    shared = RES / "assets/destiny/sounds.json"
    before = shared.read_bytes()
    helper = load_helper(HELPER, HELPER_SHA, "w102_w33")
    timing = load_helper(TIMING_HELPER, TIMING_SHA, "w102_w63")
    enforce_writes(args.verify)
    pins, old_rows = check_inputs(helper, args.fetch)
    outputs, manifest = generate(helper, timing, pins, old_rows)
    if args.verify:
        repeated, _ = generate(helper, timing, pins, old_rows)
        require(outputs == repeated, "Nondeterministic reconversion (including Ogg serials)")
        inventory(outputs)
        for path, payload in outputs.items():
            require(path.read_bytes() == payload, "Output bytes drift: " + relative(path))
    else:
        require(all(allowed(p) for p in outputs), "Forbidden publish destination")
        existing = {p for parent in [ART, ASSETS] for p in parent.rglob("*") if p.is_file()}
        require(existing <= set(outputs) | {ART / n for n in INPUT_PINS}, "Unexpected owned files; refusing destructive cleanup")
        for path, payload in outputs.items():
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_bytes() != payload:
                path.write_bytes(payload)
        inventory(outputs)
    check_inputs(helper)
    require(shared.read_bytes() == before, "Shared sounds.json changed during invocation")
    print(json.dumps({"status": "PASS", "verified": args.verify, **manifest["counts"],
                      "preservedFiles": 196, "sharedWrites": 0, "runtimeAudioAccepted": False}))


if __name__ == "__main__":
    main()
