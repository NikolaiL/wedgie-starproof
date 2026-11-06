"""Strict, shared-format action parsing; no hardware imports so it can be tested on a host."""
import math
from starproof_actions import decode_fields, certificate_der

FIELDS = ("origin", "session", "challenge", "chip", "action", "from", "target", "cost", "sequence", "expires", "nonce")
WORLDS = {'sol': 'Sol', 'kepler': 'Kepler', 'vega': 'Vega', 'lyra': 'Lyra', 'cinder': 'Cinder', 'moss': 'Moss', 'orion': 'Orion', 'nova': 'Nova', 'borealis': 'Borealis', 'glacier': 'Glacier', 'aurora': 'Aurora', 'polaris': 'Polaris', 'vulcan': 'Vulcan', 'ember': 'Ember', 'dune': 'Dune', 'mirage': 'Mirage', 'umbra': 'Umbra', 'nyx': 'Nyx', 'echo': 'Echo', 'rift': 'Rift'}
ARTIFACTS = {'sol': 'Lunar archive', 'kepler': 'Ocean prism', 'vega': 'Stellar compass', 'lyra': 'Echo capsule', 'cinder': 'Ember seed', 'moss': 'Living atlas', 'orion': 'Comet spoon', 'nova': 'Sun marble', 'borealis': 'Aurora ribbon', 'glacier': 'Frozen hourglass', 'aurora': 'Cloud lantern', 'polaris': 'Northstar crown', 'vulcan': 'Magma heart', 'ember': 'Cinder pearl', 'dune': 'Sandglass seed', 'mirage': 'Prism bloom', 'umbra': 'Shadow key', 'nyx': 'Night compass', 'echo': 'Whisper stone', 'rift': 'Infinity pebble'}
POSITIONS = {'sol': (0, 0), 'kepler': (0.9, -0.6), 'vega': (1.7, 0.5), 'lyra': (2.4, -0.9), 'cinder': (3.2, 0.3), 'moss': (4, -0.5), 'orion': (-1.4, -1.2), 'nova': (-1.6, 1.1), 'borealis': (-0.4, -3.2), 'glacier': (1.9, -3.6), 'aurora': (-2.6, -3.2), 'polaris': (0.8, -5.3), 'vulcan': (1.2, 2.6), 'ember': (3.3, 2.5), 'dune': (-1.2, 3.3), 'mirage': (1.3, 4.7), 'umbra': (-4.7, -0.8), 'nyx': (-4.8, 1.7), 'echo': (-4.6, -3.2), 'rift': (-6.8, 0.5)}


def jump_cost(source, target):
    a, b = POSITIONS[source], POSITIONS[target]
    return max(2, min(8, math.ceil(math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) * 1.8)))


def _hex(value, length):
    return len(value) == length and all(c in "0123456789abcdef" for c in value)


def parse_action(text):
    fields = decode_fields(text, "starproof", FIELDS)
    if fields["origin"] != "https://starproof-wedgie.vercel.app":
        parts = fields["origin"].split(":")
        if len(parts) != 3 or parts[0] + ":" + parts[1] not in ("http://localhost", "http://127.0.0.1"):
            raise ValueError("use Starproof's published site or the local demo")
        port = parts[2]
        if not port.isdigit() or not 1 <= int(port) <= 65535:
            raise ValueError("bad origin")
    for name, length in (("session", 32), ("challenge", 32), ("chip", 64), ("nonce", 64)):
        if not _hex(fields[name], length):
            raise ValueError("bad " + name)
    for name in ("sequence", "expires"):
        value = fields[name]
        if not value.isdigit() or len(value) > 11 or str(int(value)) != value:
            raise ValueError("bad " + name)
    action, source, target = fields["action"], fields["from"], fields["target"]
    if source not in WORLDS or target not in WORLDS:
        raise ValueError("unknown destination")
    if action not in ("launch", "jump", "claim", "refuel", "scavenge"):
        raise ValueError("not a strategic action")
    if fields["cost"] not in (("0", "4") if action == "refuel" else (str(jump_cost(source, target)),) if action == "jump" else ("0",)):
        raise ValueError("unexpected action cost")
    if action == "launch" and (source != "sol" or target != "sol" or fields["sequence"] != "0"):
        raise ValueError("bad launch")
    if action == "jump" and source == target:
        raise ValueError("choose another system")
    if action in ("claim", "refuel", "scavenge") and source != target:
        raise ValueError("act in the current system")
    return fields
