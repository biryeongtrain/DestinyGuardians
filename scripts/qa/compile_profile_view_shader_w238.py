#!/usr/bin/env python3
r"""Compile/link W238 entity + item pairs with pack-first / native 26.3 fallback includes.

Usage (run by master against the generated pack, with an empty/new output directory):
  python3 -B scripts/qa/compile_profile_view_shader_w238.py \
    --pack /path/generated.zip --client /path/26.3/minecraft-client.jar --out /path/qa

Entity: W237's 8 families x 5 phases x 2 overlay states x 2 backends = 160 programs.
Item: 3 cutout states x 3 glint states x 5 phases x 2 backends = 90 programs.
The item matrix includes 0.5 cutout as additional branch coverage, and crosses glint
with alpha-only phases as a conservative superset, not a reachable-pipeline census.
Each program compiles AND links one .vert/.frag pair. All four core overrides must
exist in the supplied pack. Includes resolve from the pack first, then the native
26.3 JAR. result.json records each selected include's origin and SHA-256, including
pack-only helpers and overrides of vanilla includes (with native comparison SHA).

Vulkan uses GLSL 450 / Vulkan 1.2 / automatic bindings+locations, as in W237.
This is offline glslang validation, not a native GPU/Vulkan rendering certificate.
Uses only the Python standard library and an already installed glslangValidator.
Exit status: 0 all programs pass; 1 compile/link failure; 2 input/setup error.
"""

import argparse
import hashlib
import itertools
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


CORE = "assets/minecraft/shaders/core/"
INCLUDE = "assets/minecraft/shaders/include/"
STAGES = (("vsh", "vert"), ("fsh", "frag"))
BACKENDS = ("opengl", "vulkan")

# RenderPipelines.OIT_SNIPPET / LevelRenderer in 26.3: rank=2, 2**3=8
# coefficients, coefficient attachment count=8/4=2. Same phase matrix as W237.
OIT = {
    "OIT": "1",
    "OIT_WAVELET_RANK": "2",
    "OIT_COEFF_COUNT": "8",
    "OIT_COEFF_ATTACHMENT_COUNT": "2",
}
PHASES = (
    ("ordinary", {}),
    ("accumulate", OIT | {"OIT_ACCUMULATE": "1"}),
    ("depth-bounds", OIT | {"OIT_ALPHA_ONLY": "1", "OIT_DEPTH_BOUNDS": "1"}),
    ("transmittance", OIT | {"OIT_ALPHA_ONLY": "1", "OIT_TRANSMITTANCE": "1"}),
    ("additive", OIT | {"OIT_ACCUMULATE": "1", "OIT_ADDITIVE": "1"}),
)
ENTITY_FAMILIES = (
    ("base", {}),
    ("cutout-01", {"ALPHA_CUTOUT": "0.1"}),
    ("cutout-05", {"ALPHA_CUTOUT": "0.5"}),
    ("no-cardinal", {"NO_CARDINAL_LIGHTING": "1"}),
    ("emissive", {"EMISSIVE": "1"}),
    ("per-face", {"PER_FACE_LIGHTING": "1"}),
    ("glint-matrix", {"GLINT": "1", "APPLY_TEXTURE_MATRIX": "1"}),
    ("dissolve", {"DISSOLVE": "1"}),
)
CUTOUTS = (("base", {}), ("cutout-01", {"ALPHA_CUTOUT": "0.1"}),
           ("cutout-05", {"ALPHA_CUTOUT": "0.5"}))
# GLINT_SPECIAL is a native item vertex-format variant and always implies GLINT.
GLINTS = (("plain", {}), ("glint", {"GLINT": "1"}),
          ("glint-special", {"GLINT": "1", "GLINT_SPECIAL": "1"}))


def programs():
    """Deterministic, named inventory; no I/O and no mutation of define constants."""
    for (family, defines), (phase, oit), no_overlay, backend in itertools.product(
            ENTITY_FAMILIES, PHASES, (False, True), BACKENDS):
        overlay = "no-overlay" if no_overlay else "overlay"
        yield {
            "id": f"entity-{family}-{phase}-{overlay}-{backend}",
            "shader": "entity", "family": family, "phase": phase, "backend": backend,
            "defines": defines | oit | ({"NO_OVERLAY": "1"} if no_overlay else {}),
        }
    for (cutout, defines), (glint, glint_defines), (phase, oit), backend in itertools.product(
            CUTOUTS, GLINTS, PHASES, BACKENDS):
        yield {
            "id": f"item-{cutout}-{glint}-{phase}-{backend}",
            "shader": "item", "family": f"{cutout}-{glint}", "phase": phase, "backend": backend,
            "defines": defines | glint_defines | oit,
        }


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def uncomment(text):
    """Blank comments while preserving offsets/newlines for include/directive scanning."""
    def blank(match):
        return "".join("\n" if c == "\n" else " " for c in match.group())
    return re.sub(r"/\*.*?\*/|//[^\n]*", blank, text, flags=re.DOTALL)


class NativeSources:
    def __init__(self, custom, native):
        self.custom = custom
        self.native = native
        self.includes = {}
        self.source_ids = {}

    def source_id(self, path):
        return self.source_ids.setdefault(path, len(self.source_ids))

    def read(self, path, core=False):
        try:
            raw = self.custom.read(path)
            origin = "pack"
        except KeyError as pack_error:
            if core:
                raise ValueError(f"Missing generated pack core override: {path}") from pack_error
            try:
                raw = self.native.read(path)
                origin = "native"
            except KeyError as native_error:
                raise ValueError(f"Missing include in both pack and native 26.3 JAR: {path}") from native_error
        if not core:
            entry = {"source": origin, "sha256": sha256(raw)}
            if origin == "pack":
                try:
                    entry["native_sha256"] = sha256(self.native.read(path))
                except KeyError:
                    pass  # Valid pack-only helper, e.g. minecraft:displayhud.glsl.
            self.includes[path] = entry
        return raw.decode("utf-8-sig").replace("\r\n", "\n")

    def expand(self, text, path, stack=()):
        """Expand effective pack/native includes with numeric #line provenance."""
        if path in stack:
            raise ValueError("Include cycle: " + " -> ".join((*stack, path)))
        source_id = self.source_id(path)
        clean_lines = uncomment(text).splitlines(keepends=True)
        original_lines = text.splitlines(keepends=True)
        out = []
        for line_number, (clean, original) in enumerate(zip(clean_lines, original_lines), 1):
            if not re.match(r"\s*#\s*include\b", clean):
                out.append(original)
                continue
            match = re.fullmatch(r"\s*#\s*include\s*<([^>\n]+)>\s*", clean)
            if not match:
                raise ValueError(f"Unsupported include at {path}:{line_number}: {original.strip()}")
            name = match[1]
            namespace, relative = name.split(":", 1) if ":" in name else ("minecraft", name)
            if not re.fullmatch(r"[a-z0-9_.-]+", namespace) or not re.fullmatch(r"[a-z0-9_./-]+", relative) \
                    or any(part in ("", ".", "..") for part in relative.split("/")):
                raise ValueError(f"Invalid include resource name {name!r} at {path}:{line_number}")
            included_path = f"assets/{namespace}/shaders/include/{relative}"
            included = self.read(included_path)
            included_id = self.source_id(included_path)
            out.append(f"#line 1 {included_id}\n")
            out.append(self.expand(included, included_path, (*stack, path)).rstrip("\n") + "\n")
            out.append(f"#line {line_number + 1} {source_id}\n")
        return "".join(out)


def prepare(text, defines, backend):
    """Set backend version; inject the SAME defines into both shader stages."""
    clean = uncomment(text)
    version = re.search(r"(?m)^[ \t]*#version[ \t]+330[ \t]*(?:core[ \t]*)?$", clean)
    if not version or clean[:version.start()].strip():
        raise ValueError("Expected native #version 330 as first shader directive")
    # Include expansion preserves the top-level #version. #define before #extension
    # is legal; insert immediately after #version so every include sees all defines.
    end = text.find("\n", version.end())
    if end < 0:
        end = len(text)
    selected_version = "450" if backend == "vulkan" else "330"
    header = f"#version {selected_version}\n"
    header += "".join(f"#define {key} {value}\n" for key, value in sorted(defines.items()))
    # Restore source line numbers after inserting defines / replacing #version.
    header += f"#line {text[:end].count(chr(10)) + 2} 0\n"
    return text[:version.start()] + header + text[end + 1:]


def load_sources(pack, client):
    """Read-only preflight: version, four core overrides, effective includes + origins."""
    with zipfile.ZipFile(pack) as custom, zipfile.ZipFile(client) as native:
        for archive, label in ((custom, "pack"), (native, "client")):
            names = archive.namelist()
            if len(names) != len(set(names)):
                raise ValueError(f"Duplicate ZIP entries in {label}")
        version = json.loads(native.read("version.json"))
        if version.get("id") != "26.3":
            raise ValueError(f"Expected native client 26.3, got {version.get('id')!r}")
        reader = NativeSources(custom, native)
        sources = {}
        core_hashes = {}
        for shader in ("entity", "item"):
            for ext, _ in STAGES:
                path = CORE + shader + "." + ext
                text = reader.read(path, core=True)
                core_hashes[path] = sha256(custom.read(path))
                # Each top-level file uses GLSL source id 0 for readable diagnostics.
                reader.source_ids = {path: 0}
                expanded = reader.expand(text, path)
                # Check header now rather than after creating output directories.
                prepare(expanded, {}, "opengl")
                sources[shader, ext] = (expanded, dict(reader.source_ids))
        metadata = {
            "native_version": version["id"],
            "core_sha256": core_hashes,
            "includes": dict(sorted(reader.includes.items())),
            "native_include_sha256": {path: entry["sha256"] for path, entry in sorted(reader.includes.items())
                                      if entry["source"] == "native"},
            "pack_include_sha256": {path: entry["sha256"] for path, entry in sorted(reader.includes.items())
                                    if entry["source"] == "pack"},
            "include_policy": "pack first, native 26.3 fallback; selected source and raw-byte SHA-256 recorded",
        }
        return sources, metadata


def run(pack, client, out, validator, timeout=30.0):
    pack, client, out = (Path(p).expanduser().resolve() for p in (pack, client, out))
    if not (timeout > 0 and timeout < float("inf")):
        raise ValueError("--timeout must be finite and greater than zero")
    executable = shutil.which(str(validator))
    if executable is None:
        raise ValueError(f"glslangValidator executable not found: {validator}")
    executable = str(Path(executable).resolve())
    # Finish input validation BEFORE writing anything.
    sources, metadata = load_sources(pack, client)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError(f"--out must be an empty or new directory: {out}")
    out.mkdir(parents=True, exist_ok=True)
    results = []
    for program in programs():
        directory = out / program["id"]
        directory.mkdir()
        files, source_maps = [], {}
        for ext, stage in STAGES:
            expanded, source_map = sources[program["shader"], ext]
            text = prepare(expanded, program["defines"], program["backend"])
            path = directory / (program["shader"] + "." + stage)
            path.write_text(text, encoding="utf-8")
            files.append(str(path))
            source_maps[stage] = {str(number): name for name, number in source_map.items()}
        options = ["--target-env", "vulkan1.2", "--amb", "--aml"] if program["backend"] == "vulkan" else []
        command = [executable, *options, "-l", *files]
        try:
            completed = subprocess.run(command, capture_output=True, text=True, cwd=directory, timeout=timeout)
            code = completed.returncode
            output = completed.stdout + completed.stderr
        except subprocess.TimeoutExpired as error:
            code = None
            parts = (error.stdout or "", error.stderr or "")
            captured = "".join(p.decode("utf-8", errors="replace") if isinstance(p, bytes) else p for p in parts)
            output = f"Timed out after {timeout}s\n{captured}"
        result = program | {"ok": code == 0, "returncode": code, "command": command,
                            "output": output, "source_map": source_maps}
        results.append(result)
        print(f"{'PASS' if result['ok'] else 'FAIL'} {program['id']}", file=sys.stderr, flush=True)
    failures = [r for r in results if not r["ok"]]
    summary = {
        "programs": len(results), "passed": len(results) - len(failures), "failed": len(failures),
        "by_shader": {shader: {"programs": sum(r["shader"] == shader for r in results),
                              "failed": sum(r["shader"] == shader and not r["ok"] for r in results)}
                      for shader in ("entity", "item")},
    }
    report = metadata | {"summary": summary, "pack": str(pack), "client": str(client),
                         "pack_sha256": file_sha256(pack), "client_sha256": file_sha256(client),
                         "validator": executable, "results": results,
                         "limitation": "Offline compile/link matrix; native GPU render and reachable pipeline census unverified."}
    (out / "result.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary | {"report": str(out / "result.json"), "failures": [r["id"] for r in failures]}))
    return 1 if failures else 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pack", required=True, type=Path, help="Master-generated resource pack ZIP")
    parser.add_argument("--client", required=True, type=Path, help="Exact native 26.3 client JAR")
    parser.add_argument("--out", required=True, type=Path, help="Empty/new directory for expanded stages, SPIR-V and result.json")
    parser.add_argument("--validator", default=shutil.which("glslangValidator") or "/opt/homebrew/bin/glslangValidator")
    parser.add_argument("--timeout", type=float, default=30.0, help="Per linked program timeout in seconds (default: 30)")
    args = parser.parse_args(argv)
    try:
        return run(args.pack, args.client, args.out, args.validator, args.timeout)
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
