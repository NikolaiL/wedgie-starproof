import sys
import types
import textwrap
import re

sys.path.insert(0, "device")


class Display:
    def fill_rect(self, x, y, width, height, color):
        assert 0 <= x < x + width <= 240
        assert 78 <= y < y + height <= 182, "art must never cover the title or physical answer bars"

    def hline(self, x, y, width, color):
        self.fill_rect(x, y, width, 1, color)

    def line(self, x, y, x2, y2, color):
        self.fill_rect(min(x, x2), min(y, y2), abs(x2 - x) + 1, abs(y2 - y) + 1, color)

    def rect(self, x, y, width, height, color):
        self.fill_rect(x, y, width, height, color)

    def pixel(self, x, y, color):
        self.fill_rect(x, y, 1, 1, color)

    def text(self, value, x, y, color):
        self.fill_rect(x, y, 8 * len(value), 8, color)

    def big_text(self, value, x, y, color, scale):
        self.fill_rect(x, y, 8 * len(value) * scale, 8 * scale, color)


sys.modules["lcd"] = types.SimpleNamespace(LCD=Display, color=lambda *rgb: rgb)
sys.modules["ui"] = types.SimpleNamespace(WHITE=0, INK=1, GREEN=2, GREEN_D=3, RED=4, MUTED=5,
    wrap=lambda value, width: textwrap.wrap(value, width),
    band=lambda d: None,
    say=lambda d, value, y, color: d.center_text(re.sub(r"\{[grk]\}", "*", value), y, color))
from starproof_art import preview, dashboard, COLORS

Display.center_text = lambda self, value, y, color, scale=1: self.big_text(value, (240 - len(value) * 8 * scale) // 2, y, color, scale)

for target in COLORS:
    for action in ("jump", "claim", "refuel", "scavenge"):
        for cost in (("0", "4") if action == "refuel" else ("1",)):
            preview(Display(), {"action": action, "target": target, "from": "sol", "cost": cost,
                "origin": "https://starproof-wedgie.vercel.app", "session": "f" * 32})
print("device art preserves controls OK")


class DashboardDisplay(Display):
    def fill_rect(self, x, y, width, height, color):
        assert 0 <= x < x + width <= 240
        assert 0 <= y < y + height <= 240

    def fill(self, color):
        pass

    def show(self):
        pass

    def big_text(self, value, x, y, color, scale):
        if value.lower() in COLORS or value.isdigit() and len(value) <= 3:
            assert scale == 3, "planet names and normal totals must be large"
        super().big_text(value, x, y, color, scale)


for target in COLORS:
    for credits in (8, 16, 999, 1000, 1000000):
        for linked in (False, True):
            dashboard(DashboardDisplay(), {"location": target, "fuel": 8, "credits": credits, "artifacts": 20}, "Flight status", linked)
print("visual dashboard fits all planets and totals OK")
