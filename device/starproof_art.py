"""Small procedural previews inside ui.ask's empty content area."""
import lcd
import ui
from starproof_protocol import WORLDS, ARTIFACTS

COLORS = {'sol': (255, 203, 112), 'kepler': (165, 251, 179), 'vega': (189, 166, 255), 'lyra': (255, 140, 186), 'cinder': (255, 147, 101), 'moss': (139, 230, 216), 'orion': (255, 185, 138), 'nova': (255, 214, 104), 'borealis': (128, 255, 216), 'glacier': (168, 231, 255), 'aurora': (236, 163, 255), 'polaris': (225, 239, 255), 'vulcan': (255, 134, 122), 'ember': (255, 191, 108), 'dune': (237, 207, 136), 'mirage': (255, 153, 217), 'umbra': (168, 155, 255), 'nyx': (132, 177, 255), 'echo': (139, 221, 215), 'rift': (249, 155, 255)}

# Match the browser HUD using palette slots unused by the dashboard's firmware UI.
RESOURCE_ROWS = (
    ("FUEL", "fuel", 2, (215, 255, 99)),
    ("CREDITS", "credits", 3, (255, 207, 127)),
    ("ARTIFACTS", "artifacts", 5, (255, 154, 200)),
)


def dashboard(d, stats, note, linked):
    d.fill(ui.WHITE)
    ui.band(d)
    ui.say(d, note[:28], 42, ui.MUTED)
    d.center_text(WORLDS[stats["location"]].upper(), 60, ui.INK, 3)
    for i, (label, field, slot, rgb) in enumerate(RESOURCE_ROWS):
        y = 90 + i * 38
        lcd.tint(slot, *rgb)
        d.fill_rect(10, y, 220, 34, slot)
        d.text(label, 22, y + (6 if field == "artifacts" else 13), ui.INK)
        if field == "artifacts":
            d.text("COLLECTED", 22, y + 20, ui.INK)
        value = str(stats[field])
        scale = 3 if len(value) <= 3 else 2 if len(value) <= 6 else 1
        d.big_text(value, 220 - len(value) * 8 * scale, y + (34 - 8 * scale) // 2, ui.INK, scale)
    if linked:
        ui.say(d, "{g} go  {k} refuel  {k} gather", 208, ui.INK)
        ui.say(d, "{r} scan  Stick: fly / info", 224, ui.MUTED)
    else:
        ui.say(d, "Connect Starproof in browser", 222, ui.MUTED)
    d.show()


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
    reward = "4 credits + new map" if target in ("kepler", "lyra", "moss", "cinder", "borealis") else "+4 space credits"
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
