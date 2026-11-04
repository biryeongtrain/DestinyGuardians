"""W111 copy/clone contract tests; stdlib and disposable files only.

Run: rtk proxy python3 -B -m unittest discover -s scripts/qa \
    -p test_worktree_clone.py -v
Missing _try_clone is a RED failure, never a skip or an injected implementation.
"""

import ctypes
import ctypes.util
import errno
import hashlib
import importlib.util
import os
from pathlib import Path
import platform
import shutil
import stat
import sys
import tempfile
import unittest
from unittest.mock import patch

import worktree_batch as batch


UNSUPPORTED = tuple(sorted({errno.EXDEV, errno.ENOTSUP, errno.EOPNOTSUPP, errno.ENOSYS}))
REAL_ERRORS = (errno.EEXIST, errno.EACCES, errno.ENOSPC, errno.EINVAL, errno.EPERM)
REJECTIONS = (batch.BatchError, OSError)


def record(path):
    """Compute expected content independently of the production hash helper."""
    data = path.read_bytes()
    return {"sha256": hashlib.sha256(data).hexdigest(), "size": len(data),
            "executable": bool(path.stat().st_mode & 0o111)}


def require_clone(test, module=batch):
    helper = getattr(module, "_try_clone", None)
    test.assertTrue(callable(helper), "RED: worktree_batch._try_clone is not implemented")
    return helper


class CopyFileCloneTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="w111-copy-contract-")
        self.addCleanup(temporary.cleanup)
        # Resolve macOS /var -> /private/var, so fixtures themselves are safe paths.
        self.root = Path(temporary.name).resolve()
        self.source = self.root / "source.bin"
        self.source.write_bytes(bytes(range(256)) * 17 + b"W111 source\n")
        self.source.chmod(0o600)
        self.target = self.root / "destination.bin"
        self.expected = record(self.source)

    def clone_patch(self, **kwargs):
        require_clone(self)
        return patch.object(batch, "_try_clone", **kwargs)

    def independent_clone(self, source, target):
        self.assertFalse(Path(target).exists(), "clone target must not be reserved beforehand")
        shutil.copyfile(source, target)
        return True

    def assert_copy(self, target=None, source_mode=0o600):
        target = target or self.target
        self.assertEqual(record(target), self.expected)
        self.assertFalse(target.is_symlink())
        self.assertNotEqual((target.stat().st_dev, target.stat().st_ino),
                            (self.source.stat().st_dev, self.source.stat().st_ino))
        self.assertEqual(stat.S_IMODE(target.stat().st_mode),
                         0o755 if self.expected["executable"] else 0o644)
        self.assertEqual(stat.S_IMODE(self.source.stat().st_mode), source_mode)

    def test_clone_success_checks_content_mode_and_independent_inode(self):
        for source_mode in (0o600, 0o700):
            with self.subTest(source_mode=oct(source_mode)):
                self.source.chmod(source_mode)
                self.expected = record(self.source)
                target = self.root / f"clone-{source_mode}"
                with self.clone_patch(side_effect=self.independent_clone) as clone:
                    batch.copy_file(self.source, target, self.expected)
                clone.assert_called_once_with(self.source, target)
                self.assert_copy(target, source_mode)
                target.write_bytes(b"worker edit")
                target.chmod(0o400)
                self.assertEqual(record(self.source), self.expected)
                self.assertEqual(stat.S_IMODE(self.source.stat().st_mode), source_mode)

    def test_false_clone_streams_and_preserves_executable_contract(self):
        for source_mode in (0o600, 0o700):
            with self.subTest(source_mode=oct(source_mode)):
                self.source.chmod(source_mode)
                self.expected = record(self.source)
                target = self.root / f"stream-{source_mode}"
                with self.clone_patch(return_value=False) as clone:
                    batch.copy_file(self.source, target, self.expected)
                clone.assert_called_once_with(self.source, target)
                self.assert_copy(target, source_mode)

    def test_empty_file_works_on_both_paths(self):
        self.source.write_bytes(b"")
        self.expected = record(self.source)
        for cloned in (False, True):
            with self.subTest(cloned=cloned):
                target = self.root / f"empty-{cloned}"
                effect = self.independent_clone if cloned else lambda source, target: False
                with self.clone_patch(side_effect=effect) as clone:
                    batch.copy_file(self.source, target, self.expected)
                clone.assert_called_once_with(self.source, target)
                self.assert_copy(target)

    def test_clone_creates_nested_destination(self):
        self.target = self.root / "new" / "nested" / "copy.bin"
        with self.clone_patch(side_effect=self.independent_clone) as clone:
            batch.copy_file(self.source, self.target, self.expected)
        clone.assert_called_once_with(self.source, self.target)
        self.assert_copy()

    def test_same_size_corrupted_clone_is_rejected_without_stream_retry(self):
        def corrupt(source, target):
            self.independent_clone(source, target)
            Path(target).write_bytes(b"x" * self.expected["size"])
            return True

        with self.clone_patch(side_effect=corrupt) as clone:
            with self.assertRaises(REJECTIONS):
                batch.copy_file(self.source, self.target, self.expected)
        clone.assert_called_once_with(self.source, self.target)
        self.assertEqual(record(self.source), self.expected)

    def test_truncated_clone_is_rejected(self):
        def truncate(source, target):
            self.independent_clone(source, target)
            Path(target).write_bytes(b"short")
            return True

        with self.clone_patch(side_effect=truncate):
            with self.assertRaises(REJECTIONS):
                batch.copy_file(self.source, self.target, self.expected)

    def test_source_content_drift_during_clone_rejected_even_if_target_matches(self):
        def drift(source, target):
            self.independent_clone(source, target)
            Path(source).write_bytes(b"x" * self.expected["size"])
            self.assertEqual(record(Path(target)), self.expected)
            return True

        with self.clone_patch(side_effect=drift) as clone:
            with self.assertRaises(REJECTIONS):
                batch.copy_file(self.source, self.target, self.expected)
        clone.assert_called_once_with(self.source, self.target)

    def test_source_replacement_during_clone_rejected_even_with_identical_bytes(self):
        def replace(source, target):
            self.independent_clone(source, target)
            before = Path(source).stat()
            replacement = self.root / "replacement"
            shutil.copyfile(source, replacement)
            replacement.chmod(stat.S_IMODE(before.st_mode))
            os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
            os.replace(replacement, source)
            self.assertEqual(record(Path(source)), self.expected)
            self.assertNotEqual(Path(source).stat().st_ino, before.st_ino)
            return True

        with self.clone_patch(side_effect=replace):
            with self.assertRaises(REJECTIONS):
                batch.copy_file(self.source, self.target, self.expected)

    def test_source_metadata_drift_during_clone_rejected(self):
        def touch(source, target):
            self.independent_clone(source, target)
            info = Path(source).stat()
            os.utime(source, ns=(info.st_atime_ns, info.st_mtime_ns + 2_000_000_000))
            self.assertEqual(record(Path(source)), self.expected)
            return True

        with self.clone_patch(side_effect=touch):
            with self.assertRaises(REJECTIONS):
                batch.copy_file(self.source, self.target, self.expected)

    def test_source_mode_drift_during_clone_rejected(self):
        def change_mode(source, target):
            self.independent_clone(source, target)
            Path(source).chmod(0o700)
            return True

        with self.clone_patch(side_effect=change_mode):
            with self.assertRaises(REJECTIONS):
                batch.copy_file(self.source, self.target, self.expected)

    def test_stale_expected_content_rejected_on_clone_and_stream_paths(self):
        self.source.write_bytes(b"x" * self.expected["size"])
        for cloned in (False, True):
            with self.subTest(cloned=cloned):
                target = self.root / f"stale-{cloned}"
                effect = self.independent_clone if cloned else lambda source, target: False
                with self.clone_patch(side_effect=effect):
                    with self.assertRaises(REJECTIONS):
                        batch.copy_file(self.source, target, self.expected)

    def test_stale_expected_executable_mode_rejected(self):
        self.source.chmod(0o700)
        with self.clone_patch(side_effect=self.independent_clone):
            with self.assertRaises(REJECTIONS):
                batch.copy_file(self.source, self.target, self.expected)
        self.assertEqual(stat.S_IMODE(self.source.stat().st_mode), 0o700)

    def test_hardlinked_clone_rejected_before_any_chmod(self):
        def hardlink(source, target):
            os.link(source, target)
            return True

        real_chmod = Path.chmod

        def guarded_chmod(path, mode, *args, **kwargs):
            if path == self.target:
                self.assertFalse(path.samefile(self.source), "chmod on a hardlink changes the source")
            return real_chmod(path, mode, *args, **kwargs)

        try:
            with self.clone_patch(side_effect=hardlink) as clone:
                with patch.object(Path, "chmod", guarded_chmod):
                    with self.assertRaises(REJECTIONS):
                        batch.copy_file(self.source, self.target, self.expected)
            clone.assert_called_once_with(self.source, self.target)
        finally:
            self.assertEqual(stat.S_IMODE(self.source.stat().st_mode), 0o600)
            self.assertEqual(record(self.source), self.expected)

    def test_clone_symlink_result_is_rejected_without_changing_source_mode(self):
        def symlink(source, target):
            Path(target).symlink_to(source)
            return True

        try:
            with self.clone_patch(side_effect=symlink):
                with self.assertRaises(REJECTIONS):
                    batch.copy_file(self.source, self.target, self.expected)
        finally:
            self.assertEqual(stat.S_IMODE(self.source.stat().st_mode), 0o600)
            self.assertEqual(record(self.source), self.expected)

    def test_real_clone_errors_are_propagated_without_silent_fallback(self):
        for code in REAL_ERRORS:
            with self.subTest(errno=code):
                target = self.root / f"error-{code}"
                with self.clone_patch(side_effect=OSError(code, os.strerror(code))) as clone:
                    with self.assertRaises(OSError) as raised:
                        batch.copy_file(self.source, target, self.expected)
                self.assertEqual(raised.exception.errno, code)
                clone.assert_called_once_with(self.source, target)
                self.assertEqual(record(self.source), self.expected)

    def test_existing_file_bytes_inode_and_mode_remain_intact(self):
        self.target.write_bytes(b"preexisting target")
        self.target.chmod(0o600)
        before = self.target.stat()
        with self.assertRaises(REJECTIONS):
            batch.copy_file(self.source, self.target, self.expected)
        self.assertEqual(self.target.read_bytes(), b"preexisting target")
        self.assertEqual(self.target.stat().st_ino, before.st_ino)
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o600)
        self.assertEqual(self.target.stat().st_ctime_ns, before.st_ctime_ns)
        self.assertEqual(record(self.source), self.expected)

    def test_preexisting_hardlink_remains_intact_without_chmod(self):
        os.link(self.source, self.target)
        before = self.source.stat()
        with self.assertRaises(REJECTIONS):
            batch.copy_file(self.source, self.target, self.expected)
        self.assertEqual(self.target.stat().st_ino, before.st_ino)
        self.assertEqual(stat.S_IMODE(self.source.stat().st_mode), 0o600)
        self.assertEqual(self.source.stat().st_ctime_ns, before.st_ctime_ns)
        self.assertEqual(record(self.source), self.expected)

    def test_target_created_during_clone_is_not_overwritten_or_chmodded(self):
        def occupied(source, target):
            Path(target).write_bytes(b"concurrent owner")
            Path(target).chmod(0o600)
            raise FileExistsError(errno.EEXIST, "fixture target appeared", str(target))

        with self.clone_patch(side_effect=occupied) as clone:
            with self.assertRaises(OSError) as raised:
                batch.copy_file(self.source, self.target, self.expected)
        self.assertEqual(raised.exception.errno, errno.EEXIST)
        clone.assert_called_once_with(self.source, self.target)
        self.assertEqual(self.target.read_bytes(), b"concurrent owner")
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o600)

    def test_source_leaf_symlink_is_rejected(self):
        link = self.root / "source-link"
        link.symlink_to(self.source)
        with self.assertRaises(REJECTIONS):
            batch.copy_file(link, self.target, self.expected)
        self.assertFalse(self.target.exists())
        self.assertEqual(record(self.source), self.expected)

    def test_destination_leaf_symlink_is_rejected_and_referent_preserved(self):
        self.target.symlink_to(self.source)
        with self.assertRaises(REJECTIONS):
            batch.copy_file(self.source, self.target, self.expected)
        self.assertTrue(self.target.is_symlink())
        self.assertEqual(stat.S_IMODE(self.source.stat().st_mode), 0o600)
        self.assertEqual(record(self.source), self.expected)

    def test_dangling_destination_symlink_is_rejected(self):
        missing = self.root / "must-not-create"
        self.target.symlink_to(missing)
        with self.assertRaises(REJECTIONS):
            batch.copy_file(self.source, self.target, self.expected)
        self.assertTrue(self.target.is_symlink())
        self.assertFalse(missing.exists())

    def test_symlinked_source_ancestor_is_rejected(self):
        link = self.root / "source-parent-link"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(REJECTIONS):
            batch.copy_file(link / self.source.name, self.target, self.expected)
        self.assertFalse(self.target.exists())

    def test_symlinked_destination_ancestor_is_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        link = self.root / "destination-parent-link"
        link.symlink_to(outside, target_is_directory=True)
        with self.assertRaises(REJECTIONS):
            batch.copy_file(self.source, link / "nested" / "target", self.expected)
        self.assertEqual(list(outside.iterdir()), [])

    def test_parent_traversal_is_rejected_for_either_path(self):
        for side in ("source", "target"):
            with self.subTest(side=side):
                source = self.root / "missing" / ".." / self.source.name if side == "source" else self.source
                target = self.root / "missing" / ".." / "target" if side == "target" else self.target
                with self.assertRaises(REJECTIONS):
                    batch.copy_file(source, target, self.expected)
                self.assertFalse((self.root / "missing").exists())
                self.assertFalse(self.target.exists())

    @unittest.skipUnless(sys.platform == "darwin", "native clonefile requires Darwin")
    def test_actual_native_clone_isolates_contents_and_mode_when_available(self):
        helper = require_clone(self)
        result = helper(self.source, self.target)
        self.assertIsInstance(result, bool)
        if not result:
            self.assertFalse(self.target.exists())
            self.skipTest("native clonefile unavailable on this filesystem")
        self.assertEqual(record(self.target), self.expected)
        self.assertNotEqual((self.source.stat().st_dev, self.source.stat().st_ino),
                            (self.target.stat().st_dev, self.target.stat().st_ino))
        self.target.write_bytes(b"native worker edit")
        self.target.chmod(0o700)
        self.assertEqual(record(self.source), self.expected)
        self.assertEqual(stat.S_IMODE(self.source.stat().st_mode), 0o600)
        self.source.write_bytes(b"native source edit")
        self.source.chmod(0o400)
        self.assertEqual(self.target.read_bytes(), b"native worker edit")
        self.assertEqual(stat.S_IMODE(self.target.stat().st_mode), 0o700)


class LibcClonefile:
    """ctypes function stand-in; permits standard argtypes/restype assignment."""
    def __init__(self, code=None):
        self.code = code
        self.calls = []

    def __call__(self, source, target, flags):
        self.calls.append((source, target, flags))
        ctypes.set_errno(self.code or 0)
        return -1 if self.code is not None else 0


class LibcShim:
    def __init__(self, function=None):
        if function is not None:
            self.clonefile = function


class TryCloneContractTests(unittest.TestCase):
    """Reload under standard-library seams; never patch private helper internals.

    The injected ctypes function only tests ABI dispatch/error classification.
    All successful copy_file emulators above use real independent copyfile bytes.
    """
    def invoke(self, *, code=None, symbol=True, system="darwin"):
        function = LibcClonefile(code)
        library = LibcShim(function if symbol else None)
        # Cover eager and lazy ctypes imports without relying on production names
        # for the library handle, function cache, flags, or errno collection.
        with patch.object(sys, "platform", system), \
                patch.object(platform, "system", return_value="Darwin" if system == "darwin" else "Linux"), \
                patch.object(ctypes.util, "find_library", return_value="libc-fixture"), \
                patch.object(ctypes, "CDLL", return_value=library), \
                patch.object(ctypes.cdll, "LoadLibrary", return_value=library):
            spec = importlib.util.spec_from_file_location("w111_clone_contract_module", batch.__file__)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            helper = require_clone(self, module)
            try:
                result = helper(Path("fixture-source"), Path("fixture-target"))
            finally:
                # Expose calls even when the helper correctly raises an OSError.
                self.libc_calls = function.calls
        return result

    def test_darwin_calls_clonefile_with_nofollow_flag_one(self):
        self.assertIs(self.invoke(), True)
        self.assertEqual(len(self.libc_calls), 1)
        source, target, flags = self.libc_calls[0]
        # ctypes paths may be bytes or c_char_p; both represent the same ABI.
        self.assertEqual(getattr(source, "value", source), b"fixture-source")
        self.assertEqual(getattr(target, "value", target), b"fixture-target")
        self.assertEqual(getattr(flags, "value", flags), 1)

    def test_non_darwin_returns_false_without_calling_clonefile(self):
        self.assertIs(self.invoke(system="linux"), False)
        self.assertEqual(self.libc_calls, [])

    def test_missing_clonefile_symbol_returns_false(self):
        self.assertIs(self.invoke(symbol=False), False)
        self.assertEqual(self.libc_calls, [])

    def test_only_unsupported_errno_values_return_false(self):
        for code in UNSUPPORTED:
            with self.subTest(errno=code):
                self.assertIs(self.invoke(code=code), False)
                self.assertEqual(len(self.libc_calls), 1)

    def test_real_errno_values_raise_instead_of_returning_false(self):
        for code in REAL_ERRORS:
            with self.subTest(errno=code):
                with self.assertRaises(OSError) as raised:
                    self.invoke(code=code)
                self.assertEqual(raised.exception.errno, code)
                self.assertEqual(len(self.libc_calls), 1)

    def test_other_unlisted_errno_is_not_silently_treated_as_unsupported(self):
        with self.assertRaises(OSError) as raised:
            self.invoke(code=errno.EIO)
        self.assertEqual(raised.exception.errno, errno.EIO)
        self.assertEqual(len(self.libc_calls), 1)


if __name__ == "__main__":
    unittest.main()
