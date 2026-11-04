#!/usr/bin/env python3
"""Deterministic W77 generator controls in a disposable, manifest-complete clone.

Only this runner's optional report is written in the real checkout. Each child
runs the unchanged generator with --verify, denied Python filesystem mutations,
network operations and process escapes. Real inputs/outputs must remain intact.
No builds, Java/native launches, downloads or Git operations are performed.
"""
import sys
sys.dont_write_bytecode = True

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = "scripts/extract_dragonfly_w77.py"
PROFILE = "src/main/java/kim/biryeong/destiny/weapon/DragonflyProfile.java"
PROVENANCE = "art/weapons/w77/references/provenance.json"
RUNTIME = "src/main/resources/destiny/weapons/w77-dragonfly.json"
RESEARCH = "art/weapons/w77/references/research.json"
NOTES = "art/weapons/w77/reference-notes.md"
REPORT = "docs/qa/2026-10-24/w77/generator-controls.json"
MARKER = "W77_READ_ONLY_GUARD="

# The parent creates/restores fixtures. This guard applies to EVERY generator
# invocation, including all negative controls; it never permits child writes.
GUARD = r'''
import json, os, runpy, sys
sys.dont_write_bytecode = True
attempts = {"writeAttempts": 0, "networkAttempts": 0, "processAttempts": 0}
write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
mutations = {"os.mkdir", "os.remove", "os.rmdir", "os.rename", "os.link", "os.symlink",
             "os.truncate", "os.chmod", "os.chown", "os.utime", "shutil.copyfile",
             "shutil.copymode", "shutil.copystat", "shutil.rmtree"}
def deny(event, args):
    if event.startswith("socket.") or event in {"urllib.Request", "http.client.connect"}:
        attempts["networkAttempts"] += 1
        raise RuntimeError("W77 guard: network forbidden")
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.exec", "pty.spawn"}:
        attempts["processAttempts"] += 1
        raise RuntimeError("W77 guard: child process escape forbidden")
    writing = event in mutations
    if event == "open":
        mode, flags = args[1], args[2]
        writing = (isinstance(mode, str) and any(c in mode for c in "wax+")) or (
            isinstance(flags, int) and bool(flags & write_flags))
    if writing:
        attempts["writeAttempts"] += 1
        raise RuntimeError("W77 guard: filesystem mutation forbidden")
sys.addaudithook(deny)
sys.argv = [sys.argv[1], "--verify"]
try:
    runpy.run_path(sys.argv[0], run_name="__main__")
finally:
    print("W77_READ_ONLY_GUARD=" + json.dumps(attempts, sort_keys=True))
'''


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_state(path):
    stat = path.stat()
    return {"sha256": sha(path), "bytes": stat.st_size, "mtimeNs": stat.st_mtime_ns}


def snapshot(root):
    return {p.relative_to(root).as_posix(): file_state(p)
            for p in sorted(root.rglob("*")) if p.is_file()}


def run_control(clone, name, expected_code, expected_message):
    before = snapshot(clone)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="0", LC_ALL="C", TZ="UTC")
    proc = subprocess.run([sys.executable, "-I", "-B", "-c", GUARD, str(clone / GENERATOR)],
                          cwd=clone, env=env, capture_output=True, text=True, timeout=45)
    stdout = proc.stdout.replace(str(clone), "<clone>")
    stderr = proc.stderr.replace(str(clone), "<clone>")
    guard_lines = [line for line in stdout.splitlines() if line.startswith(MARKER)]
    require(len(guard_lines) == 1, name + ": missing/ambiguous read-only guard result")
    guard = json.loads(guard_lines[0][len(MARKER):])
    require(guard == {"writeAttempts": 0, "networkAttempts": 0, "processAttempts": 0},
            name + ": generator attempted a forbidden operation: " + str(guard))
    require(snapshot(clone) == before, name + ": child changed clone bytes, mtimes or file inventory")
    require(proc.returncode == expected_code, name + ": unexpected exit code/output: " + stdout + stderr)
    require(expected_message in stdout + stderr, name + ": expected diagnostic absent: " + stdout + stderr)
    clean_stdout = "\n".join(line for line in stdout.splitlines() if not line.startswith(MARKER))
    return {"name": name, "mode": "--verify", "exitCode": proc.returncode,
            "expectedExitCode": expected_code, "expectedDiagnostic": expected_message,
            "stdout": clean_stdout + ("\n" if clean_stdout else ""),
            "stderr": stderr, "guard": guard, "cloneBytesMtimesAndFilesUnchanged": True, "passed": True}


def audit(root):
    root = root.resolve()
    provenance = json.loads((root / PROVENANCE).read_bytes())
    sources = provenance["sourceHashes"]
    require(len(sources) == 8, "Expected all eight W77 pinned data inputs")
    outputs = {*provenance["outputHashes"], PROVENANCE}
    require(len(outputs) == 5 and RUNTIME in outputs and NOTES in outputs, "Unexpected W77 generated output set")
    files = {GENERATOR, PROFILE, *outputs}
    for key, record in sources.items():
        relative = Path(record["path"])
        require(not relative.is_absolute() and ".." not in relative.parts,
                "Clone-only audit requires checkout-relative cache inputs: " + key)
        path = root / relative
        require(path.resolve().is_relative_to(root), "Pinned input escapes checkout: " + key)
        require(sha(path) == record["sha256"] and path.stat().st_size == record["bytes"],
                "Real pinned source differs: " + key)
        files.add(relative.as_posix())
    require(RESEARCH in files, "Pinned research source is required")
    require(sha(root / GENERATOR) == provenance["generatorSha256"], "Generator differs from pinned provenance")
    require(sha(root / PROFILE) == provenance["profileSha256"], "Profile differs from pinned provenance")
    for name, expected in provenance["outputHashes"].items():
        require(sha(root / name) == expected, "Real generated output differs: " + name)
    before = {name: file_state(root / name) for name in sorted(files)}
    result = {"stage": "W77", "generator": GENERATOR, "runnerSha256": sha(Path(__file__).resolve()),
              "consumedPins": len(sources), "protectedFilesChecked": len(files),
              "controls": [], "scope": "Generator verification only; no gameplay, Java loading, build, native, audio or live-source verification.",
              "isolation": "Disposable independent copies, never hard links. Every --verify child runs under Python audit guards denying writes, sockets/HTTP and process escapes. Full clone hashes/mtimes/file inventories are checked around every child. Guards describe the unchanged Python generator, not a security sandbox for arbitrary native code."}
    try:
        with tempfile.TemporaryDirectory(prefix="destiny-w77-generator-controls-") as tmp:
            clone = Path(tmp).resolve()
            for name in sorted(files):
                target = clone / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(root / name, target)
            baseline = snapshot(clone)
            require({name: record["sha256"] for name, record in baseline.items()} ==
                    {name: record["sha256"] for name, record in before.items()}, "Clone content differs")
            result["controls"].append(run_control(clone, "positive", 0, "VERIFIED: W77; 63 selected; 678 sockets; 627 plug-set references; four exact-base rolls."))
            controls = [
                ("missing-source", RESEARCH, "missing", "No such file or directory"),
                ("corrupt-source", RESEARCH, "corrupt", "Source SHA256 mismatch: research"),
                ("corrupt-output", NOTES, "corrupt", "Generated bytes differ: " + NOTES),
                ("wrong-radius", RUNTIME, "wrong-radius", "Generated bytes differ: " + RUNTIME),
            ]
            for name, relative, mutation, diagnostic in controls:
                target = clone / relative
                original, stat = target.read_bytes(), target.stat()
                try:
                    if mutation == "missing":
                        target.unlink()
                    elif mutation == "wrong-radius":
                        value = json.loads(original)
                        require(value["perk"]["radiusMeters"] == 4.5, "Wrong-radius control needs canonical 4.5 m")
                        value["perk"]["radiusMeters"] = 3.0
                        target.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
                        require(json.loads(target.read_bytes())["perk"]["radiusMeters"] == 3.0,
                                "Wrong-radius mutation was not installed")
                    else:
                        target.write_bytes(original + b"\nW77 synthetic corruption\n")
                    record = run_control(clone, name, 1, diagnostic)
                    record["mutatedPath"] = relative
                    if mutation == "wrong-radius":
                        record["mutation"] = {"pointer": "/perk/radiusMeters", "from": 4.5, "to": 3.0,
                                              "meaning": "Valid JSON with stale radius must fail exact regeneration comparison; this does not execute Java profile validation."}
                    result["controls"].append(record)
                finally:
                    target.write_bytes(original)
                    os.utime(target, ns=(stat.st_atime_ns, stat.st_mtime_ns))
            require(snapshot(clone) == baseline, "Control fixture failed to restore to its pristine bytes/mtimes")
            result["cloneRestoredToBaseline"] = True
    finally:
        require(before == {name: file_state(root / name) for name in sorted(files)},
                "Real source/output bytes or mtimes changed during audit")
    result["realInputsOutputsBytesAndMtimesUnchanged"] = True
    result["protectedSha256"] = {name: state["sha256"] for name, state in before.items()}
    result["allPassed"] = all(c["passed"] for c in result["controls"]) and len(result["controls"]) == 5
    require(result["allPassed"], "Missing or failing control")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, help="Only permitted output: " + REPORT)
    args = parser.parse_args()
    try:
        expected = (args.root / REPORT).resolve()
        if args.out is not None:
            require(args.out.resolve() == expected, "Report output must be " + str(expected))
        result = audit(args.root)
        raw = json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
        if args.out is not None:
            expected.parent.mkdir(parents=True, exist_ok=True)
            expected.write_text(raw, encoding="utf-8")
        print(raw, end="")
    except (OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print("W77 generator controls failed: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
