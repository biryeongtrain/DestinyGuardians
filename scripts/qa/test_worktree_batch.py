"""Small stdlib-only fixtures. Never use or seed a product checkout."""

import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import worktree_batch as batch


class WorktreeBatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="worktree-batch-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.source = self.root / "source"
        self.source.mkdir()
        self.run_git("init", "-q")
        self.put("src/owned.txt", "committed\n")
        self.put("src/other.txt", "committed other\n")
        self.put("src/deleted.txt", "tracked but deleted in working tree\n")
        self.put("config/ignored-input.json", "tracked ignored input\n")
        self.put("config/ignored-deleted.json", "tracked ignored deletion\n")
        self.put(".gitignore", "config/*.json\n")
        self.run_git("add", ".")
        self.run_git("add", "-f", "config/ignored-input.json", "config/ignored-deleted.json")
        # Only seed commits in these tiny fixture repositories, never in the tool.
        self.run_git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                     "-c", "commit.gpgsign=false", "commit", "-qm", "fixture HEAD")
        self.put("src/owned.txt", "dirty inherited owned\n")
        self.put("src/other.txt", "dirty inherited other\n")
        (self.source / "src/deleted.txt").unlink()
        (self.source / "config/ignored-deleted.json").unlink()
        self.put("config/ignored-input.json", "dirty ignored tracked input\n")
        self.put("config/untracked-ignored.json", "ignored untracked working input\n")
        self.put("art/model.bbmodel", "untracked asset\n")
        self.put("docs/design/설계.md", "untracked design\n")
        self.put("scripts/tool.py", "print('input')\n")
        (self.source / "scripts/tool.py").chmod(0o755)
        self.put("build/generated.txt", "excluded\n")
        self.put("run/server/world.bin", "excluded\n")
        self.put(".gradle/cache.bin", "excluded\n")
        self.put("logs/current.log", "excluded\n")
        self.put("docs/qa/capture.zip", "excluded archive\n")
        self.put("docs/qa/result.json", "included report\n")
        self.put("gradle/wrapper/gradle-wrapper.jar", "included build input\n")
        self.mini = self.source / "libs/minigame-lib"
        self.gcb = self.root / "GCB-server"
        for dependency in (self.mini, self.gcb):
            self.write(dependency / "build.gradle", "// dependency\n")
            self.write(dependency / "src/input.txt", "dependency input\n")
            self.write(dependency / "build/shared.bin", "must not copy\n")
            self.write(dependency / ".gradle/shared.bin", "must not copy\n")
        self.worker = self.root / "worker"

    def run_git(self, *args):
        result = subprocess.run(["rtk", "proxy", "git", "-C", str(self.source), *args],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
                                env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
        return result.stdout.decode()

    @staticmethod
    def write(path, text):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def put(self, relative, text):
        self.write(self.source / relative, text)

    def feature(self, name="worker", destination=None, scope=None):
        return {"name": name, "destination": str(destination or self.worker),
                "owned_paths": scope or ["src/owned.txt", "src/new.txt"]}

    def create(self, features=None):
        return batch.create(self.source, {"features": features or [self.feature()]},
                            gcb_server=self.gcb)

    def test_dirty_snapshot_includes_ignored_inputs_and_keeps_deletions(self):
        index_before = (self.source / ".git/index").read_bytes()
        before = batch.scan(self.source)
        self.create()
        for rel in ("src/owned.txt", "src/other.txt", "config/ignored-input.json",
                    "config/untracked-ignored.json", "art/model.bbmodel", "docs/design/설계.md",
                    "gradle/wrapper/gradle-wrapper.jar", "docs/qa/result.json"):
            self.assertEqual((self.worker / rel).read_bytes(), (self.source / rel).read_bytes())
        for rel in ("src/deleted.txt", "config/ignored-deleted.json", "build", "run", ".gradle", "logs", "docs/qa/capture.zip"):
            self.assertFalse((self.worker / rel).exists(), rel)
        self.assertEqual(batch.inspect(self.worker)["changes"], [])
        self.assertEqual(batch.inspect(self.worker)["out_of_scope"], [])
        self.assertEqual(batch.scan(self.source), before)
        self.assertEqual((self.source / ".git/index").read_bytes(), index_before)
        self.assertTrue((self.worker / "scripts/tool.py").stat().st_mode & 0o111)

    def test_batch_dependencies_and_generated_outputs_are_independent(self):
        second = self.root / "second"
        result = self.create([self.feature(), self.feature("second", second, ["src/second.txt"])])
        self.assertEqual(result[0]["baseline_sha256"], result[1]["baseline_sha256"])
        for worker in (self.worker, second):
            for dep in batch.DEPENDENCIES:
                copied = worker / dep
                self.assertTrue(copied.is_dir())
                self.assertFalse(copied.is_symlink())
                self.assertFalse((copied / "build").exists())
                original = self.mini if dep.endswith("minigame-lib") else self.gcb
                self.assertNotEqual((copied / "src/input.txt").stat().st_ino,
                                    (original / "src/input.txt").stat().st_ino)
            self.write(worker / "libs/gcb-server/build/output.bin", worker.name)
        self.assertEqual((self.worker / "libs/gcb-server/build/output.bin").read_text(), "worker")
        self.assertEqual((second / "libs/gcb-server/build/output.bin").read_text(), "second")
        self.assertFalse((self.gcb / "build/output.bin").exists())
        self.assertEqual(batch.inspect(self.worker)["out_of_scope"], [])
        self.assertEqual(result[0]["gradle_env"]["ORG_GRADLE_PROJECT_gcb_server_dir"],
                         str(self.worker / "libs/gcb-server"))

    def test_export_only_owned_delta_preserves_inherited_dirt(self):
        self.create()
        before = batch.scan(self.source)
        self.write(self.worker / "src/owned.txt", "feature\n")
        self.write(self.worker / "src/new.txt", "new feature\n")
        destination = self.root / "export"
        plan = batch.export(self.worker, destination)
        self.assertEqual(plan["status"], "exported")
        self.assertEqual({p.relative_to(destination).as_posix() for p in destination.rglob("*") if p.is_file()},
                         {"manifest.json", "files/src/owned.txt", "files/src/new.txt"})
        self.assertEqual(plan["files"][0]["operation"], "add")
        owned = next(x for x in plan["files"] if x["path"] == "src/owned.txt")
        self.assertEqual(owned["before"]["sha256"], batch.read_file(self.source / "src/owned.txt")[0]["sha256"])
        self.assertEqual(batch.scan(self.source), before)

    def test_dry_run_creates_nothing(self):
        self.create()
        self.write(self.worker / "src/owned.txt", "feature\n")
        before = set(self.root.iterdir())
        self.assertEqual(batch.export(self.worker)["status"], "dry-run")
        self.assertEqual(set(self.root.iterdir()), before)

    def test_main_conflict_including_new_path_and_mode(self):
        for conflict in ("content", "new", "mode"):
            with self.subTest(conflict=conflict):
                worker = self.root / conflict
                batch.create(self.source, {"features": [self.feature(conflict, worker)]}, gcb_server=self.gcb)
                if conflict == "content":
                    self.put("src/owned.txt", "main changed\n")
                elif conflict == "new":
                    self.put("src/new.txt", "main added\n")
                else:
                    (self.source / "src/owned.txt").chmod(0o755)
                with self.assertRaisesRegex(batch.BatchError, "baseline conflict"):
                    batch.export(worker, self.root / (conflict + "-export"))
                self.assertFalse((self.root / (conflict + "-export")).exists())

    def test_unrelated_main_edit_is_preserved_and_does_not_block_export(self):
        self.create()
        self.put("src/other.txt", "new main edit\n")
        self.write(self.worker / "src/owned.txt", "feature\n")
        batch.export(self.worker, self.root / "export")
        self.assertEqual((self.source / "src/other.txt").read_text(), "new main edit\n")

    def test_out_of_scope_add_modify_delete_and_dependency_edit_rejected(self):
        self.create()
        for rel, operation in (("src/other.txt", "modify"), ("art/new.txt", "add"),
                               ("art/model.bbmodel", "delete"), ("libs/gcb-server/src/input.txt", "modify")):
            with self.subTest(rel=rel):
                path = self.worker / rel
                old = path.read_bytes() if path.exists() else None
                if operation == "delete":
                    path.unlink()
                else:
                    self.write(path, "unrelated change\n")
                self.assertIn(rel, batch.inspect(self.worker)["out_of_scope"])
                with self.assertRaisesRegex(batch.BatchError, "Out-of-scope"):
                    batch.export(self.worker, self.root / "export")
                if old is None:
                    path.unlink()
                else:
                    path.write_bytes(old)

    def test_delete_requires_opt_in_and_is_only_a_record(self):
        self.create()
        (self.worker / "src/owned.txt").unlink()
        with self.assertRaisesRegex(batch.BatchError, "allow-deletes"):
            batch.export(self.worker, self.root / "export")
        self.assertFalse((self.root / "export").exists())
        result = batch.export(self.worker, self.root / "export", allow_deletes=True)
        self.assertEqual(result["files"][0]["operation"], "delete")
        self.assertIsNone(result["files"][0]["after"])
        self.assertTrue((self.source / "src/owned.txt").exists())
        self.assertFalse((self.root / "export/files").exists())

    def test_scope_rejects_traversal_directories_globs_and_reserved_paths(self):
        for scope in ("../escape", "/absolute", "src/../escape", "src//owned.txt", "src/./owned.txt",
                      ".", "src", "src/*.txt", ".git/config", "build/input", "libs/gcb-server/src/input.txt",
                      "docs/qa/capture.zip", "a\\b", "C:/file", "a\nfile"):
            with self.subTest(scope=scope), self.assertRaises(batch.BatchError):
                self.create([self.feature(scope=[scope])])
            self.assertFalse(self.worker.exists())

    def test_duplicate_overlapping_scope_and_batch_destination_rejected_upfront(self):
        for features in (
            [self.feature(scope=["src/owned.txt", "src/owned.txt"])],
            [self.feature(scope=["future", "future/nested"])],
            [self.feature(), self.feature("second", self.root / "second")],
            [self.feature(), self.feature("second", self.worker / "nested", ["other"])],
        ):
            with self.subTest(features=features), self.assertRaises(batch.BatchError):
                self.create(features)
            self.assertFalse(self.worker.exists())

    def test_no_overwrite_existing_empty_or_populated_destination(self):
        self.worker.mkdir()
        with self.assertRaises(batch.BatchError):
            self.create()
        marker = self.worker / "marker"
        marker.write_text("preserve")
        with self.assertRaises(batch.BatchError):
            self.create()
        self.assertEqual(marker.read_text(), "preserve")

    def test_occupied_registration_refused_even_when_directory_missing(self):
        self.run_git("worktree", "add", "--detach", str(self.worker), "HEAD")
        shutil.rmtree(self.worker)  # Only this test's tiny disposable fixture.
        with self.assertRaisesRegex(batch.BatchError, "registered"):
            self.create()
        self.assertFalse(self.worker.exists())

    def test_destination_cannot_be_inside_source_or_dependency(self):
        for destination in (self.source / "new-worker", self.gcb / "new-worker"):
            with self.subTest(destination=destination), self.assertRaises(batch.BatchError):
                self.create([self.feature(destination=destination)])
            self.assertFalse(destination.exists())

    def test_dependency_required_no_partial_destination(self):
        with self.assertRaisesRegex(batch.BatchError, "Dependency"):
            batch.create(self.source, {"features": [self.feature()]})
        self.assertFalse(self.worker.exists())

    def test_source_file_and_directory_symlinks_fail_closed(self):
        for rel in ("src/link", "art/link"):
            with self.subTest(rel=rel):
                link = self.source / rel
                link.symlink_to(self.gcb / ("src/input.txt" if rel.startswith("src") else "src"))
                with self.assertRaisesRegex(batch.BatchError, "symlink|Symlink"):
                    self.create()
                self.assertFalse(self.worker.exists())
                link.unlink()

    def test_symlinked_dependency_and_destination_parent_rejected(self):
        link = self.root / "link"
        link.symlink_to(self.gcb, target_is_directory=True)
        with self.assertRaisesRegex(batch.BatchError, "Symlink"):
            batch.create(self.source, {"features": [self.feature()]}, gcb_server=link)
        with self.assertRaisesRegex(batch.BatchError, "Symlink"):
            self.create([self.feature(destination=link / "worker")])

    def test_worker_or_main_symlink_escape_rejected_before_export(self):
        self.create()
        owned = self.worker / "src/owned.txt"
        owned.unlink()
        owned.symlink_to(self.gcb / "src/input.txt")
        with self.assertRaises(batch.BatchError):
            batch.export(self.worker, self.root / "export")
        owned.unlink()
        owned.write_text("feature")
        main_owned = self.source / "src/owned.txt"
        main_owned.unlink()
        main_owned.symlink_to(self.gcb / "src/input.txt")
        with self.assertRaises(batch.BatchError):
            batch.export(self.worker, self.root / "export")
        self.assertFalse((self.root / "export").exists())

    def test_export_no_overwrite_or_inside_any_worktree_or_dependency(self):
        self.create()
        second = self.root / "second"
        batch.create(self.source, {"features": [self.feature("second", second)]}, gcb_server=self.gcb)
        self.write(self.worker / "src/owned.txt", "feature\n")
        existing = self.root / "existing"
        existing.mkdir()
        for output in (existing, self.worker / "export", self.source / "export",
                       second / "export", self.gcb / "export"):
            with self.subTest(output=output), self.assertRaises(batch.BatchError):
                batch.export(self.worker, output)
        self.assertEqual(list(existing.iterdir()), [])

    def test_midcopy_source_and_dependency_drift_leave_incomplete(self):
        original = batch.copy_file
        changed = False

        def drifting(source, target, expected):
            nonlocal changed
            original(source, target, expected)
            if not changed:
                changed = True
                self.put("config/late-ignored.json", "appeared during copy\n")

        with patch.object(batch, "copy_file", side_effect=drifting):
            with self.assertRaisesRegex(batch.BatchError, "Source drift"):
                self.create()
        self.assertEqual(json.loads(batch.state_path(self.worker).read_text())["status"], "incomplete")
        with self.assertRaisesRegex(batch.BatchError, "incomplete"):
            batch.inspect(self.worker)

    def test_midcopy_deletion_of_ignored_tracked_input_detected(self):
        original = batch.copy_file

        def drifting(source, target, expected):
            original(source, target, expected)
            if source == self.source / "config/ignored-input.json":
                source.unlink()

        with patch.object(batch, "copy_file", side_effect=drifting):
            with self.assertRaisesRegex(batch.BatchError, "Source drift"):
                self.create()

    def test_midcopy_dependency_drift_detected(self):
        original = batch.copy_file

        def drifting(source, target, expected):
            original(source, target, expected)
            if source == self.gcb / "src/input.txt":
                source.write_text("changed after copy\n")

        with patch.object(batch, "copy_file", side_effect=drifting):
            with self.assertRaisesRegex(batch.BatchError, "Dependency drift"):
                self.create()

    def test_copy_checks_hash_instead_of_trusting_size(self):
        source = self.source / "src/owned.txt"
        expected = batch.read_file(source)[0]
        source.write_bytes(b"x" * expected["size"])
        with self.assertRaisesRegex(batch.BatchError, "Source drift"):
            batch.copy_file(source, self.root / "copy", expected)

    def test_export_midcopy_drift_keeps_incomplete_bundle(self):
        self.create()
        self.write(self.worker / "src/owned.txt", "feature\n")
        original = batch.copy_file

        def drifting(source, target, expected):
            original(source, target, expected)
            self.put("src/owned.txt", "main drift during export\n")

        output = self.root / "export"
        with patch.object(batch, "copy_file", side_effect=drifting):
            with self.assertRaisesRegex(batch.BatchError, "drift"):
                batch.export(self.worker, output)
        self.assertTrue((output / "INCOMPLETE").exists())
        self.assertFalse((output / "manifest.json").exists())

    def test_qa_large_binary_filtered_without_large_fixtures(self):
        self.put("docs/qa/capture.unknown", "\0binary capture")
        self.put("docs/qa/large-notes.md", "long textual design notes")
        with patch.object(batch, "QA_BINARY_LIMIT", 8):
            files, _ = batch.scan(self.source)
            self.assertNotIn("docs/qa/capture.unknown", files)
            self.assertIn("docs/qa/large-notes.md", files)

    def test_small_qa_binary_captures_excluded_but_art_src_and_qa_text_preserved(self):
        for extension in batch.QA_CAPTURES:
            for prefix in ("docs/qa/history", "art/qa", "src/main/resources"):
                self.put(f"{prefix}/small{extension}", "tiny capture below 8 MiB")
        for extension in (".json", ".java", ".md", ".txt", ".csv", ".svg"):
            self.put(f"docs/qa/history/input{extension}", "historical JUnit working input")
        self.put("docs/qa/history/UPPER.PNG", "small uppercase capture")
        self.create()
        for extension in batch.QA_CAPTURES:
            self.assertFalse((self.worker / f"docs/qa/history/small{extension}").exists())
            for prefix in ("art/qa", "src/main/resources"):
                self.assertTrue((self.worker / f"{prefix}/small{extension}").is_file())
        self.assertFalse((self.worker / "docs/qa/history/UPPER.PNG").exists())
        for extension in (".json", ".java", ".md", ".txt", ".csv", ".svg"):
            self.assertTrue((self.worker / f"docs/qa/history/input{extension}").is_file())
        self.write(self.worker / "docs/qa/new-capture.png", "generated during feature work")
        self.assertEqual(batch.inspect(self.worker)["out_of_scope"], [])

    def test_checksum_corruption_blocks_inspection(self):
        self.create()
        path = batch.state_path(self.worker)
        metadata = json.loads(path.read_text())
        metadata["baseline"]["src/owned.txt"]["sha256"] = "bad"
        batch.write_json(path, metadata, "w")
        with self.assertRaisesRegex(batch.BatchError, "checksum"):
            batch.inspect(self.worker)

    def test_cli_create_inspect_and_dry_run(self):
        manifest = self.root / "features.json"
        batch.write_json(manifest, {"features": [self.feature()]})
        commands = (
            ["create", "--source", str(self.source), "--manifest", str(manifest), "--gcb-server", str(self.gcb)],
            ["inspect", "--worktree", str(self.worker)],
            ["export", "--worktree", str(self.worker), "--dry-run"],
        )
        for argv in commands:
            with self.subTest(argv=argv), contextlib.redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(batch.main(argv), 0)
                self.assertTrue(json.loads(stdout.getvalue()))


if __name__ == "__main__":
    unittest.main()
