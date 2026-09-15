import math
import unittest

from vjoy_pad.controller import (
    VJOY_CENTER,
    VJOY_MAX,
    VJOY_MIN,
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


if __name__ == "__main__":
    unittest.main()
