import math
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from vjoy_pad.controller import (
    PadState,
    VJOY_CENTER,
    VJOY_MAX,
    VJOY_MIN,
    VJoyOutput,
    stick_from_pointer,
    stick_geometry,
    to_vjoy_axis,
)


class ControllerTests(unittest.TestCase):
    def test_stick_diameter_is_33_percent_of_shorter_screen_dimension(self):
        left, right, radius = stick_geometry(1920, 1080)

        self.assertEqual(radius * 2, 1080 * 0.33)
        self.assertEqual(
            left, (radius + 1080 * 0.025, 1080 - radius - 1080 * 0.025)
        )
        self.assertEqual(right, (1920 - radius - 1080 * 0.025, left[1]))

    def test_portrait_stick_size_uses_screen_width(self):
        _, _, radius = stick_geometry(600, 1000)

        self.assertEqual(radius * 2, 600 * 0.33)

    def test_axis_endpoints_and_center(self):
        self.assertEqual(to_vjoy_axis(-1), VJOY_MIN)
        self.assertEqual(to_vjoy_axis(0), VJOY_CENTER)
        self.assertEqual(to_vjoy_axis(1), VJOY_MAX)

    def test_axis_clamps(self):
        self.assertEqual(to_vjoy_axis(-4), VJOY_MIN)
        self.assertEqual(to_vjoy_axis(4), VJOY_MAX)

    def test_pointer_deadzone(self):
        self.assertEqual(stick_from_pointer((101, 100), (100, 100), 100), (0, 0))

    def test_pointer_is_constrained_to_circle(self):
        x, y = stick_from_pointer((200, 200), (100, 100), 100)
        self.assertAlmostEqual(math.hypot(x, y), 1)
        self.assertAlmostEqual(x, y)

    def test_pad_state_starts_with_four_released_buttons(self):
        first = PadState()
        second = PadState()

        self.assertEqual(first.buttons, [False, False, False, False])
        first.buttons[0] = True
        self.assertEqual(second.buttons, [False, False, False, False])

    def test_vjoy_output_updates_all_four_buttons(self):
        output = VJoyOutput.__new__(VJoyOutput)
        output._device = Mock()
        output._pyvjoy = SimpleNamespace(
            HID_USAGE_X=1, HID_USAGE_Y=2, HID_USAGE_RX=3, HID_USAGE_RY=4
        )

        output.update(PadState(buttons=[True, False, True, False]))

        self.assertEqual(
            output._device.set_button.call_args_list,
            [
                unittest.mock.call(1, True),
                unittest.mock.call(2, False),
                unittest.mock.call(3, True),
                unittest.mock.call(4, False),
            ],
        )


if __name__ == "__main__":
    unittest.main()
