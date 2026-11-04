#!/usr/bin/env python3
"""Bounded W161 graph regressions; run with python3 -B (no build/native writes)."""
import importlib.util
import itertools
import json
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("ammit_w161", ROOT/"scripts/generate_ammit_crouch_w161.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)
CONTEXTS = (*g.FIRST, *g.THIRD, "gui", "ground", "fixed", "head", "none", "on_shelf")


def evaluate(node, context, flags, pose, progress):
    kind = node["type"]
    if kind == "minecraft:model":
        return node["model"]
    if kind == "minecraft:composite":
        return tuple(evaluate(child, context, flags, pose, progress) for child in node["models"])
    index = node.get("index", 0)
    if kind == "minecraft:condition":
        assert node["property"] == "minecraft:custom_model_data"
        flag = flags[index] if index < len(flags) else False
        return evaluate(node["on_true" if flag else "on_false"], context, flags, pose, progress)
    if kind == "minecraft:select":
        value = context if node["property"] == "minecraft:display_context" else pose
        for case in node["cases"]:
            when = case["when"] if isinstance(case["when"], list) else [case["when"]]
            if value in when:
                return evaluate(case["model"], context, flags, pose, progress)
        return evaluate(node["fallback"], context, flags, pose, progress)
    if kind == "minecraft:range_dispatch":
        selected = node["fallback"]
        for entry in node["entries"]:
            if progress >= entry["threshold"]:
                selected = entry["model"]
        return evaluate(selected, context, flags, pose, progress)
    raise AssertionError("Unexpected graph type: " + kind)


class AmmitCrouchW161Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = g.generate()
        cls.graphs = {p: json.loads(cls.outputs[p]) for p in g.BASELINE}
        cls.manifest = json.loads(cls.outputs[g.MANIFEST])

    def test_01_generated_files_match_readonly_verify(self):
        self.assertEqual(11, len(self.outputs))
        for path, raw in self.outputs.items():
            self.assertEqual(raw, (ROOT/path).read_bytes(), path)
        with patch.object(Path, "write_bytes", side_effect=AssertionError("verify wrote")):
            self.assertEqual(0, g.main(["--verify"]))

    def test_02_seven_seeded_graphs_restore_byte_exactly(self):
        for path, updated in self.graphs.items():
            self.assertEqual(g.BASELINE[path], g.sha(g.encode(g.unwrap(updated))), path)

    def test_03_exactly_three_wrappers_per_graph(self):
        for path, updated in self.graphs.items():
            wrappers = [n for _, n in g.walk(updated)
                        if n.get("property") == "minecraft:display_context"
                        and n.get("fallback", {}).get("model") in g.CANONICAL]
            self.assertEqual(3, len(wrappers), path)
            self.assertEqual(set(g.CANONICAL), {n["fallback"]["model"] for n in wrappers})
            for n in wrappers:
                self.assertEqual(g.wrapper(n["fallback"]), n)
                self.assertEqual(list(g.THIRD), n["cases"][0]["when"])
                self.assertEqual(1, n["cases"][0]["model"]["index"])

    def test_04_thirdperson_both_hands_and_grip_flags(self):
        for path, updated in self.graphs.items():
            for context, pose, grip, crouch in itertools.product(g.THIRD, ("hip", "ads", "inspect"), (False, True), (False, True)):
                original = g.unwrap(updated)["model"]
                before = evaluate(original, context, [grip, crouch], pose, .7)
                after = evaluate(updated["model"], context, [grip, crouch], pose, .7)
                self.assertEqual(g.child_id(pose) if grip and crouch else before, after, path)

    def test_05_standing_release_ignores_lingering_ads_progress(self):
        for path, updated in self.graphs.items():
            for context, progress in itertools.product(g.THIRD, [i/20 for i in range(21)]):
                self.assertEqual("destiny:weapon/auto_rifle/ammit_ar2_ads_twohand",
                                 evaluate(updated["model"], context, [True, False], "ads", progress), path)
                self.assertEqual(g.child_id("ads"),
                                 evaluate(updated["model"], context, [True, True], "ads", progress), path)

    def test_06_firstperson_subtrees_and_frame_lists_preserved(self):
        animated = 0
        for updated in self.graphs.values():
            original = g.unwrap(updated)
            self.assertEqual(g.firstperson(original), g.firstperson(updated))
            self.assertEqual(g.fingerprint(original, "entries"), g.fingerprint(updated, "entries"))
            animated += len(g.firstperson(updated))
        self.assertEqual(6, animated)

    def test_07_all_non_thirdperson_results_preserved(self):
        for path, updated in self.graphs.items():
            before = g.unwrap(updated)["model"]
            for context, pose, grip, crouch, progress in itertools.product(
                    [c for c in CONTEXTS if c not in g.THIRD], ("hip", "ads", "inspect"),
                    (False, True), (False, True), (-1, 0, .5, 1, 2, 3, 100)):
                flags = [grip, crouch]
                self.assertEqual(evaluate(before, context, flags, pose, progress),
                                 evaluate(updated["model"], context, flags, pose, progress), path)

    def test_08_missing_transient_flag_defaults_to_standing(self):
        for updated in self.graphs.values():
            for context, pose, flags in itertools.product(g.THIRD, ("hip", "ads", "inspect"), ([], [False], [True])):
                self.assertEqual(evaluate(g.unwrap(updated)["model"], context, flags, pose, .5),
                                 evaluate(updated["model"], context, flags, pose, .5))

    def test_09_children_inherit_exact_pose_override_only_thirdperson(self):
        for canonical, pose in g.CANONICAL.items():
            child = json.loads(self.outputs[g.model_path(g.child_id(pose))])
            self.assertEqual({"parent", "display"}, set(child))
            self.assertEqual(canonical, child["parent"])
            self.assertEqual({hand: g.CORRECTED for hand in g.THIRD}, child["display"])
            base = json.loads((ROOT/g.model_path(canonical)).read_text())
            self.assertEqual({hand: g.OLD for hand in g.THIRD}, {hand: base["display"][hand] for hand in g.THIRD})

    def test_10_correction_preserves_grip_for_both_reflected_hands(self):
        for hand in (-1, 1):
            old = g.display_point(g.GRIP, g.OLD, hand)
            new = g.display_point(g.GRIP, g.CORRECTED, hand)
            for a, b in zip(old, new):
                self.assertAlmostEqual(a, b, delta=1e-6)
        self.assertAlmostEqual(.4, g.math.radians(g.CORRECTED["rotation"][0] - g.OLD["rotation"][0]), delta=1e-7)

    def test_11_protected_model_and_w160_sources_unchanged(self):
        for path, expected in g.PROTECTED.items():
            self.assertEqual(expected, g.sha((ROOT/path).read_bytes()), path)
            record = self.manifest["preservedSources"][path]
            self.assertEqual(record["beforeSha256"], record["afterSha256"])

    def test_12_source_drift_refused_before_writing(self):
        for attr in ("BASELINE", "PROTECTED"):
            drift = dict(getattr(g, attr))
            drift[next(iter(drift))] = "0"*64
            with patch.object(g, attr, drift), patch.object(Path, "write_bytes", side_effect=AssertionError("drift wrote")):
                with self.assertRaisesRegex(ValueError, "drift"):
                    g.generate()

    def test_13_malformed_wrapper_and_ungated_variant_refused(self):
        leaf = {"type": "minecraft:model", "model": next(iter(g.CANONICAL))}
        damaged = g.wrapper(leaf)
        damaged["cases"][0]["model"]["index"] = 0
        with self.assertRaisesRegex(ValueError, "Malformed"):
            g.unwrap(damaged)
        with self.assertRaisesRegex(ValueError, "outside"):
            g.unwrap({"type": "minecraft:model", "model": g.child_id("hip")})

    def test_14_generation_idempotent_without_writes(self):
        with patch.object(Path, "write_bytes", side_effect=AssertionError("idempotence wrote")):
            self.assertEqual(self.outputs, g.generate())
            self.assertEqual(0, g.main([]))

    def test_15_manifest_records_hashes_and_pending_acceptance(self):
        self.assertEqual("pending; unavailable this turn", self.manifest["native"]["status"])
        self.assertFalse(self.manifest["native"]["visualAcceptance"])
        self.assertEqual(0, self.manifest["native"]["operations"])
        for path, record in self.manifest["graphs"].items():
            self.assertEqual(record["beforeSha256"], record["restoredSourceSha256"])
            self.assertEqual(record["afterSha256"], g.sha(self.outputs[path]))
            self.assertEqual(record["firstpersonBefore"], record["firstpersonAfter"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
