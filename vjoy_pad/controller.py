"""Input normalization and vJoy output support."""

from __future__ import annotations

from dataclasses import dataclass, field

VJOY_MIN = 1
VJOY_MAX = 0x8000
VJOY_CENTER = (VJOY_MIN + VJOY_MAX) // 2


def stick_geometry(
    width: int, height: int
) -> tuple[tuple[float, float], tuple[float, float], float, float]:
    """Return centers and half-sizes for two vertical, single-axis sticks."""
    short_side = min(width, height)
    half_width = max(1.0, short_side * 0.14 / 2)
    half_height = max(1.0, short_side * 0.33 / 2)
    edge_margin = min(width, height) * 0.025
    y = height - half_height - edge_margin
    return (
        (half_width + edge_margin, y),
        (width - half_width - edge_margin, y),
        half_width,
        half_height,
    )


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def stick_from_pointer(
    pointer: tuple[float, float],
    center: tuple[float, float],
    radius: float,
    deadzone: float = 0.08,
) -> float:
    """Return vertical input in [-1, 1], ignoring horizontal movement."""
    if radius <= 0:
        return 0.0
    y = clamp((pointer[1] - center[1]) / radius, -1.0, 1.0)
    magnitude = abs(y)
    if magnitude <= deadzone:
        return 0.0
    scaled = (magnitude - deadzone) / (1 - deadzone)
    return scaled if y > 0 else -scaled


def to_vjoy_axis(value: float) -> int:
    """Convert a normalized axis to vJoy's integer axis range."""
    value = clamp(value, -1.0, 1.0)
    return round(VJOY_MIN + (value + 1.0) * (VJOY_MAX - VJOY_MIN) / 2)


@dataclass
class PadState:
    left_y: float = 0.0
    right_y: float = 0.0
    buttons: list[bool] = field(default_factory=lambda: [False] * 5)


class VJoyOutput:
    """Small adapter that keeps the UI independent from pyvjoy."""

    def __init__(self, device_id: int = 1) -> None:
        import pyvjoy  # Windows-only dependency; imported only when connecting.

        self._pyvjoy = pyvjoy
        self._device = pyvjoy.VJoyDevice(device_id)

    def update(self, state: PadState) -> None:
        axes = self._pyvjoy
        self._device.set_axis(axes.HID_USAGE_Y, to_vjoy_axis(state.left_y))
        self._device.set_axis(axes.HID_USAGE_RY, to_vjoy_axis(state.right_y))
        for number, pressed in enumerate(state.buttons, start=1):
            self._device.set_button(number, pressed)

    def reset(self) -> None:
        self.update(PadState())
