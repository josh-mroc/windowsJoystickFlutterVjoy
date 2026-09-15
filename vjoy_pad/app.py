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
SWITCH_OFF = (42, 52, 68)


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
        self.contacts: dict[Hashable, str] = {}
        self.output = None
        self.status = "Preview mode"
        try:
            self.output = VJoyOutput(device_id)
            self.status = f"Connected to vJoy device {device_id}"
        except Exception as exc:
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
        return stick_geometry(width, height)

    def switch_rects(self) -> list[pygame.Rect]:
        """Return four centered, touch-friendly vertical switch bounds."""
        width, height = self.screen.get_size()
        switch_width = max(42, min(58, width // 18))
        switch_height = max(76, min(96, height // 7))
        gap = max(16, switch_width // 2)
        row_width = switch_width * 4 + gap * 3
        left = (width - row_width) // 2
        top = 122
        return [
            pygame.Rect(left + index * (switch_width + gap), top, switch_width, switch_height)
            for index in range(4)
        ]

    def toggle_switch_at(self, position: tuple[float, float]) -> bool:
        """Toggle the switch at position and report whether one was hit."""
        for index, rect in enumerate(self.switch_rects()):
            if rect.collidepoint(position):
                self.state.buttons[index] = not self.state.buttons[index]
                return True
        return False

    def claim(self, contact: Hashable, position: tuple[float, float]) -> None:
        left, right, radius = self.geometry()
        distances = {
            "left": pygame.Vector2(position).distance_to(left),
            "right": pygame.Vector2(position).distance_to(right),
        }
        side = min(distances, key=distances.get)
        if distances[side] <= radius * 1.35 and side not in self.contacts.values():
            self.contacts[contact] = side
            self.move(contact, position)

    def move(self, contact: Hashable, position: tuple[float, float]) -> None:
        side = self.contacts.get(contact)
        if not side:
            return
        left, right, radius = self.geometry()
        x, y = stick_from_pointer(position, left if side == "left" else right, radius)
        if side == "left":
            self.state.left_x, self.state.left_y = x, y
        else:
            self.state.right_x, self.state.right_y = x, y

    def release(self, contact: Hashable) -> None:
        side = self.contacts.pop(contact, None)
        if side == "left":
            self.state.left_x = self.state.left_y = 0.0
        elif side == "right":
            self.state.right_x = self.state.right_y = 0.0

    def keyboard(self) -> None:
        keys = pygame.key.get_pressed()
        if "left" not in self.contacts.values():
            self.state.left_x = float(keys[pygame.K_d]) - float(keys[pygame.K_a])
            self.state.left_y = float(keys[pygame.K_s]) - float(keys[pygame.K_w])
        if "right" not in self.contacts.values():
            self.state.right_x = float(keys[pygame.K_RIGHT]) - float(keys[pygame.K_LEFT])
            self.state.right_y = float(keys[pygame.K_DOWN]) - float(keys[pygame.K_UP])

    def draw_stick(self, name: str, center, radius: float, x: float, y: float) -> None:
        pygame.draw.circle(self.screen, RING, center, radius, width=4)
        pygame.draw.circle(self.screen, RING, center, radius * 0.56, width=2)
        knob = (center[0] + x * radius, center[1] + y * radius)
        pygame.draw.circle(self.screen, ACCENT, knob, radius * 0.25)
        label = self.font.render(name, True, TEXT)
        self.screen.blit(
            label, label.get_rect(center=(center[0], center[1] - radius - 48))
        )
        values = self.small_font.render(f"X {x:+.2f}   Y {y:+.2f}", True, MUTED)
        self.screen.blit(
            values, values.get_rect(center=(center[0], center[1] - radius - 22))
        )

    def draw_switches(self) -> None:
        for index, (rect, enabled) in enumerate(
            zip(self.switch_rects(), self.state.buttons), start=1
        ):
            pygame.draw.rect(self.screen, RING, rect, border_radius=rect.width // 2)
            inner = rect.inflate(-6, -6)
            pygame.draw.rect(
                self.screen,
                ACCENT if enabled else SWITCH_OFF,
                inner,
                border_radius=inner.width // 2,
            )
            knob_radius = (inner.width - 8) // 2
            knob_y = (
                inner.top + knob_radius + 4
                if enabled
                else inner.bottom - knob_radius - 4
            )
            pygame.draw.circle(self.screen, TEXT, (inner.centerx, knob_y), knob_radius)
            label = self.small_font.render(str(index), True, TEXT)
            self.screen.blit(label, label.get_rect(center=(rect.centerx, rect.bottom + 15)))

    def draw(self) -> None:
        self.screen.fill(BG)
        width, _ = self.screen.get_size()
        title = self.font.render("vJoy Touchpad", True, TEXT)
        self.screen.blit(title, title.get_rect(center=(width / 2, 40)))
        status = self.small_font.render(self.status, True, ACCENT if self.output else MUTED)
        self.screen.blit(status, status.get_rect(center=(width / 2, 74)))
        hint = self.small_font.render(
            "Switch up = on, down = off  •  Touch or drag both sticks  •  Esc exits",
            True,
            MUTED,
        )
        self.screen.blit(hint, hint.get_rect(center=(width / 2, 105)))
        self.draw_switches()
        left, right, radius = self.geometry()
        self.draw_stick("LEFT  •  X / Y", left, radius, self.state.left_x, self.state.left_y)
        self.draw_stick("RIGHT  •  RX / RY", right, radius, self.state.right_x, self.state.right_y)
        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.FINGERDOWN:
                    position = (event.x * self.screen.get_width(), event.y * self.screen.get_height())
                    if not self.toggle_switch_at(position):
                        self.claim(("finger", event.finger_id), position)
                elif event.type == pygame.FINGERMOTION:
                    self.move(("finger", event.finger_id), (event.x * self.screen.get_width(), event.y * self.screen.get_height()))
                elif event.type == pygame.FINGERUP:
                    self.release(("finger", event.finger_id))
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not getattr(event, "touch", False):
                    if not self.toggle_switch_at(event.pos):
                        self.claim("mouse", event.pos)
                elif event.type == pygame.MOUSEMOTION and "mouse" in self.contacts:
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
    parser = argparse.ArgumentParser(description="A touch-friendly dual joystick for vJoy")
    parser.add_argument("--device", type=int, default=1, help="vJoy device ID (default: 1)")
    parser.add_argument("--windowed", action="store_true", help="open in a resizable window")
    args = parser.parse_args()
    DualStickApp(args.device, args.windowed).run()


if __name__ == "__main__":
    main()
