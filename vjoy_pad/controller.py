"""Input normalization and vJoy output support."""

from __future__ import annotations

from dataclasses import dataclass, field
import math

VJOY_MIN = 1
VJOY_MAX = 0x8000
VJOY_CENTER = (VJOY_MIN + VJOY_MAX) // 2


def stick_geometry(
    width: int, height: int
) -> tuple[tuple[float, float], tuple[float, float], float]:
    """Return bottom-corner geometry sized from the shorter screen dimension."""
    radius = max(1.0, min(width, height) * 0.33 / 2)
    edge_margin = min(width, height) * 0.025
    y = height - radius - edge_margin
    return (radius + edge_margin, y), (width - radius - edge_margin, y), radius


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def stick_from_pointer(
    pointer: tuple[float, float], center: tuple[float, float], radius: float,
    deadzone: float = 0.08,
) -> tuple[float, float]:
    """Return an x/y pair in [-1, 1], constrained to a circular gate."""
    if radius <= 0:
        return 0.0, 0.0
    x = (pointer[0] - center[0]) / radius
    y = (pointer[1] - center[1]) / radius
    magnitude = math.hypot(x, y)
    if magnitude > 1:
        x, y = x / magnitude, y / magnitude
        magnitude = 1
    if magnitude <= deadzone:
        return 0.0, 0.0
    scaled = (magnitude - deadzone) / (1 - deadzone)
    return x * scaled / magnitude, y * scaled / magnitude


def to_vjoy_axis(value: float) -> int:
    """Convert a normalized axis to vJoy's integer axis range."""
    value = clamp(value, -1.0, 1.0)
    return round(VJOY_MIN + (value + 1.0) * (VJOY_MAX - VJOY_MIN) / 2)


@dataclass
class PadState:
    left_x: float = 0.0
    left_y: float = 0.0
    right_x: float = 0.0
    right_y: float = 0.0
    buttons: list[bool] = field(default_factory=lambda: [False] * 4)


class VJoyOutput:
    """Small adapter that keeps the UI independent from pyvjoy."""

    def __init__(self, device_id: int = 1) -> None:
        import pyvjoy  # Windows-only dependency; imported only when connecting.

        self._pyvjoy = pyvjoy
        self._device = pyvjoy.VJoyDevice(device_id)

    def update(self, state: PadState) -> None:
        axes = self._pyvjoy
        self._device.set_axis(axes.HID_USAGE_X, to_vjoy_axis(state.left_x))
        self._device.set_axis(axes.HID_USAGE_Y, to_vjoy_axis(state.left_y))
        self._device.set_axis(axes.HID_USAGE_RX, to_vjoy_axis(state.right_x))
        self._device.set_axis(axes.HID_USAGE_RY, to_vjoy_axis(state.right_y))
        for number, pressed in enumerate(state.buttons, start=1):
            self._device.set_button(number, pressed)

    def reset(self) -> None:
        self.update(PadState())
