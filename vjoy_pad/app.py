"""Pygame user interface for the virtual gamepad."""

from __future__ import annotations

import argparse
from typing import Hashable

import pygame

from .controller import PadState, VJoyOutput, stick_from_pointer

BG = (13, 18, 28)
PANEL = (27, 36, 52)
RING = (64, 79, 103)
ACCENT = (66, 211, 173)
TEXT = (235, 241, 248)
MUTED = (148, 163, 184)


class DualStickApp:
    def __init__(self, device_id: int = 1, windowed: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption("vJoy Touchpad")
        flags = pygame.RESIZABLE if windowed else pygame.FULLSCREEN
        size = (1100, 650) if windowed else (0, 0)
        self.screen = pygame.display.set_mode(size, flags)
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

    def geometry(self):
        width, height = self.screen.get_size()
        radius = max(70, min(width * 0.17, height * 0.29))
        y = height * 0.57
        return (width * 0.27, y), (width * 0.73, y), radius

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
        pygame.draw.circle(self.screen, PANEL, center, radius)
        pygame.draw.circle(self.screen, RING, center, radius, width=4)
        pygame.draw.circle(self.screen, RING, center, radius * 0.56, width=2)
        knob = (center[0] + x * radius, center[1] + y * radius)
        pygame.draw.circle(self.screen, ACCENT, knob, radius * 0.25)
        label = self.font.render(name, True, TEXT)
        self.screen.blit(label, label.get_rect(center=(center[0], center[1] + radius + 38)))
        values = self.small_font.render(f"X {x:+.2f}   Y {y:+.2f}", True, MUTED)
        self.screen.blit(values, values.get_rect(center=(center[0], center[1] + radius + 68)))

    def draw(self) -> None:
        self.screen.fill(BG)
        width, _ = self.screen.get_size()
        title = self.font.render("vJoy Touchpad", True, TEXT)
        self.screen.blit(title, title.get_rect(center=(width / 2, 40)))
        status = self.small_font.render(self.status, True, ACCENT if self.output else MUTED)
        self.screen.blit(status, status.get_rect(center=(width / 2, 74)))
        left, right, radius = self.geometry()
        self.draw_stick("LEFT  •  X / Y", left, radius, self.state.left_x, self.state.left_y)
        self.draw_stick("RIGHT  •  RX / RY", right, radius, self.state.right_x, self.state.right_y)
        hint = self.small_font.render("Touch or drag both sticks  •  Esc exits  •  WASD + arrow keys also work", True, MUTED)
        self.screen.blit(hint, hint.get_rect(center=(width / 2, self.screen.get_height() - 25)))
        pygame.display.flip()

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                elif event.type == pygame.FINGERDOWN:
                    self.claim(("finger", event.finger_id), (event.x * self.screen.get_width(), event.y * self.screen.get_height()))
                elif event.type == pygame.FINGERMOTION:
                    self.move(("finger", event.finger_id), (event.x * self.screen.get_width(), event.y * self.screen.get_height()))
                elif event.type == pygame.FINGERUP:
                    self.release(("finger", event.finger_id))
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not getattr(event, "touch", False):
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
