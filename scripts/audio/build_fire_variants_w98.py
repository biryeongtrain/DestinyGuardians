#!/usr/bin/env python3
"""Six pinned named-action variants; old Fire_1, family events and all gameplay stay unchanged.

--verify regenerates twice in temporary storage, checks exact bytes and active definitions.
No network, playback, Gradle, runtime or shared sounds.json writes. Master merges definitions.
"""
from pathlib import Path
import argparse
import array
import hashlib
import importlib.util
import io
import json
import math
import re
import sys
import tempfile
import wave

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "art/weapons/w98/audio"
RES = ROOT / "src/main/resources"
HELPER = ROOT / "scripts/audio/import_sounds_w33.py"
HELPER_SHA = "e3f1dd846b69dcb5a5cad685f310ffb9a6b6a7d1ab7fbc1d11851557bca6911e"
FFMPEG = ROOT / "run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
FFMPEG_SHA = "6d175a4743ca50256e89a8cdd731100f9cee33bd79aeea46894d209410dc6617"
WEAPONS = {
    "seventh_seraph_officer_revolver": ("hand_cannon", "1nrnK-zGDIanwW7xKpBUqjjwQ33I_j-2l", ".wav"),
    "steelfeather_repeater": ("auto_rifle", "1uebuIuIJZ2J5s5yiK99TC5RvGt70LfiM", ".wav"),
    "the_recluse": ("submachine_gun", "1cA-sz60bEIzxcYGQ9nUlJJX3E9AY4nS2", ".mp3"),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def enc(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode()


def require(value, why):
    if not value:
        raise RuntimeError(why)


def generate():
    require(sha(HELPER.read_bytes()) == HELPER_SHA, "W33 conversion helper drift")
    require(sha(FFMPEG.read_bytes()) == FFMPEG_SHA, "Pinned ffmpeg drift")
    pins = json.loads((ART / "source-pins.json").read_text())
    folders = json.loads((ART / "folder-discovery.json").read_text())
    require(len(pins) == 9 and len(folders) == 3, "Expected nine named sources from three exact folders")
    require(len({p["driveId"] for p in pins}) == 9, "Duplicate source ID")
    old = json.loads((RES / "destiny/sounds/w33.json").read_text())["events"]
    archived = ROOT / "docs/qa/2026-10-25/w98/before/src/main/resources/assets/destiny/sounds.json"
    w96 = ROOT / "art/qa/w96/implementation.json"
    require(sha(w96.read_bytes()) == "bbc7ae9a16f42d4b8a4983c29bd8b39eb8e7e8a12f9ec200cdfcc7f501784458", "W96 manifest drift")
    require(sha(archived.read_bytes()) == json.loads(w96.read_text())["clientAssets"]["src/main/resources/assets/destiny/sounds.json"],
            "Archived pre-W98 definitions drift")
    before = json.loads(archived.read_text())
    spec = importlib.util.spec_from_file_location("w98_w33_conversion", HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    outputs, definitions, records, auditions = {}, {}, [], []
    with tempfile.TemporaryDirectory(prefix="destiny-w98-audio-") as tmp:
        helper.ROOT = helper.RES = Path(tmp)
        for weapon, (family, folder_id, suffix) in WEAPONS.items():
            event = "weapon." + weapon + ".fire"
            original = old["weapon." + family + ".fire"]
            selected = sorted((p for p in pins if p["id"] == weapon), key=lambda p: p["variant"])
            require([p["variant"] for p in selected] == [1, 2, 3], "Exact ordered Fire_1/2/3 variants")
            folder = next(f for f in folders if f["folderId"] == folder_id)
            listing = ROOT / folder["privateHtml"]
            require(listing.parent == ROOT / "run/private-sources/w98", "Unexpected listing path")
            require(sha(listing.read_bytes()) == folder["sha256"], "Fetched listing drift")
            definition = {"subtitle": before[event]["subtitle"], "sounds": []}
            parts, positions, sample_offset = [], [], 0
            for pin in selected:
                variant = pin["variant"]
                name = "Fire_" + str(variant) + suffix
                require(pin["event"] == event and pin["family"] == family
                        and pin["folderId"] == folder_id and pin["originalName"] == name, "Named selection drift")
                row = next(r for r in folder["rows"] if r["id"] == pin["driveId"])
                require(re.search(r"(?<!\S)" + re.escape(name) + r"(?!\S)", row["text"]) is not None,
                        "Exact filename absent from same-folder visible listing")
                source = ROOT / pin["privatePath"]
                expected_dir = ROOT / ("run/private-sources/w33" if variant == 1 else "run/private-sources/w98")
                require(source == expected_dir / (pin["driveId"] + suffix), "Private source path escape")
                require(sha(source.read_bytes()) == pin["sourceSha256"] and source.stat().st_size == pin["bytes"],
                        "Pinned original bytes drift")
                if variant == 1:
                    require(pin["driveId"] == original["drive_id"]
                            and pin["sourceSha256"] == original["source_sha256"], "Retained W33 source drift")
                    sound = original["sound"]
                    path = RES / ("assets/destiny/sounds/" + sound.split(":")[1] + ".ogg")
                    require(sha(path.read_bytes()) == original["output"]["sha256"], "Original Fire_1 Ogg changed")
                    require(before[event]["sounds"] == [{"name": sound, "stream": False, "attenuation_distance": 32}],
                            "Pre-W98 exact event is not the pinned Fire_1-only definition")
                    record = {"id": weapon, "variant": 1, "retainedSound": sound,
                              "sha256": sha(path.read_bytes()), "output": original["output"], "transforms": "unchanged W33"}
                else:
                    cfg = dict(event="weapon." + family + ".fire", drive_id=pin["driveId"],
                               original_name=name, source_folder=pin["folder"], source_folder_id=folder_id,
                               source_sha256=pin["sourceSha256"],
                               limitations="Same named uploader weapon and Fire action; not independently audition verified. No inferred alternate attack.")
                    record = helper.convert(cfg, source, str(FFMPEG))
                    path = Path(tmp) / record["asset_path"]
                    sound = "destiny:w98/" + weapon + "/fire_" + str(variant)
                    destination = RES / ("assets/destiny/sounds/" + sound.split(":")[1] + ".ogg")
                    outputs[destination] = path.read_bytes()
                    record.update(id=weapon, variant=variant, event=event, conversionPolicyEvent="weapon." + family + ".fire",
                                  sound=sound, asset_path=str(destination.relative_to(ROOT)))
                    require(record["output"]["sample_peak_dbfs"] <= -1 and record["output"]["clipped_samples"] == 0,
                            "Decoded output peak/clipping policy")
                definition["sounds"].append({"name": sound, "stream": False, "attenuation_distance": 32})
                records.append(record)
                pcm = helper.decode(str(FFMPEG), path)
                require(all(math.isfinite(x) for x in pcm), "Non-finite audition PCM")
                positions.append({"variant": variant, "startSample": sample_offset, "samples": len(pcm), "sound": sound})
                parts.extend(pcm); parts.extend([0.] * 32000); sample_offset += len(pcm) + 32000
            definitions[event] = definition
            sink = io.BytesIO()
            with wave.open(sink, "wb") as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(32000)
                pcm16 = array.array("h", (round(max(-1, min(1, x)) * 32767) for x in parts))
                if sys.byteorder != "little": pcm16.byteswap()
                w.writeframes(pcm16.tobytes())
            outputs[ART / "audition" / (weapon + "_fire_123.wav")] = sink.getvalue()
            auditions.append({"id": weapon, "order": [1, 2, 3], "silenceSecondsAfterEach": 1,
                              "rate": 32000, "positions": positions})
    outputs[ART / "event-definitions.json"] = enc(definitions)
    manifest = dict(stage="W98", wholeGoalAchieved=False,
                    authorization="User-provided public Drive audio folder; no redistribution license inferred.",
                    sourceRoot="https://drive.google.com/drive/folders/1kWVlvhqvFkf_If5Q9Zd0mMIM1haa6u4l",
                    sourcePinsSha256=sha((ART / "source-pins.json").read_bytes()),
                    folderDiscoverySha256=sha((ART / "folder-discovery.json").read_bytes()),
                    generatorSha256=sha(Path(__file__).read_bytes()), helperSha256=HELPER_SHA, ffmpegSha256=FFMPEG_SHA, events=definitions,
                    policy="Three equal default-weight named alternatives. Vanilla client chooses a clip for one unchanged emitted sound event; no added shots, pitch change, concatenation or looping in pack clips.",
                    records=records, auditions=auditions,
                    limitations=["Filename/folder identity, not independent acoustic identification or runtime audio output proof.",
                                 "Other catalog weapons keep their documented family representatives.",
                                 "Dragonfly/Firefly surrogate and W97 HUD finding remain unresolved.",
                                 "Audition WAV concatenates pack-derived clips with silence only for user review; never a runtime clip."],
                    outputs={str(p.relative_to(ROOT)): sha(b) for p, b in outputs.items()})
    outputs[ART / "implementation.json"] = enc(manifest)
    return outputs, manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    outputs, manifest = generate()
    if args.verify:
        again, _ = generate()
        require(outputs == again, "Nondeterministic regenerated variants")
        for path, data in outputs.items(): require(path.read_bytes() == data, "Output drift: " + str(path))
        active = json.loads((RES / "assets/destiny/sounds.json").read_text())
        require(all(active[k] == v for k, v in manifest["events"].items()), "Active definitions not integrated")
    else:
        for path, data in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    print(json.dumps(dict(verified=args.verify, events=3, newOgg=6, retainedOgg=3, auditionWav=3,
                          runtimeAudioAccepted=False)))


if __name__ == "__main__":
    main()
