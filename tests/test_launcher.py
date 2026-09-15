import sys
import unittest
from unittest.mock import patch

from vjoy_pad import launcher


class LauncherTests(unittest.TestCase):
    def test_install_message_uses_active_interpreter(self):
        message = launcher.pygame_install_message()

        self.assertIn(sys.executable, message)
        self.assertIn("pygame-ce", message)
        self.assertIn("requirements.txt", message)

    @patch("vjoy_pad.launcher.importlib.import_module")
    def test_missing_pygame_exits_with_install_guidance(self, import_module):
        import_module.side_effect = ModuleNotFoundError(
            "No module named 'pygame'", name="pygame"
        )

        with self.assertRaises(SystemExit) as raised:
            launcher.main()

        self.assertIn("pygame is not installed", str(raised.exception))

    @patch("vjoy_pad.launcher.importlib.import_module")
    def test_unrelated_missing_module_is_not_hidden(self, import_module):
        error = ModuleNotFoundError("No module named 'other'", name="other")
        import_module.side_effect = error

        with self.assertRaises(ModuleNotFoundError) as raised:
            launcher.main()

        self.assertIs(raised.exception, error)

    @patch("vjoy_pad.launcher.importlib.import_module")
    def test_loaded_application_is_started(self, import_module):
        app = import_module.return_value

        launcher.main()

        import_module.assert_called_once_with("vjoy_pad.app")
        app.main.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
