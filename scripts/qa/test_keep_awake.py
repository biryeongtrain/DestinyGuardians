"""Offline lifecycle tests; no macOS settings, real child, or gameplay input."""
import contextlib
import io
import subprocess
import sys
import unittest
from unittest.mock import Mock, patch

import keep_awake


class KeepAwakeTests(unittest.TestCase):
    def run_main(self, args, awake=None, result=0, error=None):
        awake = awake or Mock()
        with patch.object(sys, "argv", ["keep_awake.py", *args]), \
             patch.object(keep_awake.subprocess, "Popen", return_value=awake) as start, \
             patch.object(keep_awake.subprocess, "run", return_value=Mock(returncode=result), side_effect=error) as run:
            value = keep_awake.main()
        return value, start, run, awake

    def test_success_owns_bounded_assertion_and_cleans_it(self):
        awake = Mock(); awake.poll.return_value = None
        value, start, run, awake = self.run_main(["--seconds", "20", "--", "rtk", "proxy", "true"], awake)
        self.assertEqual(value, 0)
        start.assert_called_once_with(["/usr/bin/caffeinate", "-dimsu", "-t", "20"], start_new_session=True)
        run.assert_called_once_with(["rtk", "proxy", "true"])
        awake.terminate.assert_called_once_with()
        awake.kill.assert_not_called()

    def test_command_failure_keeps_exit_code_and_cleanup(self):
        awake = Mock(); awake.poll.return_value = None
        value, _, _, _ = self.run_main(["--", "false"], awake, result=7)
        self.assertEqual(value, 7)
        awake.terminate.assert_called_once_with()

    def test_command_exception_still_cleans_own_child(self):
        awake = Mock(); awake.poll.return_value = None
        with self.assertRaises(FileNotFoundError):
            self.run_main(["--", "missing-command"], awake, error=FileNotFoundError())
        awake.terminate.assert_called_once_with()

    def test_timeout_escalates_only_own_caffeinate(self):
        awake = Mock(); awake.poll.return_value = None
        awake.wait.side_effect = [subprocess.TimeoutExpired("caffeinate", 3), 0]
        self.run_main(["--", "true"], awake)
        awake.kill.assert_called_once_with()
        self.assertEqual(awake.wait.call_count, 2)

    def test_already_expired_assertion_is_not_signalled(self):
        awake = Mock(); awake.poll.return_value = 0
        self.run_main(["--", "true"], awake)
        awake.terminate.assert_not_called()

    def test_invalid_bounds_and_missing_command_start_nothing(self):
        for args in (["--seconds", "0", "--", "true"], ["--seconds", "43201", "--", "true"], []):
            with self.subTest(args=args), patch.object(sys, "argv", ["keep_awake.py", *args]), \
                 patch.object(keep_awake.subprocess, "Popen") as start, contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    keep_awake.main()
                self.assertEqual(error.exception.code, 2)
                start.assert_not_called()


if __name__ == "__main__":
    unittest.main()
