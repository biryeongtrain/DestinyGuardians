#!/usr/bin/env python3
"""Read-only, stdlib intake audit for the player/super and weapon return schemas.

Use --source once per bundle (repeat to combine). No exporter, decoder, subprocess,
Blender, or game is invoked. Exit 0 means intake consistency, never gameplay QA.
Reports may only be written to this worktree's two W196 owned report paths;
without --write-reports the complete JSON audit goes to stdout.
"""

import argparse
from collections import Counter, defaultdict
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import re
import stat
import sys


TAG = re.compile(r"[0-9A-F]{8}\Z")
GROUP = re.compile(r"[a-z0-9_]+\Z")
PATTERNS = {
    "reload": re.compile(r"reload", re.I),
    "weapon": re.compile(r"weapon|hand.?cannon|pistol|rifle|shotgun|sniper|launcher|machine.?gun|bow|sword|sidearm|magazine", re.I),
    "first_person_token": re.compile(r"(^|[^a-z0-9])(1p|fp|first[_ -]?person)([^a-z0-9]|$)", re.I),
}
REPORT_DIR = Path(__file__).resolve().parents[2] / "docs/qa/2026-10-27/w196"


class Invalid(ValueError):
    """Invalid intake structure or unsafe reference."""


def require(condition, message):
    if not condition:
        raise Invalid(message)


def typed(value, kind, context):
    require(type(value) is kind, f"{context}: expected {kind.__name__}")
    return value


def finite_float(value):
    result = float(value)
    require(math.isfinite(result), "non-finite JSON number")
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def strings(value, context):
    typed(value, list, context)
    require(all(type(x) is str and x for x in value), f"{context}: expected nonempty strings")
    require(len(value) == len(set(value)), f"{context}: duplicate entries")
    return value


def indexed(rows, key, context):
    typed(rows, list, context)
    result = {}
    for row in rows:
        typed(row, dict, context)
        value = row.get(key)
        require(type(value) is str and value, f"{context}: missing {key}")
        require(value not in result, f"{context}: duplicate {key} {value}")
        result[value] = row
    return result


def numeric(value, context, minimum=0):
    require(type(value) in (int, float) and math.isfinite(value) and value >= minimum,
            f"{context}: invalid finite number")
    return value


class Audit:
    def __init__(self, source):
        self.root = Path(source).absolute()
        self.errors = []
        self.files = set()
        self.hashes = {}
        self.groups = {}
        self.actions = defaultdict(dict)
        self.source_maps = {}
        self.frame_records = {}
        self.result = {
            "source": str(self.root), "errors": self.errors,
            "verification_basis": {
                "independently_checked": ["file inventory, bytes and SHA-256", "JSON/CSV references and reconciliation"],
                "independent_animation_decode": False,
                "source_reported_only": ["Blender action measurements", "rig/POV and inventory selector interpretation", "compatibleControls diagnosis"],
                "not_run": ["Blender import/render", "Minecraft", "native/live QA", "Gradle/full gate"],
            },
        }

    def safe(self, relative, exists=True):
        require(type(relative) is str and relative, "empty/non-string path")
        parts = relative.split("/")
        require(not any(x in ("", ".", "..") for x in parts)
                and "\\" not in relative and ":" not in relative and "\0" not in relative,
                f"unsafe relative path: {relative!r}")
        path = self.root
        require(not path.is_symlink() and path.resolve() == path, "source root has symlink components")
        for part in parts:
            path = path / part
            require(not path.is_symlink(), f"symlink reference rejected: {relative}")
        require(path.resolve().is_relative_to(self.root), f"outside source: {relative}")
        if exists:
            require(path.is_file(), f"missing file: {relative}")
        return path

    def load(self, name, kind):
        value = json.loads(self.safe(name).read_text(encoding="utf-8-sig"),
                           object_pairs_hook=unique_object, parse_float=finite_float,
                           parse_constant=lambda x: (_ for _ in ()).throw(Invalid(f"non-finite JSON: {x}")))
        return typed(value, kind, name)

    def csv(self, name):
        return list(csv.DictReader(io.StringIO(self.safe(name).read_text(encoding="utf-8-sig"))))

    def check(self, label, operation):
        try:
            return operation()
        except (Invalid, OSError, ValueError, KeyError, TypeError, AttributeError, IndexError, OverflowError, RecursionError) as exc:
            self.errors.append({"check": label, "message": str(exc)})
            return None

    def inventory(self):
        require(self.root.is_dir() and self.root.resolve() == self.root, "source is not a real directory (symlink roots rejected)")
        pending = [self.root]
        folded = set()
        while pending:
            for path in sorted(pending.pop().iterdir()):
                name = path.relative_to(self.root).as_posix()
                mode = path.lstat().st_mode
                if stat.S_ISLNK(mode):
                    self.errors.append({"check": "inventory", "message": f"symlink rejected: {name}"})
                elif stat.S_ISDIR(mode):
                    pending.append(path)
                elif stat.S_ISREG(mode):
                    require(name.casefold() not in folded, f"case-colliding file: {name}")
                    folded.add(name.casefold())
                    self.files.add(name)
                else:
                    self.errors.append({"check": "inventory", "message": f"non-regular file: {name}"})

    def hash_inventory(self):
        rows = self.load("FILE_HASHES.json", list)
        seen, verified, total = set(), 0, 0
        for index, row in enumerate(rows):
            def verify():
                nonlocal verified, total
                typed(row, dict, "hash row")
                name = row.get("path")
                self.safe(name, exists=False)
                require(name != "FILE_HASHES.json", "FILE_HASHES cannot self-authenticate")
                require(name not in seen, f"duplicate hash path: {name}")
                seen.add(name)
                path = self.safe(name)
                size, expected = row.get("bytes"), row.get("sha256")
                require(type(size) is int and size >= 0, f"invalid byte count: {name}")
                require(type(expected) is str and re.fullmatch(r"[a-fA-F0-9]{64}", expected), f"invalid SHA-256: {name}")
                actual = digest(path)
                self.hashes[name] = {"bytes": path.stat().st_size, "sha256": actual}
                require(self.hashes[name]["bytes"] == size, f"byte count mismatch: {name}")
                require(actual == expected.lower(), f"SHA-256 mismatch: {name}")
                total += size
                verified += 1
            self.check(f"FILE_HASHES[{index}]", verify)
        unlisted = sorted(self.files - seen - {"FILE_HASHES.json"})
        missing = sorted(seen - self.files)
        if unlisted or missing:
            self.errors.append({"check": "hash completeness", "message": "unlisted or missing files", "unlisted": unlisted, "missing": missing})
        self.result["hash_validation"] = {
            "entries": len(rows), "verified_files": verified, "verified_bytes": total,
            "actual_files": len(self.files), "unlisted": unlisted, "missing": missing,
            "file_hashes_sha256": digest(self.safe("FILE_HASHES.json")),
            "self_hash_excluded": True,
            "authentication_limit": "Local consistency only; no externally trusted signed checksum baseline.",
        }

    def raw_reference(self, tag, reference):
        require(type(tag) is str and TAG.fullmatch(tag), f"invalid raw tag: {tag!r}")
        self.safe(reference)
        require(reference == f"raw/{tag}.bin", f"tag/file mismatch: {tag} -> {reference}")

    def manifest_clips(self):
        self.clips = indexed(self.manifest.get("clips"), "id", "manifest clips")
        require(self.clips, "manifest clips: empty library")
        weapon = self.kind == "weapon"
        for cid, clip in self.clips.items():
            def validate():
                tags = typed(clip.get("tags"), dict, "tags") if weapon else {
                    "clip": cid, "skeleton": clip.get("skeleton"), "runtimeRig": clip.get("runtimeRig")}
                files = typed(clip.get("files"), dict, "files")
                for key in ("clip", "skeleton", "runtimeRig"):
                    self.raw_reference(tags.get(key), files.get(key))
                if weapon:
                    require(cid == "_".join(tags[k] for k in ("clip", "skeleton", "runtimeRig")), "clip+rig id mismatch")
                for value in files.values():
                    if value is not None:
                        self.safe(value)
                strings(clip.get("sourceNames"), "sourceNames")
                gids = strings(clip.get("groupIds" if weapon else "groups"), "clip groups")
                require(gids and all(GROUP.fullmatch(g) for g in gids), "invalid/empty clip groups")
                require(clip.get("status") in ("decoded_unverified", "raw_extracted"), "unknown clip status")
                require(clip.get("perspective") == ("1P" if weapon else "3P_player_rig"), "unexpected perspective")
                require(type(clip.get("perspectiveEvidence")) is str and clip["perspectiveEvidence"], "missing perspective evidence")
                if weapon:
                    strings(clip.get("weaponIds"), "weaponIds")
                    entries = indexed(clip.get("actualPackageEntries"), "tag", "actualPackageEntries")
                    require(set(entries) == set(tags.values()), "package entry tags mismatch")
                    for tag, entry in entries.items():
                        actual = self.hashes.get(f"raw/{tag}.bin", {})
                        require(entry.get("bytes") == actual.get("bytes") and
                                str(entry.get("sha256")).lower() == actual.get("sha256"), f"package digest mismatch: {tag}")
                elif clip["status"] == "raw_extracted":
                    require(not any(files.get(k) for k in ("fbx", "blend")) and not clip.get("measured"), "raw-only clip claims decoded data")
                if clip["status"] == "decoded_unverified":
                    typed(clip.get("measured"), dict, "measured")
                    verification = typed(clip.get("verification"), dict, "verification")
                    require(verification.get("blenderImported") is True and verification.get("gameplayVerified") is False,
                            "decoded_unverified verification contradicts status")
                    for key in (("firstPersonFbx", "weaponFbx", "blend") if weapon else ("fbx", "blend")):
                        self.safe(files.get(key))
            self.check(f"manifest clip {cid}", validate)
        self.result["manifest"] = {
            "sha256": digest(self.safe("manifest.json")), "status": self.manifest.get("status"),
            "game": self.manifest.get("game"), "source_summary": self.manifest.get("summary"),
            "records": len(self.clips), "statuses": dict(Counter(c.get("status") for c in self.clips.values())),
            "perspectives": dict(Counter(c.get("perspective") for c in self.clips.values())),
        }

    def inspection(self, name, expected, frame_records):
        data = self.load(name, dict)
        actions = indexed(data.get("actions"), "tag", name)
        for tag, action in actions.items():
            require(TAG.fullmatch(tag), f"invalid action tag: {tag}")
            require(type(action.get("name")) is str and tag in action["name"], f"action name/tag mismatch: {tag}")
            require(action.get("finite") is True, f"nonfinite action reported: {tag}")
            frames = typed(action.get("frames"), list, "action frames")
            require(len(frames) == 2, "action frames must have two endpoints")
            lo, hi = [numeric(x, "frame") for x in frames]
            require(hi >= lo, "reversed action range")
            fps = numeric(action.get("fps"), "fps", minimum=1)
            require(math.isclose(numeric(action.get("duration"), "duration"), (hi-lo)/fps, abs_tol=1e-8), f"duration mismatch: {tag}")
            for key in ("curves", "keys", "changingCurves", "maxBoneHeadDisplacement"):
                numeric(action.get(key), key)
            require(action["changingCurves"] <= action["curves"], "changing curves exceeds curves")
        observed = {
            "bones": data.get("bones"), "expected": len(expected), "actual": len(actions),
            "missing": sorted(expected-set(actions)), "unexpected": sorted(set(actions)-expected),
            "finite": all(a["finite"] for a in actions.values()),
            "moving": sum(a["maxBoneHeadDisplacement"] > 1e-6 for a in actions.values()),
        }
        numeric(data.get("bones"), "inspection bones", minimum=1)
        return data, actions, observed

    def bone_map(self, name, expected):
        bones = self.load(name, list)
        require(len(bones) == expected, f"bone-map length differs from inspection: {name}")
        names = set()
        for index, bone in enumerate(bones):
            require(bone.get("Index") == index, "bone Index/order mismatch")
            parent = bone.get("ParentNodeIndex")
            require(type(parent) is int and -1 <= parent < index, "invalid parent/cycle in bone map")
            require(type(bone.get("name")) is str and bone["name"] not in names, "duplicate/invalid bone name")
            names.add(bone["name"])
        return bones

    def group(self, gid, definition):
        require(GROUP.fullmatch(gid), f"unsafe group id: {gid}")
        weapon = self.kind == "weapon"
        folder = f"clips/{gid}" if weapon else f"animations/{gid}"
        records = indexed(self.load(f"{folder}/clips.json", list), "tag", f"{gid} clips")
        self.frame_records[gid] = records
        expected = set(records)
        memberships = {c["tags"]["clip"] if weapon else cid for cid, c in self.clips.items()
                       if gid in c.get("groupIds" if weapon else "groups", [])}
        require(expected == memberships, f"{gid}: dangling manifest/group clip membership")
        for tag, row in records.items():
            self.raw_reference(tag, f"raw/{tag}.bin")
            for key in ("FrameCount", "NodeCount", "RigControlCount"):
                require(type(row.get(key)) is int and row[key] > 0, f"invalid {key}: {tag}")
        name = f"{folder}/inspection_FirstPerson.json" if weapon else f"{folder}/inspection.json"
        data, actions, observed = self.inspection(name, expected, records)
        if weapon:
            summary = typed(definition.get("blenderAudit"), dict, "blenderAudit")
            require(definition.get("expectedClips") == len(expected), "expectedClips mismatch")
            require(data.get("file") == Path(definition["firstPersonFbx"]).name, "FP inspection filename mismatch")
            _, weapon_actions, weapon_observed = self.inspection(f"{folder}/inspection.json", expected, records)
            require(set(weapon_actions) == set(actions), "weapon vs FP action tag mismatch")
            require(not weapon_observed["missing"] and not weapon_observed["unexpected"], "weapon rig missing/unexpected action")
            self.raw_reference(definition.get("weaponSkeleton"), f"raw/{definition.get('weaponSkeleton')}.bin")
            for key in ("firstPersonFbx", "weaponFbx", "blend"):
                self.safe(definition.get(key))
            source = self.load(f"{folder}/source-map.json", dict)
            self.source_maps[gid] = source
            for key in ("skeleton", "runtimeRig", "weaponSkeleton", "weapons"):
                require(source.get(key) == definition.get(key), f"source-map {key} mismatch")
            require(source.get("groupId") == gid, "source-map groupId mismatch")
            mapped = indexed(source.get("clips"), "tag", "source-map clips")
            require(set(mapped) == expected, "source-map clip set mismatch")
            for tag, row in mapped.items():
                strings(row.get("names"), "group-local names")
            bones = self.bone_map(f"{folder}/bone-map.json", data["bones"])
            require(sum(b.get("weaponBone") is True for b in bones) == weapon_observed["bones"], "weapon bone count mismatch")
        else:
            summary = data
            self.safe(f"{folder}/{gid}.fbx")
            self.safe(f"{folder}/source.blend")
            self.bone_map("provenance/bone-map.json", data["bones"])
        require(summary.get("groupId") == gid, "inspection groupId mismatch")
        for key, value in observed.items():
            reported_key = "movingActions" if weapon and key == "moving" else key
            require(summary.get(reported_key) == value, f"{gid}: inspection {reported_key} does not reconcile")
        require(not observed["unexpected"], f"{gid}: unexpected actions")
        for cid, clip in self.clips.items():
            if gid not in clip.get("groupIds" if weapon else "groups", []):
                continue
            tag = clip["tags"]["clip"] if weapon else cid
            require((tag in actions) == (clip["status"] == "decoded_unverified"), f"status/action mismatch: {cid}")
            if weapon:
                require(clip["tags"]["skeleton"] == definition["skeleton"] and clip["tags"]["runtimeRig"] == definition["runtimeRig"], "group rig mismatch")
                require(set(mapped[tag]["names"]) <= set(clip["sourceNames"]), "local names missing from manifest union")
            if tag in actions:
                self.actions[cid][gid] = actions[tag]
        self.groups[gid] = {
            "source_inspection": name, "reconciled_source_measurements": observed,
            "independent_animation_decode": False,
            "source_frame_count_vs_action_range_differences": [
                {"tag": t, "source_frame_count": records[t]["FrameCount"], "source_action_range": a["frames"],
                 "source_changing_curves": a["changingCurves"]}
                for t,a in actions.items() if t in records and a["frames"][1]-a["frames"][0]+1 != records[t]["FrameCount"]],
            "static_curve_tags": sorted(t for t,a in actions.items() if a["changingCurves"] == 0),
            "stationary_bone_head_tags": sorted(t for t,a in actions.items() if a["maxBoneHeadDisplacement"] <= 1e-6),
        }

    def reconcile(self):
        weapon = self.kind == "weapon"
        definitions = indexed(self.manifest.get("groups"), "id", "groups") if weapon else {
            name.split("/")[1]: {} for name in sorted(self.files) if name.startswith("animations/") and name.endswith("/clips.json")}
        require(definitions, "no animation groups")
        for gid, definition in definitions.items():
            self.check(f"group {gid}", lambda gid=gid, definition=definition: self.group(gid, definition))
        for cid, clip in self.clips.items():
            def validate():
                gids = clip.get("groupIds" if weapon else "groups", [])
                require(set(gids) <= set(definitions), f"dangling groups: {gids}")
                if clip.get("status") != "decoded_unverified":
                    return
                files = clip["files"]
                chosen = files["firstPersonFbx"].split("/")[1] if weapon else clip.get("preferredGroup")
                require(chosen in gids and chosen in self.actions[cid], "missing preferred action/group")
                action = self.actions[cid][chosen]
                measured = clip["measured"]
                if weapon:
                    comparisons = {"frameCount": self.frame_records[chosen][clip["tags"]["clip"]]["FrameCount"],
                                   "fps": action["fps"], "durationSeconds": action["duration"],
                                   "blenderFcurves": action["curves"], "blenderKeyCount": action["keys"],
                                   "changingCurves": action["changingCurves"], "maxBoneHeadDisplacement": action["maxBoneHeadDisplacement"],
                                   "joints": self.groups[chosen]["reconciled_source_measurements"]["bones"]}
                    require(all(measured.get(k) == v for k,v in comparisons.items()), "manifest measured vs preferred FP inspection mismatch")
                    for key in ("firstPersonFbx", "weaponFbx", "blend"):
                        require(files[key] == definitions[chosen][key], f"preferred {key} mismatch")
                else:
                    require(measured == action, "manifest measured vs inspection mismatch")
                    require(files["fbx"] == f"animations/{chosen}/{chosen}.fbx" and files["blend"] == f"animations/{chosen}/source.blend", "preferred files mismatch")
            self.check(f"reconcile clip {cid}", validate)
        summary_name = "provenance/audit-summary.json" if weapon else "provenance/final-audit-summary.json"
        summaries = indexed(self.load(summary_name, list), "groupId", summary_name)
        require(set(summaries) == set(definitions), "final audit group set mismatch")
        for gid in self.groups:
            summary = definitions[gid]["blenderAudit"] if weapon else self.load(f"animations/{gid}/inspection.json", dict)
            require(all(summary.get(k) == v for k,v in summaries[gid].items()), f"final audit summary mismatch: {gid}")
        self.result["groups"] = self.groups

    def evidence(self):
        evidence = {}
        for category, pattern in PATTERNS.items():
            hits = []
            for cid, clip in self.clips.items():
                names = [n for n in clip.get("sourceNames", []) if pattern.search(n)]
                paths = sorted({e["path"] for e in clip.get("events", []) if type(e) is dict and type(e.get("path")) is str and pattern.search(e["path"])})
                if names or paths:
                    hits.append({"id": cid, "matched_source_names": names, "matched_event_paths": paths,
                                 "perspective": clip.get("perspective"), "status": clip.get("status")})
            evidence[category] = {"match_rule": pattern.pattern, "clips": len(hits), "matches": hits}
        evidence["interpretation"] = "Name/event token matches are search evidence, not proof of POV, exclusivity, mesh contact, or gameplay timing. Weapon manifest names are unions across groups; use group-local selections below."
        if self.kind == "weapon":
            identities = {}
            inventory = self.load("provenance/inventory-index.json", list)
            weapon_map = self.load("provenance/weapon-map.json", dict)
            mapping = {(r["id"],r["apiHash"],r["groupId"]) for r in weapon_map["mapping"]}
            for gid, source in self.source_maps.items():
                for weapon in source["weapons"]:
                    require((weapon["id"],weapon["apiHash"],gid) in mapping, "weapon-map association missing")
                    candidates = [r for r in inventory if r.get("id") == weapon["id"] and r.get("apiHash") == weapon["apiHash"]]
                    require(len(candidates) == 1, "inventory identity missing/duplicate")
                    entry = candidates[0]
                    require(entry.get("selector") == weapon["selector"], "inventory selector mismatch")
                    for key in ("skeleton", "runtimeRig", "weaponSkeleton"):
                        require(entry.get(key) == source[key], "inventory rig mismatch")
                    clips = indexed(entry.get("clips"), "tag", "inventory clips")
                    selected = []
                    for row in source["clips"]:
                        require(row["tag"] in clips and set(row["names"]) <= set(clips[row["tag"]]["names"]), "group-local names not supported by inventory")
                        names = [n for n in row["names"] if "reload" in n.lower()]
                        if names:
                            action = self.actions.get(f"{row['tag']}_{source['skeleton']}_{source['runtimeRig']}", {}).get(gid, {})
                            selected.append({"tag": row["tag"], "group_local_names": row["names"],
                                             "source_action_name": action.get("name"), "source_frames": action.get("frames"),
                                             "source_fps": action.get("fps"), "source_duration_seconds": action.get("duration")})
                    identities.setdefault(weapon["id"], []).append({
                        "group": gid, "apiHash": weapon["apiHash"], "itemTag": weapon["itemTag"],
                        "selector": weapon["selector"], "source_map_selector": source.get("selector"),
                        "fallback": entry.get("fallback"), "first_person_fbx": self.manifest_group(gid)["firstPersonFbx"],
                        "reload_selections": selected,
                        "confidence": "Source inventory/selector association reconciled with group source-map and weapon-map; no independent gameplay identity/exclusivity verification.",
                    })
            evidence["per_weapon"] = identities
            evidence["identity_caveats"] = [
                "Ace 80A8A567 and Duke 80A8A53D are distinct source-map reload selections; a generic HC clip is not an Ace substitute.",
                "Izanagi's 80A8A140, 80A8A150, 80A8A14D retain their local names; reload_special on 80A8A14D does not prove a unique Honed Edge gameplay sequence.",
                "Skeleton FBXs have no weapon/hand mesh; source 1P association remains decoded_unverified.",
            ]
        self.result["evidence"] = evidence

    def manifest_group(self, gid):
        return next(g for g in self.manifest["groups"] if g["id"] == gid)

    def counts(self):
        weapon = self.kind == "weapon"
        observed = {"rawFiles": sum(n.startswith("raw/") for n in self.files)}
        instances = sum(g["reconciled_source_measurements"]["actual"] for g in self.groups.values())
        if weapon:
            coverage = indexed(self.csv("weapon-coverage.csv"), "id", "weapon coverage")
            observed.update({"targetWeapons": len(coverage),
                             "withAnimationRigs": sum(r["status"] == "rig_animation_extracted" for r in coverage.values()),
                             "reloadNotApplicableSwords": sum("sword" in r["family"] and r["status"] != "rig_animation_extracted" for r in coverage.values()),
                             "groups": len(self.groups), "uniqueRigClipPairs": len(self.clips),
                             "uniqueSourceAnimationClips": len({c["tags"]["clip"] for c in self.clips.values()}),
                             "groupActionInstances": instances,
                             "fbxFiles": sum(n.startswith("clips/") and n.endswith(".fbx") for n in self.files),
                             "blenderGroupFiles": sum(n.startswith("clips/") and n.endswith(".blend") for n in self.files),
                             "previewVideos": sum(n.startswith("clips/") and n.endswith(".mp4") for n in self.files)})
            for wid, row in coverage.items():
                gids = set(filter(None,row["groups"].split(";")))
                actual = {gid for gid, s in self.source_maps.items() if any(w["id"] == wid for w in s["weapons"])}
                require(gids == actual, f"weapon coverage groups mismatch: {wid}")
        else:
            raw_only = [cid for cid,c in self.clips.items() if c["status"] == "raw_extracted"]
            diagnostics = indexed(self.load("provenance/missing-diagnostics.json", list), "tag", "missing diagnostics")
            for cid in raw_only:
                require(cid in diagnostics and diagnostics[cid].get("compatibleControls") == 0, f"raw-only diagnosis missing: {cid}")
                require(cid not in self.actions, f"raw-only has action: {cid}")
            self.result["raw_only"] = {"tags": raw_only, "count": len(raw_only), "diagnosis_basis": "source-reported compatibleControls=0, not independently decoded"}
            particles = indexed(self.csv("effects/particle-index.csv"), "particle", "particles")
            links = self.load("provenance/direct-super-particles.json", list)
            for link in links:
                require(link["clip"] in self.clips and link["particle"] in particles and
                        link["group"] in self.clips[link["clip"]]["groups"], "dangling direct particle link")
            observed.update({"sourceClips": len(self.clips), "decodedUniqueClips": len(self.actions), "rawOnlyClips": len(raw_only),
                             "superRelatedSourceClips": sum(c["relatedSuperCandidate"] is True for c in self.clips.values()),
                             "animationFbxFiles": sum(n.startswith("animations/") and n.endswith(".fbx") for n in self.files),
                             "blenderFiles": sum(n.startswith("animations/") and n.endswith(".blend") for n in self.files),
                             "previewVideos": sum(n.startswith("animations/") and n.endswith(".mp4") for n in self.files),
                             "particleDefinitions": len(particles), "directSuperLinkedParticles": len({x["particle"] for x in links}),
                             "effectMeshFbxFiles": sum(n.startswith("effects/") and n.endswith(".fbx") for n in self.files),
                             "effectTexturePngFiles": sum(n.startswith("effects/Textures/") and n.endswith(".png") for n in self.files),
                             "materialJsonFiles": sum(n.startswith("effects/Materials/") and n.endswith(".json") for n in self.files)})
            coverage = self.load("super-coverage.json", list)
            require(coverage == self.manifest.get("coverage"), "super coverage/manifest mismatch")
            for row in coverage:
                require(set(row["groups"]) <= set(self.groups), "dangling super coverage group")
            self.result["source_coverage"] = coverage
        self.result["observed_counts"] = observed
        self.result["source_action_instances"] = instances
        for key, value in self.manifest["summary"].items():
            require(key in observed and observed[key] == value, f"summary {key}: source={value}, observed={observed.get(key)}")

    def clip_csv(self):
        rows = self.csv("clip-index.csv")
        ids = set()
        for row in rows:
            cid = "_".join(row[k] for k in ("tag", "skeleton", "rig")) if self.kind == "weapon" else row["tag"]
            require(cid not in ids and cid in self.clips, f"duplicate/dangling CSV clip: {cid}")
            ids.add(cid)
            clip = self.clips[cid]
            require(set(filter(None,row["groups"].split(";"))) == set(clip["groupIds" if self.kind == "weapon" else "groups"]), "CSV groups mismatch")
            require(set(filter(None,row["names"].split(";"))) == set(clip["sourceNames"]), "CSV names mismatch")
            if self.kind == "super":
                require(row["status"] == clip["status"] and row["preferred_fbx"] == clip["files"].get("fbx", ""), "CSV status/file mismatch")
        require(ids == set(self.clips), "CSV clip completeness mismatch")

    def run(self):
        self.check("inventory", self.inventory)
        self.check("hash validation", self.hash_inventory)
        self.manifest = self.check("manifest JSON", lambda: self.load("manifest.json", dict))
        if self.manifest is not None:
            self.kind = "weapon" if "groups" in self.manifest and "scope" in self.manifest else "super"
            self.result["schema"] = self.kind
            self.result["source_limitations"] = self.manifest.get("unresolved" if self.kind == "weapon" else "limitations", [])
            self.check("manifest header", lambda: require(self.manifest.get("schemaVersion") == 1 and self.manifest.get("template") is False and self.manifest.get("status") == "partial", "unsupported schema/template/status"))
            if self.check("manifest clips", self.manifest_clips) is None and hasattr(self, "clips"):
                self.check("group reconciliation", self.reconcile)
                self.check("counts", self.counts)
                self.check("clip CSV", self.clip_csv)
                self.check("name/identity evidence", self.evidence)
        self.result["status"] = "invalid" if self.errors else "consistent_partial_intake"
        return self.result


def audit_source(source):
    return Audit(source).run()


def markdown(report):
    lines = ["# W196 source intake", "", "Read-only stdlib verification. A consistent intake remains partial and decoded_unverified.",
             "No independent animation decode, Blender import/render, Minecraft, native/live QA, or Gradle/full gate was run.", "",
             "Hash checks prove local consistency with the supplied index, not signed provenance. `FILE_HASHES.json` excludes itself; its observed digest is recorded.", ""]
    for kind, result in report.items():
        lines += [f"## {kind}", "", f"Source: `{result['source']}`", "", f"Result: **{result['status']}**; errors: {len(result['errors'])}.", ""]
        hashes = result.get("hash_validation", {})
        lines += [f"SHA-256: {hashes.get('verified_files')} / {hashes.get('entries')} listed files, {hashes.get('verified_bytes')} bytes; {hashes.get('actual_files')} actual files including the hash index.", "", "| Observed artifact / metadata count | Count |", "|---|---:|"]
        lines += [f"| {key} | {value} |" for key,value in result.get("observed_counts", {}).items()]
        lines += ["", "Counts of actions, motion, bones and finite values reconcile supplied inspections; they are source-reported measurements, not independently decoded animations.", ""]
        differences = [(gid, row) for gid, group in result.get("groups", {}).items()
                       for row in group["source_frame_count_vs_action_range_differences"]]
        lines += [f"Source frame count differs from keyed action range in {len(differences)} group action instances. These fields are preserved separately. Weapon manifest measured.frameCount is checked against clips.json FrameCount; duration, curves, keys, joints and motion are checked against the preferred first-person inspection.", ""]
        if differences:
            lines += ["Examples:", ""] + [f"- `{gid}/{row['tag']}`: source FrameCount={row['source_frame_count']}, inspection range={row['source_action_range']}, changingCurves={row['source_changing_curves']}." for gid,row in differences[:2]] + [""]
        if kind == "super":
            raw = result.get("raw_only", {})
            lines += [f"Raw-only {raw.get('count')}: " + ", ".join(f"`{x}`" for x in raw.get("tags", [])), "",
                      "All manifest perspectives are 3P_player_rig. Generic weapon names and fp_melee audio paths do not establish first-person weapon reloads.", ""]
        evidence = result.get("evidence", {})
        for category in PATTERNS:
            data = evidence.get(category, {})
            names = sorted({n for row in data.get("matches", []) for n in row["matched_source_names"]})
            paths = sorted({p for row in data.get("matches", []) for p in row["matched_event_paths"]})
            lines += [f"### {category} name/event evidence ({data.get('clips', 0)} clips)", "", "Names: " + (", ".join(f"`{n}`" for n in names) or "none"), ""]
            if paths:
                lines += ["Event paths (full per-tag matches are in JSON):", ""] + [f"- `{p}`" for p in paths] + [""]
        if kind == "weapon":
            lines += ["### Weapon identity and reload selections", "", "Selections below use each group's source-map and reconciled inventory/selector, never the global manifest name union. All per-weapon mappings are retained in JSON.", ""]
            for wid in ("duke_mk_44", "ace_of_spades", "izanagis_burden"):
                for identity in evidence.get("per_weapon", {}).get(wid, []):
                    lines += [f"**{wid}**: group `{identity['group']}`, API `{identity['apiHash']}`, item `{identity['itemTag']}`, selector `{identity['selector']}`, fallback `{identity['fallback']}`.", "",
                              f"First-person FBX: `{identity['first_person_fbx']}`", "", "| Tag | Group-local names | Source duration (s) |", "|---|---|---:|"]
                    lines += [f"| `{row['tag']}` | {', '.join(row['group_local_names'])} | {row['source_duration_seconds']} |" for row in identity["reload_selections"]]
                    lines += [""]
            lines += evidence.get("identity_caveats", []) + [""]
        lines += ["### Integration caveats", ""] + [f"- {x}" for x in result.get("source_limitations", [])] + [""]
        if result["errors"]:
            lines += ["### Errors", ""] + [f"- {e['check']}: {e['message']}" for e in result["errors"]] + [""]
    lines += ["## Reproduce", "", "```sh", "rtk proxy python3 -B scripts/animation/audit_destiny_return.py \\",
              "  --source /Volumes/qf-ssd/DestinyGuardians-Super-Animation-VFX-2026-10-27/destiny-animation-return \\",
              "  --source /Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return \\",
              "  --write-reports", "rtk proxy python3 -B -m unittest discover -s scripts/qa -p test_animation_return_w196.py -v", "```", "",
              "Master owns subsequent independent Blender and Minecraft validation. Coordinate/bind-pose mapping, mesh contact, ammo/event timing, GPU VFX reconstruction, and gameplay equivalence remain unverified.", ""]
    return "\n".join(lines)


def write_reports(report, sources):
    # Restrict every mutation to the two owned reports, including symlink parents.
    paths = [REPORT_DIR / "source-intake.json", REPORT_DIR / "source-intake.md"]
    for path in paths:
        require(not any(p.is_symlink() for p in [path, *path.parents]), "report symlink rejected")
        require(all(not path.resolve().is_relative_to(Path(source).resolve()) for source in sources), "report would write inside source")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    paths[0].write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    paths[1].write_text(markdown(report), encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", action="append", required=True, help="Read-only bundle root; repeat once per schema")
    parser.add_argument("--write-reports", action="store_true", help="Write only the two owned W196 report paths")
    args = parser.parse_args(argv)
    report = {}
    for source in args.source:
        result = audit_source(source)
        key = result.get("schema", "unknown")
        if key in report:
            parser.error(f"duplicate schema {key}; audit same-schema sources separately")
        report[key] = result
    if args.write_reports:
        try:
            write_reports(report, args.source)
        except (Invalid, OSError) as exc:
            parser.error(str(exc))
        print(json.dumps({key: {"status": result["status"], "errors": len(result["errors"]), "hash_validation": result.get("hash_validation")} for key,result in report.items()}, indent=2))
    else:
        print(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False))
    return int(any(result["errors"] for result in report.values()))


if __name__ == "__main__":
    sys.exit(main())
