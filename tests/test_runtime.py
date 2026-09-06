"""Native OS lock contention and release; no reader or owner workspace."""
import tempfile
import subprocess
import sys
from pathlib import Path
import unittest

from nfcraft.errors import OpsError
from nfcraft.runtime import WorkspaceLock


class WorkspaceLockTests(unittest.TestCase):
    def test_failed_runtime_file_creation_does_not_hang_shutdown(self):
        with tempfile.TemporaryDirectory() as root:
            code = """
import sys
from unittest.mock import patch
from nfcraft.__main__ import main
with patch('nfcraft.__main__.os.open', side_effect=PermissionError('Synthetic runtime refusal')):
    raise SystemExit(main(['--mode','demo','--data-dir',sys.argv[1],'--port','0','--no-browser']))
"""
            result = subprocess.run([sys.executable, "-c", code, root], capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"STARTUP_IO", result.stderr)
            owner = WorkspaceLock(Path(root) / "demo")
            owner.close()

    def test_second_process_refused_without_removing_owner_runtime(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "demo"
            owner = WorkspaceLock(directory)
            runtime = directory / "agent-runtime.json"
            runtime.write_text('{"synthetic":true}', encoding="utf-8")
            try:
                result = subprocess.run([sys.executable, "run.py", "--data-dir", root,
                    "--no-browser", "--port", "0"], capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b"WORKSPACE_BUSY", result.stderr)
                self.assertEqual(runtime.read_text(), '{"synthetic":true}')
            finally:
                owner.close()

    def test_contention_is_bounded_and_owner_can_release(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / "workspace space 測試"
            owner = WorkspaceLock(directory)
            try:
                for _ in range(3):
                    with self.assertRaises(OpsError) as error:
                        WorkspaceLock(directory)
                    self.assertEqual(error.exception.code, "WORKSPACE_BUSY")
            finally:
                owner.close()
            replacement = WorkspaceLock(directory)
            replacement.close()
