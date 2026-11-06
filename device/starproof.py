"""Starproof's USB signer. It reads the existing factory identity; it creates or changes no keys."""
import sys
import select
import json
import time
import hashlib
import binascii
import lcd
import ui
import wedgie
from starproof_protocol import WORLDS, parse_action, certificate_der
from starproof_actions import confirm_action
from starproof_art import MissionDisplay, dashboard

d = None
keys = None
linked = False
last_input = (0, 0)
last_input_at = 0
last_host_at = 0
game_stats = {"location": "sol", "fuel": 8, "credits": 8, "artifacts": 0}
chip = None
cert = None
fingerprint = None
reader = None
poll = None


def home(note="Ready for a mission"):
    d.preview = None
    dashboard(d, game_stats, note, linked)


def controls(pressed, now):
    global last_input, last_input_at
    if not linked or time.ticks_diff(now, last_host_at) > 5000:
        return
    current = (int(keys.held("right")) - int(keys.held("left")), int(keys.held("down")) - int(keys.held("up")))
    scan = "Y" in pressed
    action = next((value for key, value in (("A", "go"), ("B", "refuel"), ("X", "scavenge"), ("press", "info")) if key in pressed), None)
    if current != last_input or scan or action or (current != (0, 0) and time.ticks_diff(now, last_input_at) >= 80):
        message = {"type": "starproof_input", "dx": current[0], "dy": current[1], "scan": scan}
        if action:
            message["action"] = action
        wedgie.send(message)
        last_input, last_input_at = current, now


def identity():
    global chip, cert, fingerprint
    if cert is None:
        import optiga
        chip = optiga.Chip()
        raw = certificate_der(chip.read(optiga.CERT))
        cert = binascii.hexlify(raw).decode()
        fingerprint = binascii.hexlify(hashlib.sha256(raw).digest()).decode()
    return cert


def handle(message):
    global linked, last_host_at
    mid, kind = message.get("id"), message.get("type")
    if kind == "starproof_hello":
        linked = True
        last_host_at = time.ticks_ms()
        wedgie.send({"id": mid, "type": "starproof_identity", "protocol": "starproof/v1", "cert": identity(), "cancel": True, "appVersion": "0.5.0"})
    elif kind == "starproof_state":
        if message.get("location") not in WORLDS:
            raise ValueError("unknown stats location")
        for field, limit in (("fuel", 8), ("credits", 1000000), ("artifacts", 20)):
            value = message.get(field)
            if type(value) is not int or not 0 <= value <= limit:
                raise ValueError("bad stats " + field)
        for field in ("location", "fuel", "credits", "artifacts"):
            game_stats[field] = message[field]
        linked = True
        last_host_at = time.ticks_ms()
        home("Flight status")
        wedgie.send({"id": mid, "type": "starproof_state", "ok": True})
    elif kind == "starproof_wallet":
        import starproof_claim
        identity()
        xy = starproof_claim.wallet_public(chip)
        wedgie.send({"id": mid, "type": "starproof_wallet", "x": "0x" + binascii.hexlify(xy[:32]).decode(), "y": "0x" + binascii.hexlify(xy[32:]).decode(), "cert": cert})
    elif kind in ("starproof_sign", "starproof_airdrop"):
        is_airdrop = kind == "starproof_airdrop"
        text = message.get("text")
        if is_airdrop:
            import starproof_claim
            action = starproof_claim.parse_claim(text)
        else:
            action = parse_action(text)
        identity()
        if action["chip"] != fingerprint:
            raise ValueError("request is for another chip")
        titles = {"launch": "Launch mission?", "jump": "Commit jump?", "claim": "Claim artifact?", "refuel": "Refuel tank?", "scavenge": "Gather fuel?"}
        kind = "airdrop" if is_airdrop else action["action"]
        aborted = False

        def cancelled():
            nonlocal aborted
            if aborted:
                return True
            line = reader.pump(poll)
            if line is None:
                return False
            request = {}
            try:
                if line is False:
                    raise ValueError("request too large")
                request = json.loads(line)
                if not isinstance(request, dict):
                    raise ValueError("JSON object required")
                if request.get("type") != "starproof_cancel":
                    raise ValueError("finish the pending signing request first")
                aborted = request.get("request") == mid
                wedgie.send({"id": request.get("id"), "type": "starproof_cancelled", "cancelled": aborted})
            except Exception as error:
                wedgie.send({"id": request.get("id") if isinstance(request, dict) else None, "type": "error", "error": str(error)})
            return aborted

        d.preview = None if is_airdrop else action
        try:
            proof = starproof_claim.prove(chip, d, text, cert, fingerprint, cancelled) if is_airdrop else confirm_action(chip, d, text, titles[kind], [], cancelled=cancelled)
        finally:
            d.preview = None
        if proof is None:
            wedgie.send({"id": mid, "type": "refused"})
            home("Request cancelled" if aborted else "Action declined")
            return
        reply = {"id": mid, "type": "starproof_airdrop_proof" if is_airdrop else "starproof_signature"}
        reply.update(proof)
        wedgie.send(reply)
        home("Action signed")
    elif kind == "starproof_cancel":
        wedgie.send({"id": mid, "type": "starproof_cancelled", "cancelled": False})
    elif kind == "hello":
        wedgie.send(wedgie.hello(mid, running="starproof", app="starproof-1"))
    else:
        import slot
        slot.handle(message)
        home()


def run():
    global d, keys, reader, poll
    d, keys = MissionDisplay(), lcd.Keys(physical=True)
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)
    reader = wedgie.lines()
    home()
    while True:
        pressed = keys.pressed()
        controls(pressed, time.ticks_ms())
        line = reader.pump(poll)
        if reader.intr:
            reader.intr = False
            if wedgie.SEALED and not wedgie.is_open():
                import hatch
                if hatch.ctrl_c():
                    raise KeyboardInterrupt
                home()
        if line is False:
            wedgie.send({"type": "error", "error": "request too large"})
        elif line and line.strip():
            message = {}
            try:
                message = json.loads(line)
                if not isinstance(message, dict):
                    raise ValueError("JSON object required")
                handle(message)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as error:
                wedgie.send({"id": message.get("id") if isinstance(message, dict) else None, "type": "error", "error": str(error)})
                home("Could not sign; see browser")
        time.sleep_ms(20)
