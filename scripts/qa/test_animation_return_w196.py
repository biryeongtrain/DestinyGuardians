"""Targeted stdlib intake tests. Fixtures never modify the returned bundles."""

import contextlib
import copy
import csv
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "animation/audit_destiny_return.py"
SPEC = importlib.util.spec_from_file_location("audit_destiny_return_w196", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)

SUPER = Path("/Volumes/qf-ssd/DestinyGuardians-Super-Animation-VFX-2026-10-27/destiny-animation-return")
WEAPON = Path("/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return")
TAG, SKEL, RIG, WSKEL = "80A8A567", "80C3C215", "80C3C216", "80CEC236"


class Fixture:
    def __init__(self, root, weapon=False):
        root = root.resolve()
        self.root, self.weapon = root, weapon
        for tag in [TAG, SKEL, RIG] + ([WSKEL] if weapon else []):
            self.put(f"raw/{tag}.bin", f"fixture original bytes {tag}")
        action = {"tag": TAG, "name": f"Armature|{TAG}_reload_full|Base", "frames": [1.0, 3.0],
                  "fps": 30, "duration": 2/30, "curves": 10, "keys": 30, "finite": True,
                  "changingCurves": 2, "maxBoneHeadDisplacement": 0.01}
        summary = {"groupId": "sample", "bones": 1, "expected": 1, "actual": 1,
                   "missing": [], "unexpected": [], "finite": True, "moving": 1}
        bones = [{"Index": 0, "ParentNodeIndex": -1, "name": "ABCDEF12", "semanticName": "b_hand", "weaponBone": True}]
        clip = {"id": TAG, "status": "decoded_unverified", "perspective": "3P_player_rig",
                "perspectiveEvidence": "fixture player rig", "sourceNames": ["reload_full"],
                "groups": ["sample"], "relatedSuperCandidate": True,
                "skeleton": SKEL, "runtimeRig": RIG,
                "files": {"clip": f"raw/{TAG}.bin", "skeleton": f"raw/{SKEL}.bin", "runtimeRig": f"raw/{RIG}.bin",
                          "fbx": "animations/sample/sample.fbx", "blend": "animations/sample/source.blend"},
                "events": [{"path": r"content\audio\fp_melee\hunter_melee.wwise_event"}],
                "measured": action, "preferredGroup": "sample",
                "verification": {"blenderImported": True, "gameplayVerified": False}}
        self.manifest = {"schemaVersion": 1, "template": False, "status": "partial", "game": {},
                         "clips": [clip], "summary": {}, "coverage": [], "limitations": ["fixture"]}
        if weapon:
            self.manifest.update(scope="weapon fixture", groups=[], unresolved=["fixture"])
            clip.update(id=f"{TAG}_{SKEL}_{RIG}", perspective="1P", groupIds=["sample", "other"],
                        weaponIds=["ace_of_spades", "duke_mk_44"], sourceNames=["reload_full", "reload_special"],
                        tags={"clip": TAG, "skeleton": SKEL, "runtimeRig": RIG},
                        actualPackageEntries=[{"tag": t, "bytes": (root/f"raw/{t}.bin").stat().st_size,
                                               "sha256": audit.digest(root/f"raw/{t}.bin")} for t in [TAG, SKEL, RIG]],
                        measured={"joints": 1, "frameCount": 3, "fps": 30, "durationSeconds": 2/30,
                                  "blenderFcurves": 10, "blenderKeyCount": 30, "changingCurves": 2,
                                  "maxBoneHeadDisplacement": 0.01})
            clip["files"] = {"clip": f"raw/{TAG}.bin", "skeleton": f"raw/{SKEL}.bin", "runtimeRig": f"raw/{RIG}.bin"}
            inventories, mappings, summaries, coverage = [], [], [], []
            for gid, wid, local, selector, api_hash in [("sample", "ace_of_spades", "reload_full", "1234ABCD", 1),
                                                       ("other", "duke_mk_44", "reload_special", "5678ABCD", 2)]:
                folder = f"clips/{gid}"
                weapon_info = {"id": wid, "apiHash": api_hash, "name": wid, "itemTag": "812C4BEA", "selector": selector}
                group = {"id": gid, "weapons": [weapon_info], "skeleton": SKEL, "runtimeRig": RIG, "weaponSkeleton": WSKEL,
                         "firstPersonFbx": f"{folder}/decoded/{gid}_FirstPerson.fbx", "weaponFbx": f"{folder}/decoded/{gid}.fbx",
                         "blend": f"{folder}/blender/source.blend", "expectedClips": 1}
                group_summary = {k:v for k,v in summary.items() if k != "moving"}
                group_summary.update(groupId=gid, movingActions=1, status="decoded_unverified")
                group["blenderAudit"] = group_summary
                self.manifest["groups"].append(group)
                if gid == "sample":
                    clip["files"].update({k:group[k] for k in ("firstPersonFbx", "weaponFbx", "blend")})
                for key in ("firstPersonFbx", "weaponFbx", "blend"):
                    self.put(group[key], f"fixture {gid} {key}")
                self.dump(f"{folder}/clips.json", [{"tag": TAG, "FrameCount": 3, "NodeCount": 1, "RigControlCount": 1}])
                self.dump(f"{folder}/inspection_FirstPerson.json", {"file": f"{gid}_FirstPerson.fbx", "bones": 1, "actions": [action]})
                self.dump(f"{folder}/inspection.json", {"file": f"{gid}.fbx", "bones": 1, "actions": [action]})
                self.dump(f"{folder}/bone-map.json", bones)
                source = {"groupId": gid, "representative": wid, "selector": selector, "fallback": False,
                          "skeleton": SKEL, "runtimeRig": RIG, "weaponSkeleton": WSKEL,
                          "weapons": [weapon_info], "clips": [{"tag": TAG, "names": [local]}]}
                self.dump(f"{folder}/source-map.json", source)
                inventories.append(dict(weapon_info, skeleton=SKEL, runtimeRig=RIG, weaponSkeleton=WSKEL,
                                        fallback=False, clips=source["clips"]))
                mappings.append({"id": wid, "apiHash": api_hash, "groupId": gid})
                summaries.append(group_summary)
                coverage.append({"id": wid, "family": "hand_cannon", "status": "rig_animation_extracted", "groups": gid})
            self.dump("provenance/inventory-index.json", inventories)
            self.dump("provenance/weapon-map.json", {"mapping": mappings})
            self.dump("provenance/audit-summary.json", summaries)
            self.csv("weapon-coverage.csv", coverage)
            self.csv("clip-index.csv", [{"tag": TAG, "skeleton": SKEL, "rig": RIG,
                                          "names": "reload_full;reload_special", "groups": "sample;other"}])
            self.manifest["summary"] = {"rawFiles": 4, "targetWeapons": 2, "withAnimationRigs": 2,
                                        "reloadNotApplicableSwords": 0, "groups": 2, "uniqueRigClipPairs": 1,
                                        "uniqueSourceAnimationClips": 1, "groupActionInstances": 2,
                                        "fbxFiles": 4, "blenderGroupFiles": 2, "previewVideos": 0}
        else:
            self.put("animations/sample/sample.fbx", "fixture FBX bytes")
            self.put("animations/sample/source.blend", "fixture blend bytes")
            self.dump("animations/sample/clips.json", [{"tag": TAG, "FrameCount": 3, "NodeCount": 1, "RigControlCount": 1}])
            self.dump("animations/sample/inspection.json", dict(summary, actions=[action]))
            self.dump("provenance/final-audit-summary.json", [summary])
            self.dump("provenance/bone-map.json", bones)
            self.dump("provenance/missing-diagnostics.json", [])
            self.dump("provenance/direct-super-particles.json", [])
            self.dump("super-coverage.json", [])
            self.put("effects/particle-index.csv", "particle,material,models,direct_super_groups,fbx\n")
            self.csv("clip-index.csv", [{"tag": TAG, "status": "decoded_unverified", "names": "reload_full",
                                          "groups": "sample", "preferred_fbx": "animations/sample/sample.fbx"}])
            self.manifest["summary"] = {"rawFiles": 3, "sourceClips": 1, "decodedUniqueClips": 1, "rawOnlyClips": 0,
                                        "superRelatedSourceClips": 1, "animationFbxFiles": 1, "blenderFiles": 1,
                                        "previewVideos": 0, "particleDefinitions": 0, "directSuperLinkedParticles": 0,
                                        "effectMeshFbxFiles": 0, "effectTexturePngFiles": 0, "materialJsonFiles": 0}
        self.save()

    def put(self, name, text):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def dump(self, name, value):
        self.put(name, json.dumps(value))

    def csv(self, name, rows):
        stream = io.StringIO()
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        self.put(name, stream.getvalue())

    def rehash(self):
        self.dump("FILE_HASHES.json", [{"path": p.relative_to(self.root).as_posix(), "bytes": p.stat().st_size,
                                       "sha256": audit.digest(p)} for p in sorted(self.root.rglob("*"))
                                      if p.is_file() and p.name != "FILE_HASHES.json"])

    def save(self):
        self.dump("manifest.json", self.manifest)
        self.rehash()


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.fixture = Fixture(self.root)

    def result(self):
        return audit.audit_source(self.root)

    def assertInvalid(self, needle):
        result = self.result()
        self.assertEqual("invalid", result["status"])
        self.assertIn(needle, str(result["errors"]))

    def test_valid_read_only_super_keeps_fp_audio_as_3p(self):
        before = {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()}
        result = self.result()
        self.assertEqual([], result["errors"])
        self.assertEqual("consistent_partial_intake", result["status"])
        self.assertFalse(result["verification_basis"]["independent_animation_decode"])
        self.assertEqual(1, result["evidence"]["first_person_token"]["clips"])
        self.assertEqual({"3P_player_rig": 1}, result["manifest"]["perspectives"])
        self.assertEqual(before, {p: (p.read_bytes(), p.stat().st_mtime_ns) for p in self.root.rglob("*") if p.is_file()})

    def test_hashchanged_same_length(self):
        path = self.root/f"raw/{TAG}.bin"
        data = path.read_bytes()
        path.write_bytes(b"X" + data[1:])
        self.assertInvalid("SHA-256 mismatch")

    def test_missing_file(self):
        (self.root/f"raw/{TAG}.bin").unlink()
        self.assertInvalid("missing file")
        self.assertIn(f"raw/{TAG}.bin", self.result()["hash_validation"]["missing"])

    def test_unlisted_file(self):
        self.fixture.put("unlisted.txt", "added")
        self.assertInvalid("unlisted")

    def test_malformed_and_duplicate_json_keys(self):
        for content in ("{", '{"schemaVersion":1,"schemaVersion":1}', '{"number":NaN}', '{"number":1e999}'):
            with self.subTest(content=content):
                self.fixture.put("manifest.json", content)
                self.fixture.rehash()
                self.assertInvalid("manifest JSON")

    def test_wrong_schema_shapes(self):
        for value in (None, [], "bad"):
            with self.subTest(value=value):
                self.fixture.manifest["clips"] = value
                self.fixture.save()
                self.assertInvalid("manifest clips")

    def test_duplicate_and_malformed_hash_rows(self):
        path = self.root/"FILE_HASHES.json"
        original = json.loads(path.read_text())
        for extra in (original[0], {"path": "manifest.json", "bytes": -1, "sha256": "bad"}, None):
            with self.subTest(extra=extra):
                self.fixture.dump("FILE_HASHES.json", original + [extra])
                self.assertInvalid("FILE_HASHES[")

    def test_reject_relative_absolute_windows_and_symlink_references(self):
        for bad in ("../outside", "/etc/passwd", "raw/../manifest.json", "raw//bad", "C:\\outside", "./manifest.json"):
            with self.subTest(bad=bad):
                self.fixture.manifest["clips"][0]["files"]["clip"] = bad
                self.fixture.save()
                self.assertInvalid("unsafe relative path")
        self.fixture.manifest["clips"][0]["files"]["clip"] = f"raw/{TAG}.bin"
        path = self.root/f"raw/{TAG}.bin"
        path.unlink()
        path.symlink_to(self.root/"manifest.json")
        self.assertInvalid("symlink")

    def test_reject_hash_path_escape(self):
        self.fixture.dump("FILE_HASHES.json", [{"path": "../outside", "bytes": 0, "sha256": "0"*64}])
        self.assertInvalid("unsafe relative path")

    def test_reject_symlink_directory_and_root(self):
        (self.root/"linked").symlink_to(self.root/"raw", target_is_directory=True)
        self.assertInvalid("symlink")
        alias = self.root/"linked"
        result = audit.audit_source(alias)
        self.assertEqual("invalid", result["status"])

    def test_duplicate_and_dangling_manifest(self):
        self.fixture.manifest["clips"].append(copy.deepcopy(self.fixture.manifest["clips"][0]))
        self.fixture.save()
        self.assertInvalid("duplicate id")
        self.fixture.manifest["clips"].pop()
        self.fixture.manifest["clips"][0]["groups"] = ["unknown"]
        self.fixture.save()
        self.assertInvalid("dangling")

    def test_tag_reference_status_perspective_and_summary(self):
        baseline = copy.deepcopy(self.fixture.manifest)
        for field, value, needle in [("skeleton", TAG, "tag/file mismatch"),
                                      ("perspective", "1P", "unexpected perspective"),
                                      ("status", "raw_extracted", "raw-only clip claims")]:
            with self.subTest(field=field):
                self.fixture.manifest = copy.deepcopy(baseline)
                self.fixture.manifest["clips"][0][field] = value
                self.fixture.save()
                self.assertInvalid(needle)
        self.fixture.manifest = baseline
        self.fixture.manifest["summary"]["sourceClips"] = 100
        self.fixture.save()
        self.assertInvalid("summary sourceClips")

    def test_inspection_reconciliation_duplicate_actions_and_measurements(self):
        path = "animations/sample/inspection.json"
        baseline = json.loads((self.root/path).read_text())
        for field, value, needle in [("actual", 2, "does not reconcile"), ("moving", 0, "does not reconcile"),
                                      ("missing", [TAG], "does not reconcile")]:
            with self.subTest(field=field):
                changed = dict(baseline, **{field:value})
                self.fixture.dump(path, changed)
                self.fixture.rehash()
                self.assertInvalid(needle)
        changed = copy.deepcopy(baseline)
        changed["actions"].append(changed["actions"][0])
        self.fixture.dump(path, changed)
        self.fixture.rehash()
        self.assertInvalid("duplicate tag")
        self.fixture.dump(path, baseline)
        self.fixture.manifest["clips"][0]["measured"]["keys"] = 99
        self.fixture.save()
        self.assertInvalid("measured vs inspection mismatch")

    def test_source_frame_count_is_not_keyed_action_range(self):
        # Static/exporter frame-count differences must be disclosed, not silently equated.
        path = "animations/sample/clips.json"
        rows = json.loads((self.root/path).read_text())
        rows[0]["FrameCount"] = 4
        self.fixture.dump(path, rows)
        self.fixture.rehash()
        result = self.result()
        self.assertEqual([], result["errors"])
        self.assertEqual(4, result["groups"]["sample"]["source_frame_count_vs_action_range_differences"][0]["source_frame_count"])

    def test_weapon_group_local_names_do_not_inherit_manifest_union(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp), weapon=True)
            result = audit.audit_source(fixture.root)
            self.assertEqual([], result["errors"])
            identities = result["evidence"]["per_weapon"]
            self.assertEqual(["reload_full"], identities["ace_of_spades"][0]["reload_selections"][0]["group_local_names"])
            self.assertEqual(["reload_special"], identities["duke_mk_44"][0]["reload_selections"][0]["group_local_names"])
            source = json.loads((fixture.root/"clips/sample/source-map.json").read_text())
            source["weapons"][0]["selector"] = "BADBAD00"
            fixture.dump("clips/sample/source-map.json", source)
            fixture.rehash()
            self.assertIn("source-map weapons mismatch", str(audit.audit_source(fixture.root)["errors"]))

    def test_cli_exit_status_and_combined_schemas(self):
        with tempfile.TemporaryDirectory() as temp:
            fixture = Fixture(Path(temp), weapon=True)
            stream = io.StringIO()
            with contextlib.redirect_stdout(stream):
                status = audit.main(["--source", str(self.root), "--source", str(fixture.root)])
            self.assertEqual(0, status)
            self.assertEqual({"super", "weapon"}, set(json.loads(stream.getvalue())))
        (self.root/f"raw/{TAG}.bin").unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, audit.main(["--source", str(self.root)]))

    def test_reports_cannot_overwrite_input_or_follow_symlink(self):
        with patch.object(audit, "REPORT_DIR", self.root):
            with self.assertRaisesRegex(audit.Invalid, "inside source"):
                audit.write_reports({}, [str(self.root)])
        alias = self.root/"report-link"
        alias.symlink_to(self.root, target_is_directory=True)
        with patch.object(audit, "REPORT_DIR", alias):
            with self.assertRaisesRegex(audit.Invalid, "symlink"):
                audit.write_reports({}, ["/elsewhere"])


class RealBundleTests(unittest.TestCase):
    @unittest.skipUnless(SUPER.is_dir() and WEAPON.is_dir(), "real returned bundles not mounted")
    def test_both_real_sources_read_only(self):
        snapshots = {p: (audit.digest(p), p.stat().st_mtime_ns) for root in (SUPER, WEAPON)
                     for p in (root/"FILE_HASHES.json", root/"manifest.json")}
        player, weapon = audit.audit_source(SUPER), audit.audit_source(WEAPON)
        self.assertEqual([], player["errors"])
        self.assertEqual([], weapon["errors"])
        self.assertEqual(5011, player["hash_validation"]["verified_files"])
        self.assertEqual(796, weapon["hash_validation"]["verified_files"])
        self.assertEqual(11, player["raw_only"]["count"])
        self.assertEqual(2160, player["observed_counts"]["decodedUniqueClips"])
        self.assertEqual(2182, player["source_action_instances"])
        self.assertEqual(509, weapon["source_action_instances"])
        identities = weapon["evidence"]["per_weapon"]
        for wid, expected in [("ace_of_spades", {"80A8A567"}), ("duke_mk_44", {"80A8A53D"}),
                              ("izanagis_burden", {"80A8A140", "80A8A150", "80A8A14D"})]:
            full = {r["tag"] for identity in identities[wid] for r in identity["reload_selections"]
                    if "reload_full" in r["group_local_names"]}
            self.assertEqual(expected, full)
        self.assertFalse(weapon["verification_basis"]["independent_animation_decode"])
        self.assertEqual(snapshots, {p: (audit.digest(p), p.stat().st_mtime_ns) for p in snapshots})


if __name__ == "__main__":
    unittest.main()
