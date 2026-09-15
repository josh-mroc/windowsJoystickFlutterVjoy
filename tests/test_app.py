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

    def test_button_two_is_selected_by_default(self):
        self.assertEqual(self.app.state.buttons, [False, True, False, False])

    def test_first_switch_selects_button_one_or_two(self):
        switch = self.app.switch_rects()[0]

        self.assertTrue(self.app.toggle_switch_at(switch.center))
        self.assertEqual(self.app.state.buttons[:2], [True, False])
        self.assertTrue(self.app.toggle_switch_at(switch.center))
        self.assertEqual(self.app.state.buttons[:2], [False, True])

    def test_other_switches_toggle_buttons_three_and_four(self):
        for switch_index, button_index in ((1, 2), (2, 3)):
            switch = self.app.switch_rects()[switch_index]
            self.assertTrue(self.app.toggle_switch_at(switch.center))
            self.assertTrue(self.app.state.buttons[button_index])
            self.assertTrue(self.app.toggle_switch_at(switch.center))
            self.assertFalse(self.app.state.buttons[button_index])

    def test_position_outside_switches_is_not_consumed(self):
        self.assertFalse(self.app.toggle_switch_at((0, 0)))
        self.assertEqual(self.app.state.buttons, [False, True, False, False])


if __name__ == "__main__":
    unittest.main()
