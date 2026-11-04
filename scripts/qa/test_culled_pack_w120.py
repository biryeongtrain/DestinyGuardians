"""Audit-transport positive/negative controls, not native/render evidence."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

SPEC = importlib.util.spec_from_file_location("audit", Path(__file__).with_name("audit_culled_pack_w120.py"))
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)


class TransportAudit(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name); self.res = self.root / "src/main/resources"
        self.export = self.root / "build/qa/w119-culling"; self.export.mkdir(parents=True)
        self.old = self.root / "old.zip"; self.new = self.root / "new.zip"
        self.old_files = {}; self.new_files = {}; rules = []; audit = {}
        for weapon, family, parts in (("blast_furnace", "pulse_rifle", ("body", "magazine")),
                                       ("hammerhead", "machine_gun", ("body", "magazine", "cover"))):
            original_assembly = []; new_assembly = []
            texture = {"0": f"destiny:item/weapon/w115/{weapon}"}
            for part in parts:
                # Minimal JSON for transport/assembly invariants; no PNG opacity proof.
                visible = {"name": f"{part}-outer", "faces": {"north": {}}}
                inner = {"name": f"{part}-inner", "faces": {"north": {}}}
                before = dict(textures=texture, elements=[visible, inner])
                after = dict(textures=texture, elements=[visible])
                self.row(f"assets/destiny/models/weapon_reload_w114_{weapon}/{weapon}_{part}.json", before, after, rules, audit)
                original_assembly.extend(before["elements"]); new_assembly.extend(after["elements"])
            self.row(f"assets/destiny/models/weapon/{family}/{weapon}.json",
                     dict(textures=texture, elements=original_assembly),
                     dict(textures=texture, elements=new_assembly), rules, audit)
            atlas = f"assets/destiny/textures/item/weapon/w115/{weapon}.png"
            self.old_files[atlas] = self.new_files[atlas] = b"same-static-pixel-fixture"
            self.write(self.res / atlas, self.old_files[atlas])
        self.old_files["assets/destiny/sounds.json"] = self.new_files["assets/destiny/sounds.json"] = b"unchanged"
        self.write(self.res / "weapon_surface_w115/manifest.json", json.dumps(dict(targets=rules)).encode())
        self.write(self.export / "audit.json", json.dumps(audit).encode())
        self.zip(self.old, self.old_files); self.zip(self.new, self.new_files)
        self.write(self.root / "docs/qa/2026-10-25/w118/runtime-artifact-provenance.json",
                   json.dumps([dict(path=str(self.old), sha256=M.sha(self.old.read_bytes()))]).encode())

    def row(self, path, before, after, rules, audit):
        raw = (json.dumps(before, indent=2) + "\n").encode(); optimized = json.dumps(after, separators=(",", ":")).encode()
        replacement = "assets/destiny/models/weapon_surface_w115/" + Path(path).name
        self.old_files[path] = raw; self.new_files[path] = optimized
        self.old_files[replacement] = self.new_files[replacement] = raw
        self.write(self.res / replacement, raw); self.write(self.export / Path(path).name, optimized)
        rules.append(dict(path=path, replacement=replacement, replacementSha256=M.sha(raw)))
        audit[path] = dict(inputSha256=M.sha(raw), outputSha256=M.sha(optimized))

    @staticmethod
    def write(path, raw):
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)

    @staticmethod
    def zip(path, files):
        with zipfile.ZipFile(path, "w") as z:
            for name, raw in files.items(): z.writestr(name, raw)

    def run_audit(self):
        with patch.object(M, "ROOT", self.root), patch.object(M, "RES", self.res), patch.object(M, "EXPORT", self.export), patch.object(M, "BASE", self.old):
            return M.audit(old=self.old, new=self.new)

    def test_exact_seven_changes_and_separate_part_assembly_pass(self):
        result = self.run_audit()
        self.assertEqual(len(result["changed"]), 7)
        self.assertTrue(result["samePartFullAssemblyVerified"])
        self.assertFalse(result["framebuffer"]); self.assertFalse(result["fpsMeasurement"])

    def test_old_pack_cannot_be_counted_as_new_output(self):
        self.zip(self.new, self.old_files)
        with self.assertRaises(AssertionError): self.run_audit()

    def test_foreign_texture_or_sound_change_rejected(self):
        for path in ("assets/destiny/sounds.json", "assets/destiny/textures/item/weapon/w115/blast_furnace.png"):
            with self.subTest(path=path):
                changed = copy.copy(self.new_files); changed[path] = b"foreign-change"; self.zip(self.new, changed)
                with self.assertRaises(AssertionError): self.run_audit()

    def test_added_and_removed_destiny_paths_rejected(self):
        for operation in ("add", "remove"):
            with self.subTest(operation=operation):
                changed = copy.copy(self.new_files)
                if operation == "add": changed["assets/destiny/foreign.json"] = b"{}"
                else: changed.pop("assets/destiny/sounds.json")
                self.zip(self.new, changed)
                with self.assertRaises(AssertionError): self.run_audit()

    def test_duplicate_zip_entries_rejected(self):
        with zipfile.ZipFile(self.new, "a") as z:
            with self.assertWarns(UserWarning): z.writestr("assets/destiny/sounds.json", b"unchanged")
        with self.assertRaises(AssertionError): self.run_audit()

    def test_stale_java_export_or_authored_input_rejected(self):
        path = next(self.export.glob("blast_furnace_body.json")); path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaises(AssertionError): self.run_audit()

    def test_wrong_emitted_bytes_rejected_even_if_inside_allowed_scope(self):
        path = "assets/destiny/models/weapon/pulse_rifle/blast_furnace.json"
        self.new_files[path] += b"\n"; self.zip(self.new, self.new_files)
        with self.assertRaises(AssertionError): self.run_audit()


if __name__ == "__main__":
    unittest.main(verbosity=2)
