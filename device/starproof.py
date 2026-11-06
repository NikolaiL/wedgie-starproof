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
from starproof_protocol import parse_action, certificate_der
from starproof_actions import confirm_action
from starproof_art import MissionDisplay

d = None
keys = None
chip = None
cert = None
fingerprint = None
reader = None
poll = None


def home(note="Ready for a mission"):
    d.preview = None
    ui.page(d, "Starproof", [(note, ui.INK), ("Jump / refuel / explore", ui.MUTED), ("Explore freely in browser", ui.MUTED)], "{g} on a request  {r} decline")


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
    mid, kind = message.get("id"), message.get("type")
    if kind == "starproof_hello":
        wedgie.send({"id": mid, "type": "starproof_identity", "protocol": "starproof/v1", "cert": identity(), "cancel": True, "appVersion": "0.3.0"})
    elif kind == "starproof_sign":
        text = message.get("text")
        action = parse_action(text)
        identity()
        if action["chip"] != fingerprint:
            raise ValueError("request is for another chip")
        titles = {"launch": "Launch mission?", "jump": "Commit jump?", "claim": "Claim artifact?", "refuel": "Refuel tank?", "scavenge": "Gather fuel?"}
        kind = action["action"]
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

        d.preview = action
        try:
            proof = confirm_action(chip, d, text, titles[kind], [], cancelled=cancelled)
        finally:
            d.preview = None
        if proof is None:
            wedgie.send({"id": mid, "type": "refused"})
            home("Request cancelled" if aborted else "Action declined")
            return
        wedgie.send({"id": mid, "type": "starproof_signature", "r": proof["r"], "s": proof["s"]})
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
        keys.pressed()
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
