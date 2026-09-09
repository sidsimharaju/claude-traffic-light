"""
Unit tests for claude_traffic_light.hook.

Run with:
    python3 -m pytest tests/ -v
"""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from claude_traffic_light import hook as status_hook  # noqa: E402


class StatusHookTests(unittest.TestCase):
    def setUp(self):
        # Redirect the module's STATE_DIR into a throwaway temp-like path
        # under the test's own tmp dir so we never touch the real
        # ~/.claude-traffic-light directory.
        import tempfile

        self._tmpdir = tempfile.TemporaryDirectory()
        self._orig_state_dir = status_hook.STATE_DIR
        status_hook.STATE_DIR = Path(self._tmpdir.name) / "sessions"

    def tearDown(self):
        status_hook.STATE_DIR = self._orig_state_dir
        self._tmpdir.cleanup()

    def run_hook(self, state, payload):
        stdin = io.StringIO(json.dumps(payload))
        with mock.patch.object(sys, "stdin", stdin):
            return status_hook.main([state])

    def test_running_writes_state_file(self):
        rc = self.run_hook("running", {"session_id": "abc123", "cwd": "/tmp/project"})
        self.assertEqual(rc, 0)
        path = status_hook.STATE_DIR / "abc123.json"
        self.assertTrue(path.exists())
        data = json.loads(path.read_text())
        self.assertEqual(data["state"], "running")
        self.assertEqual(data["cwd"], "/tmp/project")
        self.assertIn("updated_at", data)

    def test_needs_action_overwrites_running(self):
        self.run_hook("running", {"session_id": "abc123", "cwd": "/tmp/project"})
        self.run_hook(
            "needs_action",
            {"session_id": "abc123", "cwd": "/tmp/project", "message": "Approve Bash?"},
        )
        path = status_hook.STATE_DIR / "abc123.json"
        data = json.loads(path.read_text())
        self.assertEqual(data["state"], "needs_action")
        self.assertEqual(data["detail"], "Approve Bash?")

    def test_ended_removes_file(self):
        self.run_hook("running", {"session_id": "abc123", "cwd": "/tmp/project"})
        path = status_hook.STATE_DIR / "abc123.json"
        self.assertTrue(path.exists())

        self.run_hook("ended", {"session_id": "abc123"})
        self.assertFalse(path.exists())

    def test_missing_session_id_falls_back(self):
        rc = self.run_hook("idle", {"cwd": "/tmp/no-id"})
        self.assertEqual(rc, 0)
        path = status_hook.STATE_DIR / "unknown-session.json"
        self.assertTrue(path.exists())

    def test_unrecognized_state_is_a_no_op(self):
        rc = self.run_hook("bogus-state", {"session_id": "abc123"})
        self.assertEqual(rc, 0)
        self.assertFalse(status_hook.STATE_DIR.exists())

    def test_malformed_stdin_does_not_crash(self):
        with mock.patch.object(sys, "stdin", io.StringIO("not json")):
            rc = status_hook.main(["running"])
        self.assertEqual(rc, 0)
        path = status_hook.STATE_DIR / "unknown-session.json"
        self.assertTrue(path.exists())


if __name__ == "__main__":
    unittest.main()
