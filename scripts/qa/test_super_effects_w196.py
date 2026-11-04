#!/usr/bin/env python3
"""Scoped synthetic delivery fixtures: broken links, ownership, assets and timing.

Run: rtk proxy python3 -B scripts/qa/test_super_effects_w196.py
No external applications, subprocesses, original delivery writes or repo-wide gate.
"""

import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "animation/audit_super_effects.py"
SPEC = importlib.util.spec_from_file_location("audit_super_effects_w196", SCRIPT)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class EffectLinksTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="w196-effect-links-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "delivery"
        self.root.mkdir()
        self.clip = "80A8A7CC"
        self.entity = "80D942CC"
        self.component = "80D8B524"
        self.particle = "80D8B513"
        self.candidate = "80C2FFCD"
        self.material = "80D8FAB1"
        self.texture = "80D8A475"
        self.group = "hunter_spectral_blades_event_linked"
        self.event = dict(type="S80808C13", startFrame=5, marker="BA5B68D6",
                          eventTag=self.entity, path=r"content\supers\void_blade\fx\trail.sequence.tft")
        self.claim = dict(clip=self.clip, group=self.group, sequence=self.entity,
                          component=self.component, particle=self.particle,
                          nodeName="1329E0C2", start=0.033, duration=0.0001,
                          evidence="typed_animation_frame_event_to_entity_sequence_particle")
        self.put("manifest.json", dict(summary=dict(directSuperLinkedParticles=1), clips=[
            dict(id=self.clip, groups=[self.group], relatedSuperCandidate=True,
                 sourceNames=["legacy_name"], events=[self.event]),
            dict(id="80A8A922", groups=["hunter_arc_staff"], relatedSuperCandidate=True,
                 events=[dict(type="S80808C1A", fields=dict(Unk00=33, Unk04=24))]),
            dict(id="80A8AD97", groups=["hunter_shadowshot"], relatedSuperCandidate=True, events=[])]))
        self.put("provenance/frame-events.json", [dict(tag=self.clip, events=[self.event]),
            dict(tag="80A8A922", events=[dict(type="S80808C1A", fields=dict(Unk00=33, Unk04=24))]),
            dict(tag="80A8AD97", events=[])])
        self.put("provenance/direct-super-particles.json", [self.claim])
        self.put("provenance/super-event-seeds.json", [dict(clip=self.clip, group=self.group, **self.event)])
        self.put("provenance/effects-graph.json", dict(particles=[self.particle, self.candidate],
            edges=[dict(source="80A8A922", target=self.candidate, kind="aligned_u32_candidate")]))
        self.put("provenance/entity-index.json", [dict(entity=self.entity, components=[self.component])])
        self.put("provenance/player-sequences.json", [dict(component=self.component, nodes=[
            dict(type="SSequenceParticleSystem", particles=[self.particle])])])
        self.put("provenance/effects-results.json", [dict(particle=p, material=self.material, models=[])
                                                   for p in [self.particle, self.candidate]])
        p = self.root / "effects/particle-index.csv"
        p.parent.mkdir(parents=True)
        p.write_text("particle,material,models,direct_super_groups,fbx\n"
                     f"{self.particle},{self.material},,{self.group},\n"
                     f"{self.candidate},{self.material},,,\n", encoding="utf-8-sig")
        self.put(f"effects/Materials/{self.material}.json", dict(Hash=self.material, Material=dict(
            Pixel=dict(Textures={"0": dict(Hash=self.texture, Dimension="2D")}),
            Vertex=dict(Textures={}))))
        p = self.root / f"effects/Textures/{self.texture}.png"
        p.parent.mkdir(parents=True)
        p.write_bytes(b"fixture: asset existence only; not a valid PNG")
        for tag in [self.clip, self.entity, self.component, self.particle, self.candidate, self.material]:
            p = self.root / f"raw/{tag}.bin"
            p.parent.mkdir(exist_ok=True)
            p.write_bytes(b"fixture: no binary decoding")

    def put(self, relative, value):
        p = self.root / relative
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(value), encoding="utf-8")

    def read(self, relative):
        return json.loads((self.root / relative).read_text())

    def run_audit(self, **kwargs):
        return audit.Audit(self.root).run(**kwargs)

    def codes(self, report):
        return {i["code"] for i in report["issues"]}

    def test_real_typed_chain_and_graph_candidate_do_not_transfer_to_arc_staff(self):
        report = self.run_audit()
        self.assertEqual(report["direct_links"][0]["status"], "json_chain_substantiated")
        self.assertFalse(report["summary"]["issue_counts"].get("error"))
        arc = report["priority_groups"]["hunter_arc_staff"]
        self.assertEqual(arc["reported_direct_particles"], [])
        self.assertEqual(arc["unknown_schema_events"][0]["event"]["fields"]["Unk00"], 33)
        self.assertEqual(report["particle_assets"][0]["classification"], "graph_candidate_only")
        self.assertIn(self.group, report["other_groups"])

    def test_finite_fractional_sequence_times_remain_ambiguous(self):
        report = self.run_audit()
        time = report["direct_links"][0]["timing"]
        self.assertEqual(time["start"], 0.033)
        self.assertEqual(time["duration"], 0.0001)
        self.assertEqual(time["unit"], "unresolved")
        self.assertEqual(time["synchronization"], "unresolved")
        self.assertIn("sequence_time_unit_unknown", self.codes(report))
        self.assertNotIn("seconds", time)
        self.assertNotIn("ticks", time)

    def test_reported_claim_and_graph_edge_cannot_replace_missing_nodes(self):
        self.put("provenance/player-sequences.json", [])
        report = self.run_audit()
        self.assertEqual(report["direct_links"][0]["status"], "reported_only")
        self.assertIn("typed_component_nodes_json_absent", report["direct_links"][0]["missing_evidence"])
        self.assertEqual(report["summary"]["json_substantiated_direct_particles"], 0)

    def test_existing_component_with_different_particle_contradicts_claim(self):
        self.put("provenance/player-sequences.json", [dict(component=self.component, nodes=[
            dict(type="SSequenceParticleSystem", particles=[self.candidate])])])
        report = self.run_audit()
        self.assertIn("component_particle_mismatch", self.codes(report))
        self.assertEqual(report["direct_links"][0]["status"], "contradicted_or_dangling")

    def test_entity_must_actually_own_component(self):
        self.put("provenance/entity-index.json", [dict(entity=self.entity, components=[])])
        report = self.run_audit()
        self.assertIn("event_component_mismatch", self.codes(report))
        self.assertEqual(report["summary"]["json_substantiated_direct_particles"], 0)

    def test_missing_entity_json_is_gap_not_a_proven_link(self):
        self.put("provenance/entity-index.json", [])
        report = self.run_audit()
        self.assertIn("event_entity_components_json_absent", report["direct_links"][0]["missing_evidence"])
        self.assertEqual(report["direct_links"][0]["status"], "reported_only")

    def test_seed_requires_exact_manifest_occurrence_including_frame_and_path(self):
        for field, bad in [("startFrame", 6), ("path", r"other\fake.sequence.tft"), ("marker", "12345678")]:
            with self.subTest(field=field):
                self.put("provenance/super-event-seeds.json", [dict(clip=self.clip, group=self.group,
                         **{**self.event, field: bad})])
                report = self.run_audit()
                self.assertIn("seed_event_not_found", self.codes(report))
                self.assertIn("unsubstantiated_direct_event", self.codes(report))
                self.assertNotEqual(report["direct_links"][0]["status"], "json_chain_substantiated")

    def test_dangling_raw_particle_and_referenced_texture_are_errors(self):
        (self.root / f"raw/{self.particle}.bin").unlink()
        (self.root / f"effects/Textures/{self.texture}.png").unlink()
        report = self.run_audit()
        missing = [i["detail"] for i in report["issues"] if i["code"] == "missing_or_empty_asset"]
        self.assertIn(f"raw/{self.particle}.bin", missing)
        self.assertIn(f"effects/Textures/{self.texture}.png", missing)
        self.assertEqual(report["direct_links"][0]["status"], "contradicted_or_dangling")

    def test_csv_cannot_assign_candidate_to_a_direct_group(self):
        p = self.root / "effects/particle-index.csv"
        p.write_text(p.read_text(encoding="utf-8-sig").replace(
            f"{self.candidate},{self.material},,,", f"{self.candidate},{self.material},,hunter_arc_staff,"))
        self.assertIn("csv_direct_group_mismatch", self.codes(self.run_audit()))

    def test_supplemental_actual_schema_can_close_component_evidence_gap(self):
        nodes = self.read("provenance/player-sequences.json")
        self.put("provenance/player-sequences.json", [])
        supplement = self.base / "component-nodes.json"
        supplement.write_text(json.dumps(nodes))
        report = self.run_audit(components_json=[supplement])
        self.assertEqual(report["direct_links"][0]["status"], "json_chain_substantiated")
        self.assertIn(str(supplement), report["input_fingerprints"])

    def test_negative_timing_and_incomplete_direct_rows_fail(self):
        self.put("provenance/direct-super-particles.json", [{**self.claim, "duration": -1}, dict(error="decode failed")])
        report = self.run_audit()
        self.assertIn("invalid_sequence_time", self.codes(report))
        self.assertIn("incomplete_direct_claim", self.codes(report))

    def test_cli_partial_exit_and_read_only_source_output_guard(self):
        outputs = ["--json", str(self.base / "report.json"), "--markdown", str(self.base / "report.md")]
        args = ["--source-root", str(self.root)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(audit.main(args + outputs), 0)
            self.assertEqual(audit.main(args + outputs + ["--require-substantiated"]), 2)
        original = (self.root / "manifest.json").read_bytes()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            audit.main(args + ["--json", str(self.root / "manifest.json"), "--markdown", str(self.base / "x.md")])
        self.assertEqual(raised.exception.code, 2)
        self.assertEqual((self.root / "manifest.json").read_bytes(), original)

    def test_cli_dangling_link_fails_even_without_strict_option(self):
        (self.root / f"raw/{self.component}.bin").unlink()
        with contextlib.redirect_stdout(io.StringIO()):
            result = audit.main(["--source-root", str(self.root), "--json", str(self.base / "broken.json"),
                                 "--markdown", str(self.base / "broken.md")])
        self.assertEqual(result, 1)
        report = json.loads((self.base / "broken.json").read_text())
        self.assertEqual(report["status"], "errors")
        self.assertEqual(report["direct_links"][0]["status"], "contradicted_or_dangling")


if __name__ == "__main__":
    unittest.main(verbosity=2)
