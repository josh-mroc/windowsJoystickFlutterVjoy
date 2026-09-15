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

        self.assertTrue(self.app.toggle_switch_at((switch.centerx, switch.top + 1)))

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

    def test_two_paddle_input_is_unchecked_and_ry_is_horizontal_by_default(self):
        _, _, half_width, half_height = self.app.geometry()

        self.assertFalse(self.app.two_paddle_input)
        self.assertEqual(self.app.right_stick_half_sizes(), (half_height, half_width))

    def test_two_paddle_checkbox_is_in_upper_left_corner(self):
        checkbox = self.app.two_paddle_checkbox_rect()

        self.assertEqual(checkbox.topleft, (24, 28))

    def test_two_paddle_checkbox_restores_vertical_ry_stick(self):
        checkbox = self.app.two_paddle_checkbox_rect()

        self.assertTrue(self.app.toggle_two_paddle_at(checkbox.center))

        _, _, half_width, half_height = self.app.geometry()
        self.assertTrue(self.app.two_paddle_input)
        self.assertEqual(self.app.right_stick_half_sizes(), (half_width, half_height))

    def test_horizontal_right_stick_tracks_horizontal_movement_on_ry(self):
        _, right, _, half_height = self.app.geometry()
        self.app.claim("finger", right)

        self.app.move("finger", (right[0] + half_height, right[1] + 500))

        self.assertEqual(self.app.state.right_y, 1)

    def test_vertical_right_stick_tracks_vertical_movement(self):
        self.app.toggle_two_paddle_at(self.app.two_paddle_checkbox_rect().center)
        _, right, _, half_height = self.app.geometry()
        self.app.claim("finger", right)

        self.app.move("finger", (right[0] + 500, right[1] + half_height))

        self.assertEqual(self.app.state.right_y, 1)

    def test_changing_orientation_releases_right_contact_and_centers_axis(self):
        _, right, _, half_height = self.app.geometry()
        self.app.claim("finger", (right[0] + half_height, right[1]))
        self.assertEqual(self.app.state.right_y, 1)

        self.app.toggle_two_paddle_at(self.app.two_paddle_checkbox_rect().center)

        self.assertEqual(self.app.state.right_y, 0)
        self.assertNotIn("finger", self.app.contacts)

    def test_sticks_only_track_vertical_movement(self):
        left, _, _, half_height = self.app.geometry()
        self.app.claim("finger", left)

        self.app.move("finger", (left[0] + 500, left[1] + half_height))

        self.assertEqual(self.app.state.left_y, 1)

    def test_release_centers_vertical_stick(self):
        left, _, _, half_height = self.app.geometry()
        self.app.claim("finger", (left[0], left[1] + half_height))
        self.assertEqual(self.app.state.left_y, 1)

        self.app.release("finger")

        self.assertEqual(self.app.state.left_y, 0)


if __name__ == "__main__":
    unittest.main()
