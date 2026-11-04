#!/usr/bin/env python3
"""Check pinned audio provenance and pack/JAR copies without downloading or playing anything."""
import argparse, hashlib, json, math, struct, zipfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def sha(data): return hashlib.sha256(data).hexdigest()
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jar", type=Path)
    parser.add_argument("--pack", type=Path)
    parser.add_argument("--client-pack", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    res = ROOT / "src/main/resources"
    manifest = json.loads((res / "destiny/sounds/w33.json").read_text())
    definitions = json.loads((res / "assets/destiny/sounds.json").read_text())
    tracked = {"assets/destiny/sounds.json"}
    files = set()
    for name, value in definitions.items():
        for sound in value["sounds"]:
            rid = sound if isinstance(sound, str) else sound["name"]
            namespace, path = rid.split(":", 1)
            assert namespace == "destiny" and path.startswith(("w33/", "w34/", "w36/", "w56/", "w63/reload/")) and ".." not in path
            relative = f"assets/{namespace}/sounds/{path}.ogg"
            files.add(relative); tracked.add(relative)
            data = (res / relative).read_bytes()
            assert data.startswith(b"OggS")
            index = data.index(b"\x01vorbis")
            assert data[index + 11] == 1
            assert struct.unpack_from("<I", data, index + 12)[0] == 32000
    for key, record in manifest["events"].items():
        relative = str(Path(record["asset_path"]).relative_to("src/main/resources"))
        data = (res / relative).read_bytes()
        assert sha(data) == record["output"]["sha256"], key
        assert record["output"]["clipped_samples"] == 0, key
        assert record["output"]["sample_peak_dbfs"] <= -1, key
        original = ROOT / "run/private-sources/w33" / (record["drive_id"] + Path(record["original_name"]).suffix)
        assert original.exists() and sha(original.read_bytes()) == record["source_sha256"], key
    seq_path = res / "destiny/sounds/w36.json"
    sequence = json.loads(seq_path.read_text())["events"] if seq_path.exists() else {}
    overlay_path = res / "destiny/sounds/w34.json"
    if overlay_path.exists():
        overlay = json.loads(overlay_path.read_text())
        original = ROOT / "run/private-sources/w34" / overlay["source"]["cache_name"]
        assert original.exists() and sha(original.read_bytes()) == overlay["source"]["sha256"]
        assert len(overlay["events"]) == 5
        for key, record in overlay["events"].items():
            assert key.startswith("hunter.void.super.")
            assert definitions[key]["sounds"][0]["name"] == sequence.get(key, record)["sound"]
            assert sha((ROOT / record["asset_path"]).read_bytes()) == record["output"]["sha256"]
            assert record["output"]["sample_peak_dbfs"] <= -1 and record["output"]["clipped_samples"] == 0
    for key, record in sequence.items():
        assert definitions[key]["sounds"][0]["name"] == record["sound"]
        assert sha((ROOT/record["asset_path"]).read_bytes()) == record["output"]["sha256"]
        assert record["output"]["clipped_samples"] == 0
    total = sum((res / p).stat().st_size for p in files)
    assert total < 30_000_000
    report = dict(custom_events=len(definitions), unique_ogg=len(files), ogg_bytes=total,
                  mapped_keys=sorted(definitions), missing_keys=[e["event"] for e in manifest["missing_events"]],
                  verification="Pinned original/output hashes, mono Vorbis, decoded measurements; not acoustic listening")
    for label, path in [("jar", args.jar), ("server_pack", args.pack), ("client_pack", args.client_pack)]:
        if path is None: continue
        with zipfile.ZipFile(path) as z:
            for p in tracked:
                if p.endswith("sounds.json"):
                    assert json.loads(z.read(p)) == json.loads((res / p).read_bytes()), (label, p)
                else: assert sha(z.read(p)) == sha((res / p).read_bytes()), (label, p)
        report[label] = dict(path=str(path.resolve()), sha256=sha(path.read_bytes()), identical_audio_resources=len(tracked)-1, sounds_json_semantically_equal=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k:v for k,v in report.items() if not k.endswith("keys")},indent=2))
if __name__ == "__main__": main()
