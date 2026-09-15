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
    def test_sticks_are_tall_narrow_and_sized_from_shorter_dimension(self):
        left, right, half_width, half_height = stick_geometry(1920, 1080)

        self.assertEqual(half_width * 2, 1080 * 0.14)
        self.assertEqual(half_height * 2, 1080 * 0.33)
        self.assertEqual(
            left,
            (
                half_width + 1080 * 0.025,
                1080 - half_height - 1080 * 0.025,
            ),
        )
        self.assertEqual(right, (1920 - half_width - 1080 * 0.025, left[1]))

    def test_portrait_stick_size_uses_screen_width(self):
        _, _, half_width, half_height = stick_geometry(600, 1000)

        self.assertEqual(half_width * 2, 600 * 0.14)
        self.assertEqual(half_height * 2, 600 * 0.33)

    def test_axis_endpoints_and_center(self):
        self.assertEqual(to_vjoy_axis(-1), VJOY_MIN)
        self.assertEqual(to_vjoy_axis(0), VJOY_CENTER)
        self.assertEqual(to_vjoy_axis(1), VJOY_MAX)

    def test_axis_clamps(self):
        self.assertEqual(to_vjoy_axis(-4), VJOY_MIN)
        self.assertEqual(to_vjoy_axis(4), VJOY_MAX)

    def test_pointer_deadzone(self):
        self.assertEqual(stick_from_pointer((100, 101), (100, 100), 100), 0)

    def test_pointer_is_constrained_to_vertical_axis(self):
        self.assertEqual(stick_from_pointer((400, 200), (100, 100), 100), 1)
        self.assertEqual(stick_from_pointer((-200, 0), (100, 100), 100), -1)

    def test_horizontal_pointer_movement_is_ignored(self):
        self.assertEqual(stick_from_pointer((400, 100), (100, 100), 100), 0)

    def test_pad_state_starts_with_five_released_buttons(self):
        first = PadState()
        second = PadState()

        self.assertEqual(first.buttons, [False, False, False, False, False])
        first.buttons[0] = True
        self.assertEqual(second.buttons, [False, False, False, False, False])

    def test_vjoy_output_updates_x_y_and_ry_axes_and_all_five_buttons(self):
        output = VJoyOutput.__new__(VJoyOutput)
        output._device = Mock()
        output._pyvjoy = SimpleNamespace(
            HID_USAGE_X=1, HID_USAGE_Y=2, HID_USAGE_RX=3, HID_USAGE_RY=4
        )

        output.update(
            PadState(
                x=1,
                left_y=-1,
                right_y=1,
                buttons=[True, False, True, False, True],
            )
        )

        self.assertEqual(
            output._device.set_axis.call_args_list,
            [
                unittest.mock.call(1, VJOY_MAX),
                unittest.mock.call(2, VJOY_MIN),
                unittest.mock.call(4, VJOY_MAX),
            ],
        )

        self.assertEqual(
            output._device.set_button.call_args_list,
            [
                unittest.mock.call(1, True),
                unittest.mock.call(2, False),
                unittest.mock.call(3, True),
                unittest.mock.call(4, False),
                unittest.mock.call(5, True),
            ],
        )

        output._device.reset_mock()
        output.update(PadState())
        self.assertEqual(
            output._device.set_axis.call_args_list[0],
            unittest.mock.call(1, VJOY_MIN),
        )


if __name__ == "__main__":
    unittest.main()
