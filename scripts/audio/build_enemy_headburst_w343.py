#!/usr/bin/env python3
"""Read-only import of the 2026-11-08 headburst delivery; full-length positional mono derivatives."""
import argparse
import hashlib
import json
import shutil
import subprocess
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ART = ROOT / "art/audio/enemy-headburst-w343"
ASSETS = ROOT / "src/main/resources/assets/destiny_headburst"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path.home() / "Downloads/Destiny-Enemy-Headburst-SFX-2026-11-08")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--ffmpeg", type=Path)
    args = parser.parse_args()
    source = args.source.resolve()
    manifest = json.loads((source / "manifest.json").read_text())
    bindings = json.loads((source / "event-bindings.json").read_text())
    hashes = json.loads((source / "FILE-HASHES.json").read_text())
    bundled = ROOT / "run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
    ffmpeg = str(args.ffmpeg) if args.ffmpeg else str(bundled) if bundled.exists() else shutil.which("ffmpeg")
    if not ffmpeg:
        raise SystemExit("ffmpeg is required")
    expected = {wem for binding in bindings for wem in binding["wems"]}
    assert expected == {row["wem"] for row in manifest} and len(expected) == 40
    for row in manifest:
        for field in ("wav", "ogg"):
            assert digest(source / row[field]) == hashes[row[field]], row[field]
    if args.verify:
        saved = json.loads((ART / "manifest.json").read_text())
        assert len(saved["files"]) == 40
        for row in saved["files"]:
            assert digest(ROOT / row["output"]) == row["outputSha256"], row["output"]
        assert digest(ASSETS / "sounds.json") == saved["soundsSha256"]
        print("40 source WAV/OGG pairs and 40 shipped mono derivatives verified")
        return
    (ASSETS / "sounds").mkdir(parents=True, exist_ok=True)
    files = []
    for row in manifest:
        wav = source / row["wav"]
        with wave.open(str(wav)) as stream:
            rate, frames, channels = stream.getframerate(), stream.getnframes(), stream.getnchannels()
        assert channels == 2
        out = ASSETS / "sounds" / (row["wem"].lower() + ".ogg")
        subprocess.run([ffmpeg, "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav),
                        "-af", "pan=mono|c0=0.5*c0+0.5*c1", "-ar", str(rate),
                        "-map_metadata", "-1", "-threads", "1", "-fflags", "+bitexact", "-flags:a", "+bitexact",
                        "-c:a", "libvorbis", "-q:a", "5", str(out)], check=True)
        pcm = subprocess.check_output([ffmpeg, "-hide_banner", "-loglevel", "error", "-i", str(out),
                                       "-f", "s16le", "-acodec", "pcm_s16le", "-"])
        decoded = len(pcm) // 2
        assert abs(decoded - frames) <= 256 and any(pcm), row["wem"]
        assert out.read_bytes()[39] == 1, "Vorbis identification must report mono"
        files.append(dict(row, sourceWavSha256=digest(wav), sourceOggSha256=digest(source / row["ogg"]),
                          sourceFrames=frames, outputFrames=decoded, outputChannels=1,
                          output=out.relative_to(ROOT).as_posix(), outputSha256=digest(out)))
    sounds = {}
    for binding in bindings:
        sounds["headburst." + binding["key"]] = {"sounds": [
            {"name": "destiny_headburst:" + wem.lower(), "attenuation_distance": 24}
            for wem in binding["wems"]]}
    write_json(ASSETS / "sounds.json", sounds)
    write_json(ART / "event-bindings.json", bindings)
    write_json(ART / "source-manifest.json", manifest)
    write_json(ART / "source-hashes.json", hashes)
    ART.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source / "HANDOFF.md", ART / "SOURCE-HANDOFF.md")
    write_json(ART / "manifest.json", dict(batch="W343", delivery=source.name,
               sourceManifestSha256=digest(source / "manifest.json"),
               sourceBindingsSha256=digest(source / "event-bindings.json"),
               conversion="0.5*L + 0.5*R mono, original rate and complete duration; Vorbis q5; no trim/normalization",
               selection="One equal-weight Minecraft variant per event, not reconstructed Wwise weights/history",
               cabal="Shipped with an explicit entity-type tag hook; no Cabal actors currently authored",
               marauder="Uses Vandal family cue; family reuse, not an exact Marauder binding from this extraction",
               soundsSha256=digest(ASSETS / "sounds.json"), files=files))
    print(json.dumps(dict(variants=len(files), bytes=sum((ROOT / f["output"]).stat().st_size for f in files))))


if __name__ == "__main__":
    main()
