"""Small synthetic ZIPs only; never touch the server pack or project fixture."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile


SPEC = importlib.util.spec_from_file_location(
    "pack_model_closure_w236", Path(__file__).with_name("pack_model_closure_w236.py"))
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class PackClosureTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="w236-closure-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def pack(self, files, name="pack.zip"):
        path = self.root / name
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
            for key, value in files.items():
                archive.writestr(key, json.dumps(value, separators=(",", ":")))
        return path

    def test_missing_nested_geometry_and_object_model_not_a_reference(self):
        path = self.pack({"assets/demo/items/nested/selector.json": {"model": {
            "type": "select", "property": "custom_model_data",
            "fallback": {"type": "model", "model": "item/stick"},
            "cases": [{"when": "x", "model": {"type": "minecraft:composite", "models": [
                {"type": "minecraft:model", "model": "demo:missing"},
                {"type": "minecraft:model", "model": "demo:missing"},
            ]}}],
        }}})
        report = audit.audit_pack(path)
        self.assertFalse(report["closure"]["ok"])
        self.assertEqual(report["closure"]["missing_custom_count"], 1)
        self.assertEqual(report["closure"]["error_count"], 0)
        self.assertEqual(report["closure"]["missing_custom_models"][0]["model"], "demo:missing")
        self.assertEqual(report["items"]["reference_count"], 3)
        self.assertEqual(report["items"]["unique_refs"], 2)
        self.assertEqual(report["closure"]["unique_vanilla_refs_skipped"], 1)

    def test_parent_chain_missing_dependency_and_cycle(self):
        files = {
            "assets/demo/items/a.json": {"model": {"type": "model", "model": "demo:child"}},
            "assets/demo/models/child.json": {"parent": "demo:middle", "elements": []},
            "assets/demo/models/middle.json": {"parent": "demo:missing_parent"},
            # Unreachable model JSON must not be parsed or included in closure.
            "assets/demo/models/orphan.json": ["invalid model"],
        }
        missing = audit.audit_pack(self.pack(files))
        self.assertEqual(missing["closure"]["missing_custom_models"][0]["chain"],
                         ["demo:child", "demo:middle", "demo:missing_parent"])
        self.assertEqual(missing["closure"]["custom_models_loaded"], 2)
        files["assets/demo/models/missing_parent.json"] = {"parent": "minecraft:item/generated"}
        complete = audit.audit_pack(self.pack(files, "complete.zip"))
        self.assertTrue(complete["closure"]["ok"])
        self.assertEqual(complete["closure"]["parent_edge_count"], 3)
        files["assets/demo/models/missing_parent.json"] = {"parent": "demo:child"}
        cycle = audit.audit_pack(self.pack(files, "cycle.zip"))
        self.assertFalse(cycle["closure"]["ok"])
        self.assertIn("parent cycle", cycle["closure"]["errors"][0]["message"])

    def test_special_base_parent_and_renderer_object(self):
        files = {
            "assets/demo/items/special.json": {"model": {
                "type": "minecraft:special", "base": "demo:special_base",
                "model": {"type": "minecraft:head", "kind": "player"},
            }},
            "assets/demo/models/special_base.json": {"parent": "demo:base_parent"},
        }
        missing = audit.audit_pack(self.pack(files))
        self.assertEqual(missing["items"]["special_base_count"], 1)
        self.assertEqual(missing["items"]["geometry_count"], 0)
        self.assertEqual(missing["closure"]["missing_custom_models"][0]["model"], "demo:base_parent")
        files["assets/demo/models/base_parent.json"] = {"parent": "item/generated"}
        complete = audit.audit_pack(self.pack(files, "complete.zip"))
        self.assertTrue(complete["closure"]["ok"])
        files["assets/demo/items/special.json"]["model"]["base"] = {"model": "demo:wrong"}
        invalid = audit.audit_pack(self.pack(files, "invalid.zip"))
        self.assertFalse(invalid["closure"]["ok"])
        self.assertEqual(invalid["closure"]["missing_custom_count"], 0)
        self.assertIn("must be a string", invalid["closure"]["errors"][0]["message"])

    def test_metrics_comparison_cli_exit_and_read_only_input(self):
        files = {
            "assets/demo/items/a.json": {"model": {"type": "composite", "models": [
                {"type": "model", "model": "demo:a", "tints": [
                    {"type": "minecraft:constant", "value": 1},
                    {"type": "minecraft:custom_model_data", "index": 64},
                ]}, {"type": "model", "model": "demo:a"},
            ]}},
            "assets/demo/items/b.json": {"model": {"type": "empty"}},
            "assets/demo/models/a.json": {"parent": "item/generated"},
        }
        path = self.pack(files)
        before = path.read_bytes()
        report = audit.audit_pack(path)
        raw = sum(len(json.dumps(files[p], separators=(",", ":")).encode())
                  for p in files if "/items/" in p)
        self.assertEqual(report["items"]["raw_bytes"], raw)
        self.assertEqual(report["items"]["count"], 2)
        self.assertEqual(report["items"]["unique_refs"], 1)
        self.assertEqual(report["items"]["reference_count"], 2)
        self.assertEqual(report["items"]["tint_source_count"], 2)
        self.assertEqual(report["items"]["top_by_tint_source_count"][0]["path"],
                         "assets/demo/items/a.json")
        self.assertEqual(report["closure"]["custom_models_loaded"], 1)
        baseline = self.root / "baseline.json"
        baseline.write_text(json.dumps(report))
        del files["assets/demo/models/a.json"]
        broken = self.pack(files, "broken.zip")
        output = self.root / "comparison.json"
        self.assertEqual(audit.main([str(broken), "--compare", str(baseline),
                                     "--report", str(output)]), 1)
        comparison = json.loads(output.read_text())["comparison"]
        self.assertEqual(comparison["missing_added"], ["demo:a"])
        self.assertEqual(comparison["delta_current_minus_baseline"]["items.raw_bytes"], 0)
        self.assertEqual(audit.main([str(path), "--report", str(path)]), 2)
        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
