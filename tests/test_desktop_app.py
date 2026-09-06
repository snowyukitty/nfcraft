"""Windowed startup errors must remain visible without leaking capabilities."""
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import patch

from nfcraft.desktop_app import main
from nfcraft.runtime import WorkspaceLock


class DesktopStartupTests(unittest.TestCase):
    def test_windowed_success_without_standard_streams(self):
        messages = []
        with patch('sys.stdout', None), patch('sys.stderr', None):
            with patch('nfcraft.desktop_app.run_workstation', return_value=0) as run:
                self.assertEqual(main([], show_error=messages.append), 0)
        self.assertEqual(run.call_args.args[0], ['--desktop', '--tray'])
        self.assertEqual(messages, [])

    def test_busy_workspace_is_visible_and_existing_lock_survives(self):
        with tempfile.TemporaryDirectory() as root:
            directory = Path(root) / 'demo'
            owner = WorkspaceLock(directory)
            messages = []
            try:
                self.assertEqual(main(['--data-dir', root, '--port', '0'], show_error=messages.append), 2)
                self.assertIn('WORKSPACE_BUSY', messages[0])
                self.assertFalse((directory / 'journal.sqlite3').exists())
            finally:
                owner.close()

    def test_busy_port_is_visible_and_releases_workspace(self):
        with tempfile.TemporaryDirectory() as root, socket.socket() as listener:
            listener.bind(('127.0.0.1', 0)); listener.listen()
            messages = []
            self.assertEqual(main(['--data-dir', root, '--port', str(listener.getsockname()[1])], show_error=messages.append), 2)
            self.assertIn('STARTUP_IO', messages[0])
            lock = WorkspaceLock(Path(root) / 'demo'); lock.close()

    def test_unexpected_exception_does_not_expose_raw_exception_contents(self):
        messages = []
        with patch('nfcraft.desktop_app.run_workstation', side_effect=RuntimeError('private operator capability')):
            self.assertEqual(main([], show_error=messages.append), 2)
        self.assertIn('RuntimeError', messages[0])
        self.assertNotIn('private operator capability', messages[0])
