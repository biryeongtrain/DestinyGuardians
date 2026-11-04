#!/usr/bin/env python3
"""Standalone W199 source shape/contact checks; no subprocess, native client or writes.
Run bundled Python with -B. Central Java/pitch/Vision gates belong to master.
"""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import build_shadowshot_source_w199 as w


def clips(model):
    return {c["name"]: c for c in model["animations"]}


def raw_clips(path):
    # Compare each complete serialized clip, including UUIDs and whitespace.
    text = path.read_text()
    offset = text.index('"animations": [') + len('"animations": [')
    decoder = json.JSONDecoder()
    result = {}
    while True:
        while text[offset].isspace() or text[offset] == ",":
            offset += 1
        if text[offset] == "]":
            return result
        obj, end = decoder.raw_decode(text, offset)
        result[obj["name"]] = text[offset:end].encode()
        offset = end


class ShadowshotSourceW199(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(w.SOURCE.read_text())
        cls.model = json.loads(w.ART.read_text())
        cls.pack = json.loads(w.PACK.read_text())
        cls.data = json.loads(w.DATA.read_text())
        cls.old = clips(cls.source)[w.ATTACK]
        cls.new = clips(cls.model)[w.ATTACK]

    def test_pinned_evaluated_ground_and_air_are_distinct_and_events_uninterpreted(self):
        w.validate_data(self.data)
        ground, air = (self.data["clips"][n] for n in (w.GROUND, w.AIR))
        self.assertEqual(ground["events"], air["events"])
        self.assertTrue(all(e["type"] == "S80808C1A" for e in ground["events"]))
        self.assertNotEqual(ground["frames"][0]["matrices"], air["frames"][0]["matrices"])
        self.assertEqual(w.GROUND, self.data["retarget"]["selected"])
        self.assertIn("inspected/deferred", self.data["retarget"]["airStatus"])
        # Semantic side names and actual parent paths, not FBX bone-list order.
        for _, _, chain in w.LEGS:
            for a, b in zip((w.HIP,)+chain, chain):
                self.assertEqual(a, self.data["bones"][b]["parent"])
        feet = [self.data["bones"][chain[-1]]["head"] for _, _, chain in w.LEGS]
        self.assertLess(feet[0][1], 0)
        self.assertGreater(feet[1][1], 0)

    def test_saved_products_reproduce_without_subprocess_or_external_source(self):
        result = w.compose(self.source, self.data)
        w.validate(result, self.source)
        self.assertEqual(w.ART.read_bytes(), w.encoded(result))
        self.assertEqual(w.PACK.read_bytes(), w.encoded(w.export(result)))
        self.assertEqual(w.DATA.read_bytes(), w.encoded(self.data))

    def test_rig_all_twenty_names_source_arc_and_nonvoid_clip_bytes_preserved(self):
        w.validate(self.model, self.source)
        self.assertEqual(20, len(self.pack["animations"]))
        self.assertEqual(w.export(self.model), self.pack)
        for before_path, after_path in ((w.SOURCE, w.ART), (w.BASE_PACK, w.PACK)):
            before, after = raw_clips(before_path), raw_clips(after_path)
            self.assertEqual(set(before), set(after))
            for name in before:
                if name != w.ATTACK:
                    self.assertEqual(before[name], after[name], name)
        a = {v["name"]: v for v in self.old["animators"].values()}
        b = {v["name"]: v for v in self.new["animators"].values()}
        self.assertEqual(set(w.CHANGED), {n for n in a if a[n] != b[n]})
        self.assertEqual(a["player_root"], b["player_root"])
        self.assertEqual(.9, self.new["length"])
        self.assertEqual("once", self.new["loop"])
        for animator in self.new["animators"].values():
            for key in animator["keyframes"]:
                if key["channel"] == "position":
                    self.assertEqual("player_root", animator["name"])
                    self.assertEqual(0, key["data_points"][0]["x"])
                    self.assertEqual(0, key["data_points"][0]["z"])

    def test_dense_contact_trajectory_and_compensated_chest_parent(self):
        max_trajectory = max_contact = max_cheek = max_aim = 0
        # Includes authoring keys, 1ms inter-key samples and arbitrary phase offsets.
        times = sorted({i/1000 for i in range(901)} | {i/1000+.00037 for i in range(900)})
        for t in times:
            p, y = w.h19.sample(self.new, t)
            original, oy = w.h19.sample(self.old, t)
            m, old = w.h19.fk(self.model, p, y), w.h19.fk(self.source, original, oy)
            for n in ("pc_chest", "h_ph_head", "pli_left_item", "pri_right_item"):
                for point in ([0, 0, 0], [4.2, 3, -2.6], [0, 2, 8.24], [0, 0, -1]):
                    gap = w.h19.norm(w.h19.sub(w.h19.point(m[n], point), w.h19.point(old[n], point)))
                    max_trajectory = max(max_trajectory, gap)
                    self.assertLess(gap, .0001, (t, n, point))
            # Test an additive chest pitch against the complete changing parent
            # chain. Actual live controls/handed item conversion remain Java/native QA.
            if abs(t*100-round(t*100)) < 1e-8:
                for pitch in (-60, 0, 60):
                    pp, op = copy.deepcopy(p), copy.deepcopy(original)
                    pp["pc_chest"][0] += pitch
                    op["pc_chest"][0] += pitch
                    pm, om = w.h19.fk(self.model, pp, y), w.h19.fk(self.source, op, oy)
                    for n in ("h_ph_head", "pli_left_item", "pri_right_item"):
                        self.assertLess(max(abs(pm[n][i][j]-om[n][i][j])
                                            for i in range(3) for j in range(4)), .0001)
            if t <= .30:
                right = w.h19.point(m["pri_right_item"], [0, 0, 0])
                nock = w.h19.point(m["pli_left_item"], [0, 2, 8.24])
                cheek = w.h19.point(m["h_ph_head"], [4.2, 3, -2.6])
                contact, anchor = w.h19.norm(w.h19.sub(right, nock)), w.h19.norm(w.h19.sub(right, cheek))
                aim = w.h19.norm(w.h19.sub(w.h19.vector(m["pli_left_item"], [0, 0, -1]), [0, 0, -1]))
                max_contact, max_cheek, max_aim = max(max_contact, contact), max(max_cheek, anchor), max(max_aim, aim)
                self.assertLess(contact, .0001, t)
                self.assertLess(anchor, .0001, t)
                self.assertLess(aim, .0001, t)
        # Release separation remains precisely inherited, rather than constrained
        # hands continuing to stick to a released string.
        p, y = w.h19.sample(self.new, .35)
        m = w.h19.fk(self.model, p, y)
        self.assertGreater(w.h19.norm(w.h19.sub(w.h19.point(m["pri_right_item"], [0, 0, 0]),
                                              w.h19.point(m["pli_left_item"], [0, 2, 8.24]))), 1.5)
        print("W199 max model-unit trajectory/contact/cheek, aim vector error:",
              max_trajectory, max_contact, max_cheek, max_aim)

    def test_source_asymmetric_knees_thigh_shape_and_recovery(self):
        # World-space bend-plane rotation must follow measured source motion;
        # limb length/root translation are deliberately not copied.
        for t, seconds in w.PHASES:
            p, y = w.h19.sample(self.new, t)
            old, oy = w.h19.sample(self.old, t)
            matrices, before = w.h19.fk(self.model, p, y), w.h19.fk(self.source, old, oy)
            pts = w.w197.source_points(self.data, w.GROUND, seconds)
            ref = w.w197.source_points(self.data, w.GROUND, 1.3)
            if .05 <= t <= .75:
                for upper, lower, chain in w.LEGS:
                    f, bend = w.w197.leg_frame(pts, chain)
                    neutral, neutral_bend = w.w197.leg_frame(ref, chain)
                    self.assertAlmostEqual(-min(155, max(0, abs(old[lower][0])+bend-neutral_bend)),
                                           p[lower][0], places=7)
                    # Delta comparing target world thighs against the source
                    # anatomical bend-plane delta is invariant to hip compensation.
                    actual = w.h15.mm(w.w197.rotation(matrices[upper]), w.h19.inverse_rotation(w.w197.rotation(before[upper])))
                    expected = w.h15.mm(w.C, w.h15.mm(f, w.h15.mm(w.h19.inverse_rotation(neutral), w.h19.inverse_rotation(w.C))))
                    self.assertLess(max(abs(actual[i][j]-expected[i][j]) for i in range(3) for j in range(3)), 1e-7)
        for t in (.15, .30):
            p, y = w.h19.sample(self.new, t)
            old, oy = w.h19.sample(self.old, t)
            a, b = w.h19.fk(self.model, p, y), w.h19.fk(self.source, old, oy)
            for _, lower, _ in w.LEGS:
                self.assertGreater(w.h19.norm(w.h19.sub(w.h19.point(a[lower], [0, -5.625, 0]),
                                                       w.h19.point(b[lower], [0, -5.625, 0]))), 2)
        at15 = w.h19.sample(self.new, .15)[0]
        at30 = w.h19.sample(self.new, .30)[0]
        self.assertLess(at15["prfl_right_foreleg"][0], at15["plfl_left_foreleg"][0]-40)
        self.assertLess(at30["plfl_left_foreleg"][0], at30["prfl_right_foreleg"][0]-20)
        for t in (0, .90):
            self.assertEqual(w.h19.sample(self.new, t), w.h19.sample(self.old, t))

    def test_linear_continuous_bounded_keys_and_measure_lift_clearance(self):
        floor = []
        for animator in self.new["animators"].values():
            if animator["name"] not in w.CHANGED:
                continue
            keys = animator["keyframes"]
            self.assertLessEqual(len(keys), 256)
            self.assertEqual(len(keys), len({k["time"] for k in keys}))
            self.assertEqual([0, .9], [keys[0]["time"], keys[-1]["time"]])
            for a, b in zip(keys, keys[1:]):
                self.assertEqual("linear", a["interpolation"])
                self.assertLess(max(abs(a["data_points"][0][axis]-b["data_points"][0][axis]) for axis in "xyz"), 35)
        for i in range(901):
            t = i/1000
            p, y = w.h19.sample(self.new, t)
            self.assertTrue(all(math.isfinite(v) for values in p.values() for v in values))
            for _, lower, _ in w.LEGS:
                self.assertTrue(-155.000001 <= p[lower][0] <= 0, (t, lower, p[lower]))
            floor.append((t, y-w.h15.floor_y(self.model, p)))
        # Measurement, not a ground-contact pass: inherited root/drop trajectory
        # deliberately unchanged. Master must check actual assisted entity lift.
        print("W199 skin clearance from fixed model anchor, min/max (time, units):",
              min(floor, key=lambda v: v[1]), max(floor, key=lambda v: v[1]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
