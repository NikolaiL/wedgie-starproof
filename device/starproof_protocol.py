"""Strict, shared-format action parsing; no hardware imports so it can be tested on a host."""
from starproof_actions import decode_fields, certificate_der

FIELDS = ("origin", "session", "challenge", "chip", "action", "from", "target", "cost", "sequence", "expires", "nonce")
WORLDS = {"sol": "Sol", "kepler": "Kepler", "vega": "Vega", "lyra": "Lyra", "cinder": "Cinder", "moss": "Moss"}
ARTIFACTS = {"sol": "Lunar archive", "kepler": "Ocean prism", "vega": "Stellar compass", "lyra": "Echo capsule", "cinder": "Ember seed", "moss": "Living atlas"}


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
    if action not in ("launch", "jump", "claim", "refuel"):
        raise ValueError("not a strategic action")
    if fields["cost"] not in (("0", "3") if action == "refuel" else ("1",) if action == "jump" else ("0",)):
        raise ValueError("unexpected action cost")
    if action == "launch" and (source != "sol" or target != "sol" or fields["sequence"] != "0"):
        raise ValueError("bad launch")
    if action == "jump" and source == target:
        raise ValueError("choose another system")
    if action in ("claim", "refuel") and source != target:
        raise ValueError("act in the current system")
    return fields
