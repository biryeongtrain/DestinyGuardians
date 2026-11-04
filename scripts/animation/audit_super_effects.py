#!/usr/bin/env python3
"""Audit the delivered effect links with stdlib only; never decode guessed binary fields.

rtk proxy python3 -B scripts/animation/audit_super_effects.py --source-root DELIVERY \
    --json REPORT.json --markdown REPORT.md

Additional --components-json files must use the delivered player-sequences.json
shape: [{"component": TAG, "nodes": [{"type": "SSequenceParticleSystem",
"particles": [TAG]}]}]. --entities-json uses entity-index.json's list shape.
These are explicit supplemental evidence, never generated from direct claims.
Exit 1: contradictions/missing assets; 2: --require-substantiated found evidence
gaps (or invalid CLI/input); 0: report completed without errors, possibly partial.
File existence/nonzero size does not certify FBX, PNG, shaders or GPU simulation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path


TAG = re.compile(r"^[0-9A-Fa-f]{8}$")
PRIORITY = ("hunter_arc_staff", "hunter_shadowshot")
EVENT_FIELDS = ("type", "startFrame", "marker", "eventTag", "path")


def is_tag(value):
    return isinstance(value, str) and bool(TAG.fullmatch(value)) and value.upper() != "FFFFFFFF"


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def sequence_path(value):
    return isinstance(value, str) and value.lower().endswith((".sequence.tft", ".fx_sequence.tft"))


class Audit:
    def __init__(self, root):
        self.root = Path(root).resolve(strict=True)
        self.inputs = {}
        self.issues = []
        self.files = {}

    def issue(self, severity, code, location, detail):
        self.issues.append(dict(severity=severity, code=code, location=location, detail=detail))

    def read(self, path):
        path = Path(path)
        if not path.is_absolute():
            path = self.root / path
        data = path.read_bytes()
        self.inputs[str(path)] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        return data.decode("utf-8-sig")

    def load(self, path, kind):
        value = json.loads(self.read(path))
        if not isinstance(value, kind):
            raise ValueError(f"{path}: expected {kind.__name__}")
        return value

    def file(self, relative, location):
        """Check a delivered path; reject escape paths, including escaping symlinks."""
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root):
            self.issue("error", "unsafe_asset_path", location, str(relative))
            return dict(path=str(relative), exists=False, bytes=0)
        key = path.relative_to(self.root).as_posix()
        if key not in self.files:
            size = path.stat().st_size if path.is_file() else 0
            self.files[key] = dict(path=key, exists=path.is_file(), bytes=size)
        result = self.files[key]
        if not result["exists"] or not result["bytes"]:
            self.issue("error", "missing_or_empty_asset", location, key)
        return result

    def raw(self, tag, location):
        if not is_tag(tag):
            self.issue("error", "invalid_tag", location, repr(tag))
            return False
        f = self.file(f"raw/{tag}.bin", location)
        return f["exists"] and f["bytes"] > 0

    def index(self, rows, field, location):
        result = {}
        for i, row in enumerate(rows):
            if not isinstance(row, dict) or not is_tag(row.get(field)):
                raise ValueError(f"{location}[{i}]: expected {field} tag")
            key = row[field]
            if key in result and result[key] != row:
                self.issue("error", "conflicting_evidence", f"{location}[{i}]", key)
            result[key] = row
        return result

    def run(self, components_json=(), entities_json=()):
        manifest = self.load("manifest.json", dict)
        clips = self.index(manifest["clips"], "id", "manifest.clips")
        direct = self.load("provenance/direct-super-particles.json", list)
        seeds = self.load("provenance/super-event-seeds.json", list)
        frames = self.index(self.load("provenance/frame-events.json", list), "tag", "frame-events")
        graph = self.load("provenance/effects-graph.json", dict)
        exports = self.index(self.load("provenance/effects-results.json", list), "particle", "effects-results")
        entities = self.load("provenance/entity-index.json", list)
        for path in entities_json:
            entities.extend(self.load(path, list))
        entities = self.index(entities, "entity", "entities")
        components = self.load("provenance/player-sequences.json", list)
        for path in components_json:
            components.extend(self.load(path, list))
        components = self.index(components, "component", "components")
        csv_rows = list(csv.DictReader(self.read("effects/particle-index.csv").splitlines()))
        particles = self.index(csv_rows, "particle", "particle-index.csv")
        graph_particles = set(graph["particles"])
        reported = {d["particle"] for d in direct if is_tag(d.get("particle"))}
        if manifest.get("summary", {}).get("directSuperLinkedParticles") != len(reported):
            self.issue("error", "reported_count_mismatch", "manifest.summary", str(len(reported)))
        for label, tags in [("effects-results", set(exports)), ("effects-graph", graph_particles)]:
            if set(particles) != tags:
                self.issue("error", "particle_inventory_mismatch", label,
                           f"CSV-only={sorted(set(particles)-tags)}; other-only={sorted(tags-set(particles))}")

        seed_results = []
        for i, seed in enumerate(seeds):
            loc = f"super-event-seeds[{i}]"
            clip = clips.get(seed.get("clip"), {})
            event = {k: seed.get(k) for k in EVENT_FIELDS}
            valid = True
            if seed.get("group") not in clip.get("groups", []):
                self.issue("error", "seed_clip_group_mismatch", loc, str(seed))
                valid = False
            if event["type"] != "S80808C13" or not is_tag(event["eventTag"]):
                self.issue("error", "invalid_seed_event", loc, str(event))
                valid = False
            for source, events in [("manifest", clip.get("events", [])),
                                   ("frame-events", frames.get(seed.get("clip"), {}).get("events", []))]:
                if not any(all(e.get(k) == v for k, v in event.items()) for e in events):
                    self.issue("error", "seed_event_not_found", loc, source)
                    valid = False
            valid = self.raw(seed.get("eventTag"), loc) and valid
            valid = self.raw(seed.get("clip"), loc) and valid
            seed_results.append(dict(seed=seed, event_and_raw_supported=valid))

        typed_refs = []
        for component, data in sorted(components.items()):
            self.raw(component, f"components/{component}")
            for i, node in enumerate(data.get("nodes", [])):
                if node.get("type") != "SSequenceParticleSystem":
                    continue
                refs = node.get("particles")
                if not isinstance(refs, list):
                    self.issue("error", "invalid_particle_node", f"components/{component}/{i}", str(refs))
                    continue
                for particle in refs:
                    ok = self.raw(particle, f"components/{component}/{i}")
                    if particle not in particles:
                        self.issue("error", "typed_particle_not_exported", f"components/{component}/{i}", str(particle))
                        ok = False
                    typed_refs.append(dict(component=component, node_index=i, particle=particle,
                                           assets_present=ok, super_ownership="not_implied_by_component_reference"))

        links = []
        for i, row in enumerate(direct):
            loc = f"direct-super-particles[{i}]"
            required = ("clip", "group", "sequence", "component", "particle", "nodeName", "start", "duration")
            if any(k not in row for k in required):
                self.issue("error", "incomplete_direct_claim", loc, str(row))
                links.append(dict(index=i, claim=row, status="invalid", missing_evidence=[]))
                continue
            errors_before = sum(x["severity"] == "error" for x in self.issues)
            matches = [s for s in seed_results if all(s["seed"].get(k) == row[v] for k, v in
                       [("clip", "clip"), ("group", "group"), ("eventTag", "sequence")])]
            if not matches or not all(s["event_and_raw_supported"] for s in matches):
                self.issue("error", "unsubstantiated_direct_event", loc, "No matching supported clip/group/event seed")
            for key in ("clip", "sequence", "component", "particle"):
                self.raw(row[key], f"{loc}/{key}")
            if row["particle"] not in particles:
                self.issue("error", "direct_particle_not_exported", loc, row["particle"])
            missing = []
            if row["sequence"] != row["component"]:
                entity = entities.get(row["sequence"])
                if entity is None:
                    missing.append("event_entity_components_json_absent")
                elif row["component"] not in entity.get("components", []):
                    self.issue("error", "event_component_mismatch", loc, row["component"])
            component = components.get(row["component"])
            if component is None:
                missing.append("typed_component_nodes_json_absent")
            elif not any(r["component"] == row["component"] and r["particle"] == row["particle"] for r in typed_refs):
                self.issue("error", "component_particle_mismatch", loc, row["particle"])
            for key in ("start", "duration"):
                if not finite(row[key]) or row[key] < 0:
                    self.issue("error", "invalid_sequence_time", f"{loc}/{key}", repr(row[key]))
            if missing:
                self.issue("unresolved", "unsubstantiated_direct_chain", loc, ", ".join(missing))
            has_errors = sum(x["severity"] == "error" for x in self.issues) > errors_before
            links.append(dict(index=i, claim=row,
                              status="contradicted_or_dangling" if has_errors else
                              "reported_only" if missing else "json_chain_substantiated",
                              missing_evidence=missing,
                              event_occurrences=[s["seed"] for s in matches],
                              timing=dict(start=row["start"], duration=row["duration"],
                                          unit="unresolved", synchronization="unresolved",
                                          numeric_values="provider_claim_not_independently_decoded")))

        groups_by_particle = defaultdict(set)
        for d in direct:
            if is_tag(d.get("particle")) and isinstance(d.get("group"), str):
                groups_by_particle[d["particle"]].add(d["group"])
        assets = []
        material_cache = {}
        for particle, index in sorted(particles.items()):
            loc = f"particles/{particle}"
            self.raw(particle, loc)
            export = exports.get(particle, {})
            material = index.get("material")
            models = list(filter(None, index.get("models", "").split(";")))
            csv_groups = set(filter(None, index.get("direct_super_groups", "").split(";")))
            if csv_groups != groups_by_particle[particle]:
                self.issue("error", "csv_direct_group_mismatch", loc, str(sorted(csv_groups)))
            if material != export.get("material") or models != export.get("models", []):
                self.issue("error", "csv_export_mismatch", loc, str(index))
            if export.get("error") or export.get("materialError"):
                self.issue("error", "provider_export_error", loc, str(export))
            material_path = f"effects/Materials/{material}.json"
            if not is_tag(material):
                self.issue("error", "invalid_material_tag", loc, str(material))
            elif material not in material_cache:
                self.raw(material, loc)
                f = self.file(material_path, loc)
                textures = []
                if f["exists"] and f["bytes"]:
                    data = self.load(material_path, dict)
                    if data.get("Hash") != material:
                        self.issue("error", "material_identity_mismatch", material_path, str(data.get("Hash")))
                    for stage, shader in data.get("Material", {}).items():
                        for slot, texture in shader.get("Textures", {}).items():
                            tag = texture.get("Hash")
                            if not is_tag(tag):
                                self.issue("error", "invalid_texture_tag", material_path, str(texture))
                                continue
                            png = self.file(f"effects/Textures/{tag}.png", material_path)
                            textures.append(dict(stage=stage, slot=slot, tag=tag, file=png))
                material_cache[material] = dict(file=f, textures=textures)
            model_files = []
            for model in models:
                self.raw(model, loc)
                model_files.append(f"raw/{model}.bin")
            fbx = index.get("fbx")
            if models and not fbx:
                self.issue("error", "model_without_fbx", loc, str(models))
            fbx_file = self.file(f"effects/{fbx}", loc) if fbx else None
            assets.append(dict(particle=particle, classification="reported_direct" if particle in reported else
                               "graph_candidate_only", reported_groups=sorted(csv_groups),
                               definition=f"raw/{particle}.bin", material=material,
                               material_assets=material_cache.get(material), models=model_files, fbx=fbx_file))

        groups = {}
        group_names = set(PRIORITY) | {g for c in clips.values() if c.get("relatedSuperCandidate") for g in c["groups"]}
        group_names |= {s["group"] for s in seeds} | {d["group"] for d in direct if "group" in d}
        for group in sorted(group_names):
            selected = [c for c in clips.values() if group in c.get("groups", [])]
            events = []
            unknown = []
            for c in selected:
                if c.get("events", []) != frames.get(c["id"], {}).get("events", []):
                    self.issue("error", "manifest_frame_events_mismatch", c["id"], group)
                for i, e in enumerate(c.get("events", [])):
                    record = dict(clip=c["id"], event_index=i, event=e)
                    if e.get("type") == "S80808C13":
                        events.append(record)
                    else:
                        unknown.append(record)
            glinks = [r for r in links if r["claim"].get("group") == group]
            groups[group] = dict(
                clips=[dict(id=c["id"], source_names=c.get("sourceNames", []), files=c.get("files", {})) for c in selected],
                event_types=dict(Counter(e.get("type", "missing") for c in selected for e in c.get("events", []))),
                typed_events=events, unknown_schema_events=unknown,
                seed_count=sum(s.get("group") == group for s in seeds),
                sequence_path_events=sum(sequence_path(r["event"].get("path")) for r in events),
                audio_path_events=sum(str(r["event"].get("path", "")).lower().endswith(".wwise_event") for r in events),
                unresolved_tag_events=sum(not is_tag(r["event"].get("eventTag")) for r in events),
                reported_direct_particles=sorted({r["claim"]["particle"] for r in glinks if "particle" in r["claim"]}),
                substantiated_direct_particles=sorted({r["claim"]["particle"] for r in glinks
                                                       if r["status"] == "json_chain_substantiated"}),
                direct_rows=len(glinks),
                finding="no_direct_particle_link_in_supplied_evidence" if not glinks else
                        "reported_links_require_typed_component_evidence" if any(r["status"] != "json_chain_substantiated" for r in glinks)
                        else "json_chain_substantiated_timing_unresolved")
        if direct:
            self.issue("unresolved", "sequence_time_unit_unknown", "direct-super-particles.start/duration",
                       "No unit contract supplied. Do not combine with startFrame, assume seconds/30fps, or map to Minecraft ticks.")
        for group, data in groups.items():
            if data["unknown_schema_events"]:
                self.issue("unresolved", "undefined_event_schema", group,
                           "Unk* fields retained verbatim; no assumed timing, emitter, attachment, or effect role.")
        status_counts = dict(Counter(r["status"] for r in links))
        counts = dict(Counter(i["severity"] for i in self.issues))
        evidence_gaps = dict(
            missing_event_entities=sorted({r["claim"]["sequence"] for r in links
                                          if "event_entity_components_json_absent" in r["missing_evidence"]}),
            missing_typed_components=sorted({r["claim"]["component"] for r in links
                                            if "typed_component_nodes_json_absent" in r["missing_evidence"]}))
        untraversed_materials = sorted(p.relative_to(self.root).as_posix()
                                     for p in (self.root / "effects/Materials").glob("*.json")
                                     if p.stem not in material_cache)
        summary = dict(reported_direct_particles=len(reported), reported_direct_rows=len(direct),
                       reported_manifest_direct_particles=manifest.get("summary", {}).get("directSuperLinkedParticles"),
                       particle_definitions=len(particles), graph_candidate_only_particles=len(set(particles)-reported),
                       json_substantiated_direct_particles=len({r["claim"]["particle"] for r in links
                                                               if r["status"] == "json_chain_substantiated"}),
                       direct_status_counts=status_counts, typed_component_particle_references=len(typed_refs),
                       supported_seed_occurrences=sum(s["event_and_raw_supported"] for s in seed_results),
                       file_checks=len(self.files), nonempty_assets=sum(f["exists"] and f["bytes"] > 0 for f in self.files.values()),
                       materials=len(material_cache), texture_files=len({t["file"]["path"] for m in material_cache.values() for t in m["textures"]}),
                       fbx_files=sum(bool(a["fbx"]) for a in assets), issue_counts=counts)
        return dict(schema_version=1, source_root=str(self.root), game=manifest.get("game"),
                    status="errors" if counts.get("error") else "partial" if counts.get("unresolved") else "checked",
                    summary=summary, priority_groups={g: groups.pop(g) for g in PRIORITY}, other_groups=groups,
                    direct_links=links, seed_checks=seed_results, typed_component_references=typed_refs,
                    evidence_gaps=evidence_gaps, material_jsons_not_referenced_by_particle_index=untraversed_materials,
                    particle_assets=assets, issues=self.issues, input_fingerprints=self.inputs,
                    limits=["JSON references and asset presence/size only; binary schemas not independently decoded.",
                            "Reported direct claims are not independent component-node evidence.",
                            "Aligned_u32_candidate graph edges do not establish clip ownership or semantic links.",
                            "Sequence start/duration units, Unk* event semantics and synchronization unresolved.",
                            "Material/texture traversal follows particle-index and material JSON; embedded FBX dependencies are not parsed.",
                            "Existing/finite PNG or FBX is not running GPUVFX; no emitter, shader, lifetime or visual equivalence test.",
                            "No Blender, ComputerUse, Vision, Gradle, server or Minecraft runtime used."],
                    next_action="For Arc Staff 80A8A922/80A8A95C and Shadowshot 80A8AD97/80A8AD8A, obtain typed ability/weapon-event mapping for S80808C1A fields plus event-entity/component particle-node dumps and a time-unit contract. Re-run this audit before assigning converted effects. Keep Spectral/Silkstrike evidence separate.")


def markdown(report):
    s = report["summary"]
    lines = ["# W196 effect links", "", f"Source (read-only): `{report['source_root']}`", "",
             f"Result: **{report['status']}**. {s['reported_direct_rows']} reported rows / "
             f"{s['reported_direct_particles']} unique reported direct particles; "
             f"{s['json_substantiated_direct_particles']} independently substantiated through JSON component chains.",
             f"{s['particle_definitions']} particle definitions; {s['graph_candidate_only_particles']} graph-only candidates. "
             "The reported-direct set and graph-only set are disjoint; the graph inventory also includes the reported set.", "",
             "## Hunter conversion priority", "", "| Group | Clips | Event types | Sequence path events | Reported / substantiated particles |",
             "|---|---:|---|---:|---:|"]
    for group, data in report["priority_groups"].items():
        lines.append(f"| {group} | {len(data['clips'])} | {json.dumps(data['event_types'], sort_keys=True)} | "
                     f"{data['sequence_path_events']} | {len(data['reported_direct_particles'])} / {len(data['substantiated_direct_particles'])} |")
    for group, data in report["priority_groups"].items():
        lines += ["", f"### {group}", "", f"Finding: `{data['finding']}`. "
                  f"Audio path events: {data['audio_path_events']}; unresolved/null tag events: {data['unresolved_tag_events']}; "
                  f"seed rows: {data['seed_count']}. Absence applies to supplied evidence, not to the original game's effects.", ""]
        for clip in data["clips"]:
            lines.append(f"- `{clip['id']}`: {', '.join(clip['source_names'])}")
        lines += ["", "Typed events (Unk* events remain verbatim in the JSON report):", ""]
        if not data["typed_events"]:
            lines.append("None supplied.")
        for event in data["typed_events"]:
            e = event["event"]
            lines.append(f"- `{event['clip']}` frame `{e.get('startFrame')}` / `{e.get('eventTag')}` / "
                         f"marker `{e.get('marker')}` / `{e.get('path')}`")
    lines += ["", "## Other families — separate evidence", "",
              "| Group | Clips | Direct rows | Reported particles | Substantiated particles |", "|---|---:|---:|---:|---:|"]
    for group, data in report["other_groups"].items():
        lines.append(f"| {group} | {len(data['clips'])} | {data['direct_rows']} | "
                     f"{len(data['reported_direct_particles'])} | {len(data['substantiated_direct_particles'])} |")
    lines += ["", "Particle sets overlap between families; do not sum family counts.", "",
              "## Trace and assets", "",
              f"Direct status rows: `{json.dumps(s['direct_status_counts'], sort_keys=True)}`.",
              f"Matched seed occurrences in both manifest and frame-events, with clip/event raw assets present: {s['supported_seed_occurrences']}.",
              f"Actual typed component→particle JSON references: {s['typed_component_particle_references']} "
              "(component ownership alone does not identify a super).", ""]
    for ref in report["typed_component_references"]:
        lines.append(f"- `{ref['component']}` node {ref['node_index']} → `{ref['particle']}`")
    lines += ["", f"Checked {s['file_checks']} distinct referenced files: {s['nonempty_assets']} present and nonempty; "
              f"{s['materials']} material JSONs, {s['texture_files']} referenced PNGs, {s['fbx_files']} indexed FBXs. "
              "Missing FBX is not an error for particles with no exported model reference.", "",
              "The JSON report records every direct row, matched seed/manifest occurrence, missing link evidence, "
              "typed component reference, particle/material/texture/model/FBX asset path and input JSON/CSV SHA-256.", "",
              "Component-node JSON missing for: " + ", ".join(f"`{t}`" for t in report["evidence_gaps"]["missing_typed_components"]) + ".",
              "Event-entity component-list JSON missing for: " + ", ".join(f"`{t}`" for t in report["evidence_gaps"]["missing_event_entities"]) + ".",
              "Material JSON files outside particle-index traversal (not certified through embedded FBX references): " +
              ", ".join(f"`{p}`" for p in report["material_jsons_not_referenced_by_particle_index"]) + ".", "",
              "## Findings and limits", "", "| Severity | Finding | Occurrences |", "|---|---|---:|"]
    for (severity, code), count in sorted(Counter((i["severity"], i["code"]) for i in report["issues"]).items()):
        lines.append(f"| {severity} | {code} | {count} |")
    lines += [""] + [f"- {limit}" for limit in report["limits"]]
    lines += ["", "## Useful next action", "", report["next_action"], "", "## Reproduce", "", "```sh",
              "rtk proxy python3 -B scripts/qa/test_super_effects_w196.py",
              f"rtk proxy python3 -B scripts/animation/audit_super_effects.py --source-root '{report['source_root']}' "
              "--json docs/qa/2026-10-27/w196/effect-links.json --markdown docs/qa/2026-10-27/w196/effect-links.md",
              "```", "", "Add `--require-substantiated` to exit 2 when evidence or timing remains unresolved. "
              "Default exit 0 means the partial audit completed without contradictions; it does not certify conversion readiness.", "",
              "Supply new typed dumps outside the original delivery using `--components-json /path/component-nodes.json` "
              "and `--entities-json /path/event-entities.json`. Their list schemas match the delivered "
              "`player-sequences.json` and `entity-index.json`; supplemental inputs are fingerprinted. "
              "These can close reference gaps but do not resolve undocumented timing or Unk* semantics.", ""]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--json", type=Path, required=True, dest="json_path")
    parser.add_argument("--markdown", type=Path, required=True)
    parser.add_argument("--components-json", type=Path, action="append", default=[])
    parser.add_argument("--entities-json", type=Path, action="append", default=[])
    parser.add_argument("--require-substantiated", action="store_true")
    args = parser.parse_args(argv)
    try:
        audit = Audit(args.source_root)
        outputs = [args.json_path.resolve(), args.markdown.resolve()]
        if outputs[0] == outputs[1] or any(p.is_relative_to(audit.root) for p in outputs):
            raise ValueError("Outputs must be distinct and outside the read-only source root")
        report = audit.run(args.components_json, args.entities_json)
        if any(str(p) in audit.inputs for p in outputs):
            raise ValueError("Output would overwrite supplemental evidence")
        for p in outputs:
            p.parent.mkdir(parents=True, exist_ok=True)
        outputs[0].write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
        outputs[1].write_text(markdown(report), encoding="utf-8")
        print(json.dumps(dict(status=report["status"], summary=report["summary"]), sort_keys=True))
        if report["summary"]["issue_counts"].get("error"):
            return 1
        return 2 if args.require_substantiated and report["summary"]["issue_counts"].get("unresolved") else 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    sys.exit(main())
