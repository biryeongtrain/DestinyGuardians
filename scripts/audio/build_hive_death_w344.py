#!/usr/bin/env python3
"""Import source-verified Hive death dissolves. soft/hard are not body/headshot aliases."""
import argparse
import json
import shutil
from pathlib import Path
from audio_variant_common import digest, write_json, mono_derivative

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "art/audio/hive-death-w344"
ASSETS = ROOT / "src/main/resources/assets/destiny_hive_death"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.home() / "Downloads/Destiny-Hive-Death-SFX-Comparison-2026-11-08")
    parser.add_argument("--ffmpeg", type=Path)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    source = args.source.resolve()
    rows = json.loads((source / "manifest.json").read_text())
    bindings = json.loads((source / "event-bindings.json").read_text())
    hashes = json.loads((source / "FILE-HASHES.json").read_text())
    assert len(bindings) == 8 and len(rows) == 36
    assert {w for b in bindings for w in b["wems"]} == {r["wem"] for r in rows}
    for row in rows:
        assert not row["headshot_only_confirmed"]
        for key in ["wav", "ogg"]:
            assert digest(source / row[key]) == hashes[row[key]], row[key]
    if args.verify:
        old = json.loads((ART / "manifest.json").read_text())
        assert len(old["files"]) == 36
        for row in old["files"]:
            assert digest(ROOT / row["output"]) == row["outputSha256"], row["wem"]
        assert digest(ASSETS / "sounds.json") == old["soundsSha256"]
        print("36 source WAV/OGG pairs and mono output hashes verified")
        return
    bundled = ROOT / "run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
    ffmpeg = args.ffmpeg or (bundled if bundled.exists() else shutil.which("ffmpeg"))
    if not ffmpeg:
        raise SystemExit("ffmpeg with libvorbis required")
    files = []
    for row in rows:
        out = ASSETS / "sounds" / (row["wem"].lower() + ".ogg")
        rate, frames, decoded = mono_derivative(ffmpeg, source / row["wav"], out)
        files.append(dict(row, sourceWavSha256=digest(source / row["wav"]),
                     sourceOggSha256=digest(source / row["ogg"]), sourceFrames=frames,
                     outputFrames=decoded, outputChannels=1, outputRate=rate,
                     output=out.relative_to(ROOT).as_posix(), outputSha256=digest(out)))
    sounds = {"death." + b["unit"] + "." + b["style"]: {"sounds": [
        {"name": "destiny_hive_death:" + wem.lower(), "attenuation_distance": 40}
        for wem in b["wems"]]} for b in bindings}
    write_json(ASSETS / "sounds.json", sounds)
    write_json(ART / "event-bindings.json", bindings)
    write_json(ART / "source-manifest.json", rows)
    write_json(ART / "source-hashes.json", hashes)
    shutil.copyfile(source / "README.md", ART / "SOURCE-README.md")
    write_json(ART / "manifest.json", dict(batch="W344", delivery=source.name,
               sourceManifestSha256=digest(source / "manifest.json"), sourceBindingsSha256=digest(source / "event-bindings.json"),
               headshot_only_confirmed=False, soft_hard_equals_body_headshot=False,
               conversion="0.5*L + 0.5*R mono at source rate/full duration; no trim, pitch change or normalization; Vorbis q5",
               playback="Ordinary death uses species soft event at gain 0.35; hard events remain explicitly separate",
               selection="One equal-weight Minecraft variant, not reconstructed Wwise weights/history",
               soundsSha256=digest(ASSETS / "sounds.json"), files=files))
    print(json.dumps(dict(variants=len(files), events=len(sounds), bytes=sum((ROOT / r["output"]).stat().st_size for r in files))))


if __name__ == "__main__":
    main()
