import os
import unittest
from unittest.mock import patch

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from vjoy_pad.app import DualStickApp


class AppTests(unittest.TestCase):
    def setUp(self):
        with patch("vjoy_pad.app.VJoyOutput", side_effect=RuntimeError("preview")):
            self.app = DualStickApp(windowed=True)

    def tearDown(self):
        pygame.quit()

    def test_switch_toggles_on_and_off(self):
        switch = self.app.switch_rects()[0]

        self.assertTrue(self.app.toggle_switch_at(switch.center))
        self.assertTrue(self.app.state.buttons[0])
        self.assertTrue(self.app.toggle_switch_at(switch.center))
        self.assertFalse(self.app.state.buttons[0])

    def test_position_outside_switches_is_not_consumed(self):
        self.assertFalse(self.app.toggle_switch_at((0, 0)))
        self.assertEqual(self.app.state.buttons, [False, False, False, False])


if __name__ == "__main__":
    unittest.main()
