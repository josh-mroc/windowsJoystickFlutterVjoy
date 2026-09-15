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
        self.assertEqual(self.app.state.buttons, [False, True, False, False, True])

    def test_first_switch_selects_button_one_or_two(self):
        switch = self.app.switch_rects()[0]

        self.assertTrue(self.app.toggle_switch_at(switch.center))
        self.assertEqual(self.app.state.buttons[:2], [True, False])
        self.assertTrue(self.app.toggle_switch_at(switch.center))
        self.assertEqual(self.app.state.buttons[:2], [False, True])
        self.assertEqual(self.app.state.buttons[2:], [False, False, True])

    def test_second_switch_selects_buttons_three_four_and_five(self):
        self.app.toggle_switch_at(self.app.switch_rects()[0].center)
        switch = self.app.switch_rects()[1]
        positions = ((switch.top + 1, 2), (switch.centery, 3), (switch.bottom - 1, 4))
        for position, button_index in positions:
            self.assertTrue(self.app.toggle_switch_at((switch.centerx, position)))
            self.assertEqual(
                self.app.state.buttons[2:],
                [i == button_index for i in range(2, 5)],
            )

    def test_second_switch_is_one_third_longer(self):
        first, second = self.app.switch_rects()

        self.assertEqual(second.height, first.height * 4 // 3)

    def test_second_switch_cannot_move_up_while_button_two_is_selected(self):
        switch = self.app.switch_rects()[1]

        self.assertTrue(
            self.app.toggle_switch_at((switch.centerx, switch.top + 1))
        )

        self.assertEqual(self.app.state.buttons[2:], [False, False, True])

    def test_selecting_button_two_moves_second_switch_to_five(self):
        first, second = self.app.switch_rects()
        self.app.toggle_switch_at(first.center)
        self.app.toggle_switch_at((second.centerx, second.top + 1))

        self.app.toggle_switch_at(first.center)

        self.assertEqual(self.app.state.buttons, [False, True, False, False, True])

    def test_position_outside_switches_is_not_consumed(self):
        self.assertFalse(self.app.toggle_switch_at((0, 0)))
        self.assertEqual(self.app.state.buttons, [False, True, False, False, True])


if __name__ == "__main__":
    unittest.main()
