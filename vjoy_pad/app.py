"""Pygame user interface for the virtual gamepad."""

from __future__ import annotations

import argparse
import ctypes
from ctypes import wintypes
import sys
from typing import Hashable

import pygame

from .controller import PadState, VJoyOutput, stick_from_pointer, stick_geometry

BG = (13, 18, 28)
RING = (64, 79, 103)
ACCENT = (66, 211, 173)
TEXT = (235, 241, 248)
MUTED = (148, 163, 184)
RED = (239, 68, 68)
GREEN = (34, 197, 94)
ORANGE = (249, 115, 22)

# Labels are ordered by their corresponding vJoy button number.
SWITCH_LABELS = (
    ("ARMED", RED),
    ("Disarmed", MUTED),
    ("Auto", GREEN),
    ("Manual", ORANGE),
    ("HOLD", MUTED),
)


class DualStickApp:
    def __init__(self, device_id: int = 1, windowed: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption("vJoy Touchpad")
        flags = pygame.RESIZABLE if windowed else pygame.NOFRAME
        display = pygame.display.Info()
        size = (1100, 650) if windowed else (display.current_w, display.current_h)
        self.screen = pygame.display.set_mode(size, flags)
        self._enable_transparent_overlay()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 24)
        self.small_font = pygame.font.SysFont("Segoe UI", 17)
        self.state = PadState()
        self.two_paddle_input = False
        # The first switch is a two-position selector: down selects button 2.
        self.state.buttons[1] = True
        # Button 2 starts selected, so the three-position selector starts at 5.
        self.state.buttons[4] = True
        self.contacts: dict[Hashable, str] = {}
        self.output = None
        self.status = "Preview mode"
        try:
            self.output = VJoyOutput(device_id)
            # vJoy initializes its axes at center. Publish our initial state
            # immediately so the unidirectional X slider appears at its
            # minimum (far-left) position as soon as the device connects.
            self.output.update(self.state)
            self.status = f"Connected to vJoy device {device_id}"
        except Exception as exc:
            self.output = None
            self.status = f"Preview mode — vJoy unavailable: {exc}"

    def _enable_transparent_overlay(self) -> None:
        """Make the color-keyed window transparent and topmost on Windows."""
        if sys.platform != "win32":
            return

        hwnd = pygame.display.get_wm_info()["window"]
        user32 = ctypes.windll.user32
        get_window_long = user32.GetWindowLongW
        set_window_long = user32.SetWindowLongW
        get_window_long.argtypes = [wintypes.HWND, ctypes.c_int]
        get_window_long.restype = ctypes.c_long
        set_window_long.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
        set_window_long.restype = ctypes.c_long
        extended_style = get_window_long(hwnd, -20)  # GWL_EXSTYLE
        set_window_long(hwnd, -20, extended_style | 0x00080000)  # WS_EX_LAYERED
        color_key = BG[0] | (BG[1] << 8) | (BG[2] << 16)
        user32.SetLayeredWindowAttributes.argtypes = [
            wintypes.HWND,
            wintypes.COLORREF,
            wintypes.BYTE,
            wintypes.DWORD,
        ]
        user32.SetLayeredWindowAttributes(hwnd, color_key, 0, 0x00000001)
        user32.SetWindowPos.argtypes = [
            wintypes.HWND,
            wintypes.HWND,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_int,
            wintypes.UINT,
        ]
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)

    def geometry(self):
        width, height = self.screen.get_size()
        left, right, half_width, half_height = stick_geometry(width, height)
        if not self.two_paddle_input:
            # Preserve the right edge margin after swapping the RY dimensions.
            right = (right[0] - (half_height - half_width), right[1])
        return left, right, half_width, half_height

    def switch_rects(self) -> list[pygame.Rect]:
        """Return the centered two- and three-position switch bounds."""
        width, height = self.screen.get_size()
        switch_width = max(42, min(58, width // 18))
        switch_height = max(76, min(96, height // 7))
        gap = max(16, switch_width // 2)
        row_width = switch_width * 2 + gap
        left = (width - row_width) // 2
        top = 140
        return [
            pygame.Rect(left, top, switch_width, switch_height),
            pygame.Rect(
                left + switch_width + gap,
                top,
                switch_width,
                switch_height * 4 // 3,
            ),
        ]

    def x_slider_rect(self) -> pygame.Rect:
        """Return the X-axis slider to the right of the mode switch."""
        first, mode = self.switch_rects()
        width = max(24, first.width // 2)
        # Leave the mode labels unobstructed between the switch and the slider.
        left = mode.right + max(100, first.width * 2)
        return pygame.Rect(left, first.top, width, first.height * 2)

    def set_x_slider_at(self, position: tuple[float, float]) -> bool:
        """Set the unidirectional X axis when the slider is touched."""
        rect = self.x_slider_rect()
        target = rect.inflate(24, 12)
        if not target.collidepoint(position):
            return False
        self.move_x_slider(position)
        return True

    def move_x_slider(self, position: tuple[float, float]) -> None:
        """Update a claimed slider, clamping drags beyond either endpoint."""
        _, bottom, travel = self.x_slider_track()
        # Use the same normalized -1..+1 convention as the Y joystick.  The
        # slider is inverted visually, so its bottom endpoint is -1 (the vJoy
        # minimum) and its top endpoint is +1.  Measure against the knob's
        # actual travel rather than the outer rectangle: otherwise dragging to
        # the visible bottom stop could never produce the minimum axis value.
        requested_x = max(
            -1.0,
            min(1.0, (bottom - position[1]) * 2.0 / travel - 1.0),
        )
        # Blade power may only be increased while ARMED (button 1) and while
        # the flight-mode selector is away from HOLD (button 5).  Reducing
        # power remains available at all times so the operator can always
        # return the blade to OFF.
        can_increase = self.state.buttons[0] and not self.state.buttons[4]
        if requested_x <= self.state.x or can_increase:
            self.state.x = requested_x

    def x_slider_fraction(self) -> float:
        """Return X as the zero-to-one value displayed by the UI."""
        return (self.state.x + 1.0) / 2.0

    def x_slider_track(self) -> tuple[int, int, int]:
        """Return the top, bottom, and length of the knob-center track."""
        inner = self.x_slider_rect().inflate(-6, -6)
        knob_radius = max(6, (inner.width - 4) // 2)
        top = inner.top + knob_radius
        bottom = inner.bottom - knob_radius
        return top, bottom, bottom - top

    def two_paddle_checkbox_rect(self) -> pygame.Rect:
        """Return the upper-left touch target for the orientation checkbox."""
        label_width, _ = self.small_font.size("Two Paddle input")
        control_width = 24 + 8 + label_width
        return pygame.Rect(24, 28, control_width, 28)

    def toggle_two_paddle_at(self, position: tuple[float, float]) -> bool:
        """Toggle the right stick orientation when its checkbox is touched."""
        if not self.two_paddle_checkbox_rect().collidepoint(position):
            return False
        self.two_paddle_input = not self.two_paddle_input
        self.state.right_y = 0.0
        for contact, side in list(self.contacts.items()):
            if side == "right":
                del self.contacts[contact]
        return True

    def toggle_switch_at(self, position: tuple[float, float]) -> bool:
        """Select the position touched on either switch."""
        for index, rect in enumerate(self.switch_rects()):
            if rect.collidepoint(position):
                if index == 0:
                    button_one = not self.state.buttons[0]
                    self.state.buttons[0] = button_one
                    self.state.buttons[1] = not button_one
                    if not button_one:
                        self._select_button(5)
                else:
                    if self.state.buttons[1]:
                        return True
                    third = min(2, int((position[1] - rect.top) * 3 / rect.height))
                    self._select_button(3 + third)
                return True
        return False

    def _select_button(self, number: int) -> None:
        """Select exactly one button on the three-position switch."""
        for button_number in range(3, 6):
            self.state.buttons[button_number - 1] = button_number == number

    def claim(self, contact: Hashable, position: tuple[float, float]) -> None:
        left, right, half_width, half_height = self.geometry()
        right_half_width, right_half_height = self.right_stick_half_sizes()
        distances = {
            "left": (
                ((position[0] - left[0]) / half_width) ** 2
                + ((position[1] - left[1]) / half_height) ** 2
            )
            ** 0.5,
            "right": (
                ((position[0] - right[0]) / right_half_width) ** 2
                + ((position[1] - right[1]) / right_half_height) ** 2
            )
            ** 0.5,
        }
        side = min(distances, key=distances.get)
        if distances[side] <= 1.35 and side not in self.contacts.values():
            self.contacts[contact] = side
            self.move(contact, position)

    def move(self, contact: Hashable, position: tuple[float, float]) -> None:
        side = self.contacts.get(contact)
        if not side:
            return
        left, right, _, half_height = self.geometry()
        if side == "left":
            self.state.left_y = stick_from_pointer(position, left, half_height)
        else:
            if self.two_paddle_input:
                self.state.right_y = stick_from_pointer(position, right, half_height)
            else:
                # Rotate the vertical RY control clockwise: its positive (bottom)
                # end points left after the quarter turn.
                self.state.right_y = -stick_from_pointer(
                    (position[1], position[0]), (right[1], right[0]), half_height
                )

    def right_stick_half_sizes(self) -> tuple[float, float]:
        """Return RY's half-sizes for its selected orientation."""
        _, _, half_width, half_height = self.geometry()
        if self.two_paddle_input:
            return half_width, half_height
        return half_height, half_width

    def release(self, contact: Hashable) -> None:
        side = self.contacts.pop(contact, None)
        if side == "left":
            self.state.left_y = 0.0
        elif side == "right":
            self.state.right_y = 0.0

    def keyboard(self) -> None:
        keys = pygame.key.get_pressed()
        if "left" not in self.contacts.values():
            self.state.left_y = float(keys[pygame.K_s]) - float(keys[pygame.K_w])
        if "right" not in self.contacts.values():
            if self.two_paddle_input:
                self.state.right_y = float(keys[pygame.K_DOWN]) - float(
                    keys[pygame.K_UP]
                )
            else:
                self.state.right_y = float(keys[pygame.K_LEFT]) - float(
                    keys[pygame.K_RIGHT]
                )

    def draw_stick(
        self, name: str, center, half_width: float, half_height: float, y: float
    ) -> None:
        outer = pygame.Rect(0, 0, half_width * 2, half_height * 2)
        outer.center = center
        pygame.draw.ellipse(self.screen, RING, outer, width=4)
        inner = outer.inflate(-half_width * 0.65, -half_height * 0.65)
        pygame.draw.ellipse(self.screen, RING, inner, width=2)
        horizontal = half_width > half_height
        knob = (
            (center[0] - y * half_width, center[1])
            if horizontal
            else (center[0], center[1] + y * half_height)
        )
        pygame.draw.circle(
            self.screen, ACCENT, knob, min(half_width, half_height) * 0.42
        )
        label = self.font.render(name, True, TEXT)
        self.screen.blit(
            label, label.get_rect(center=(center[0], center[1] - half_height - 48))
        )
        values = self.small_font.render(f"{name} {y:+.2f}", True, MUTED)
        self.screen.blit(
            values, values.get_rect(center=(center[0], center[1] - half_height - 22))
        )

    def draw_switches(self) -> None:
        for index, rect in enumerate(self.switch_rects()):
            pygame.draw.rect(self.screen, RING, rect, border_radius=rect.width // 2)
            inner = rect.inflate(-6, -6)
            pygame.draw.rect(self.screen, ACCENT, inner, border_radius=inner.width // 2)
            knob_radius = (inner.width - 8) // 2
            if index == 0:
                knob_y = (
                    inner.top + knob_radius + 4
                    if self.state.buttons[0]
                    else inner.bottom - knob_radius - 4
                )
            else:
                selected = next(i for i in range(3) if self.state.buttons[i + 2])
                knob_y = (
                    inner.top + knob_radius + 4,
                    inner.centery,
                    inner.bottom - knob_radius - 4,
                )[selected]
            pygame.draw.circle(self.screen, TEXT, (inner.centerx, knob_y), knob_radius)
            if index == 0:
                top_text, top_color = SWITCH_LABELS[0]
                bottom_text, bottom_color = SWITCH_LABELS[1]
                top_label = self.small_font.render(top_text, True, top_color)
                bottom_label = self.small_font.render(bottom_text, True, bottom_color)
                self.screen.blit(
                    top_label,
                    top_label.get_rect(center=(rect.centerx, rect.top - 13)),
                )
                self.screen.blit(
                    bottom_label,
                    bottom_label.get_rect(center=(rect.centerx, rect.bottom + 15)),
                )
            else:
                label_x = rect.right + 14
                for (text, color), y in zip(
                    SWITCH_LABELS[2:],
                    (
                        inner.top + knob_radius + 4,
                        inner.centery,
                        inner.bottom - knob_radius - 4,
                    ),
                ):
                    label = self.small_font.render(text, True, color)
                    self.screen.blit(label, label.get_rect(midleft=(label_x, y)))

    def draw_x_slider(self) -> None:
        """Draw blade power, with its below-zero half visually muted."""
        rect = self.x_slider_rect()
        pygame.draw.rect(self.screen, RING, rect, border_radius=rect.width // 2)
        inner = rect.inflate(-6, -6)
        pygame.draw.rect(self.screen, ACCENT, inner, border_radius=inner.width // 2)
        lower_half = pygame.Rect(
            inner.left, inner.centery, inner.width, inner.bottom - inner.centery
        )
        pygame.draw.rect(
            self.screen,
            MUTED,
            lower_half,
            border_bottom_left_radius=inner.width // 2,
            border_bottom_right_radius=inner.width // 2,
        )
        knob_radius = max(6, (inner.width - 4) // 2)
        value = self.x_slider_fraction()
        _, bottom, travel = self.x_slider_track()
        knob_y = round(bottom - value * travel)
        pygame.draw.circle(self.screen, TEXT, (inner.centerx, knob_y), knob_radius)
        label = self.small_font.render("Blade Power", True, TEXT)
        value_label = self.small_font.render("Blade OFF", True, MUTED)
        self.screen.blit(label, label.get_rect(center=(rect.centerx, rect.top - 13)))
        self.screen.blit(
            value_label,
            value_label.get_rect(center=(rect.centerx, rect.bottom + 15)),
        )

    def draw_two_paddle_checkbox(self) -> None:
        rect = self.two_paddle_checkbox_rect()
        box = pygame.Rect(rect.left, rect.centery - 12, 24, 24)
        pygame.draw.rect(self.screen, RING, box, width=2, border_radius=3)
        if self.two_paddle_input:
            pygame.draw.lines(
                self.screen,
                ACCENT,
                False,
                (
                    (box.left + 5, box.centery),
                    (box.left + 10, box.bottom - 6),
                    (box.right - 4, box.top + 5),
                ),
                width=3,
            )
        label = self.small_font.render("Two Paddle input", True, TEXT)
        self.screen.blit(label, label.get_rect(midleft=(box.right + 8, rect.centery)))

    def draw(self) -> None:
        self.screen.fill(BG)
        width, _ = self.screen.get_size()
        title = self.font.render("vJoy Touchpad", True, TEXT)
        self.screen.blit(title, title.get_rect(center=(width / 2, 40)))
        status = self.small_font.render(
            self.status, True, ACCENT if self.output else MUTED
        )
        self.screen.blit(status, status.get_rect(center=(width / 2, 74)))
        hint = self.small_font.render(
            "Switches select arming and flight modes  •  Esc exits",
            True,
            MUTED,
        )
        self.screen.blit(hint, hint.get_rect(center=(width / 2, 105)))
        self.draw_switches()
        self.draw_x_slider()
        self.draw_two_paddle_checkbox()
        left, right, half_width, half_height = self.geometry()
        self.draw_stick("Y", left, half_width, half_height, self.state.left_y)
        right_half_width, right_half_height = self.right_stick_half_sizes()
        self.draw_stick(
            "RY", right, right_half_width, right_half_height, self.state.right_y
        )
        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                    event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
                ):
                    running = False
                elif event.type == pygame.FINGERDOWN:
                    position = (
                        event.x * self.screen.get_width(),
                        event.y * self.screen.get_height(),
                    )
                    control_touched = self.toggle_two_paddle_at(position)
                    if not control_touched:
                        control_touched = self.toggle_switch_at(position)
                    if not control_touched and self.set_x_slider_at(position):
                        self.contacts[("finger", event.finger_id)] = "x"
                        control_touched = True
                    if not control_touched:
                        self.claim(("finger", event.finger_id), position)
                elif event.type == pygame.FINGERMOTION:
                    contact = ("finger", event.finger_id)
                    position = (
                        event.x * self.screen.get_width(),
                        event.y * self.screen.get_height(),
                    )
                    if self.contacts.get(contact) == "x":
                        self.move_x_slider(position)
                    else:
                        self.move(contact, position)
                elif event.type == pygame.FINGERUP:
                    self.release(("finger", event.finger_id))
                elif (
                    event.type == pygame.MOUSEBUTTONDOWN
                    and event.button == 1
                    and not getattr(event, "touch", False)
                ):
                    control_clicked = self.toggle_two_paddle_at(event.pos)
                    if not control_clicked:
                        control_clicked = self.toggle_switch_at(event.pos)
                    if not control_clicked and self.set_x_slider_at(event.pos):
                        self.contacts["mouse"] = "x"
                        control_clicked = True
                    if not control_clicked:
                        self.claim("mouse", event.pos)
                elif event.type == pygame.MOUSEMOTION and "mouse" in self.contacts:
                    if self.contacts["mouse"] == "x":
                        self.move_x_slider(event.pos)
                    else:
                        self.move("mouse", event.pos)
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    self.release("mouse")
            self.keyboard()
            if self.output:
                try:
                    self.output.update(self.state)
                except Exception as exc:
                    self.status, self.output = f"vJoy disconnected: {exc}", None
            self.draw()
            self.clock.tick(60)
        if self.output:
            self.output.reset()
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="A touch-friendly dual joystick for vJoy"
    )
    parser.add_argument(
        "--device", type=int, default=1, help="vJoy device ID (default: 1)"
    )
    parser.add_argument(
        "--windowed", action="store_true", help="open in a resizable window"
    )
    args = parser.parse_args()
    DualStickApp(args.device, args.windowed).run()


if __name__ == "__main__":
    main()
