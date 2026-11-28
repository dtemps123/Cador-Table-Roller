"""Test launcher command construction without a display or dice backend."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import eccentric_east_launcher as launcher

class LauncherTests(unittest.TestCase):
    def test_workshops(self):
        for key, name, description, script, args in launcher.WORKSHOPS:
            command = launcher.launch_command(script, args)
            self.assertEqual(command[0], sys.executable)
            self.assertEqual(Path(command[1]), launcher.HERE / script)
            self.assertTrue(Path(command[1]).is_file())
            self.assertEqual(command[2:], list(args))
    def test_shared_editor(self):
        entries = [w for w in launcher.WORKSHOPS if w[0] == 'record']
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0][3], entries[1][3])
        self.assertEqual({w[4] for w in entries}, {('--kind', 'Location'), ('--kind', 'Plot')})
    def test_missing_script(self):
        with self.assertRaises(FileNotFoundError):
            launcher.launch_command('missing-workshop.py')

if __name__ == '__main__':
    unittest.main()
