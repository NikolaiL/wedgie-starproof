"""Small procedural previews inside ui.ask's empty content area."""
import lcd
import ui
from starproof_protocol import WORLDS, ARTIFACTS

COLORS = {"sol": (255, 203, 112), "kepler": (165, 251, 179), "vega": (189, 166, 255),
          "lyra": (255, 140, 186), "cinder": (255, 147, 101), "moss": (139, 230, 216)}


def planet(d, target, x=39, y=111, radius=24):
    color = lcd.color(*COLORS[target])
    for dy in range(-radius, radius + 1):
        width = int((radius * radius - dy * dy) ** 0.5)
        d.hline(x - width, y + dy, width * 2 + 1, color)
    for dx, dy, size in ((-9, -8, 7), (7, 4, 5), (-3, 12, 4)):
        d.fill_rect(x + dx, y + dy, size, 3, ui.WHITE)
    if target == "lyra":
        d.line(x - 31, y + 13, x + 31, y - 13, ui.RED)
    if target in ("kepler", "moss"):
        for dx in (-6, 5):
            d.fill_rect(x + dx, y - 4, 5, 7, ui.INK)
            d.pixel(x + dx + 1, y - 3, ui.WHITE)
        d.hline(x - 3, y + 8, 8, ui.INK)


def preview(d, fields):
    # Leave the firmware's title, answer bars and physical-key timing untouched.
    action, target = fields["action"], fields["target"]
    d.fill_rect(0, 78, 240, 104, ui.WHITE)
    if action == "claim":
        for offset in range(12):
            d.line(39 - offset, 91 + offset, 39 + offset, 91 + offset, ui.GREEN)
            d.line(27 + offset, 103 + offset, 51 - offset, 103 + offset, ui.GREEN_D)
        d.line(39, 91, 39, 115, ui.WHITE)
        d.line(27, 103, 51, 103, ui.WHITE)
        d.text("RELIC", 19, 128, ui.MUTED)
    elif action in ("refuel", "scavenge"):
        d.fill_rect(24, 91, 29, 40, ui.GREEN)
        d.rect(24, 91, 29, 40, ui.INK)
        d.fill_rect(31, 86, 15, 5, ui.INK)
        d.text("F", 35, 107, ui.WHITE)
    else:
        planet(d, target)
    d.big_text(WORLDS[target].upper(), 78, 83, ui.INK, 2)
    detail = ARTIFACTS[target] if action == "claim" else "Up to 2 fuel" if action == "scavenge" else "Tank: 8 fuel" if action == "refuel" else "From " + WORLDS[fields["from"]]
    for i, line in enumerate(ui.wrap(detail, 19)[:2]):
        d.text(line, 78, 107 + i * 12, ui.INK)
    reward = "4 credits + new map" if target in ("kepler", "lyra") else "+4 space credits"
    cost = reward if action == "claim" else "Free scavenged fuel" if action == "scavenge" else ("Free planet cache" if fields["cost"] == "0" else fields["cost"] + " space credits") if action == "refuel" else "Jump fuel: " + fields["cost"]
    ui.say(d, cost, 146, ui.GREEN_D)
    ui.say(d, fields["origin"].split("//", 1)[1], 160, ui.MUTED)
    ui.say(d, "Mission " + fields["session"][:8], 173, ui.MUTED)


class MissionDisplay(lcd.LCD):
    preview = None

    def show(self, y0=0, y1=240):
        if self.preview is not None:
            preview(self, self.preview)
        super().show(y0, y1)
