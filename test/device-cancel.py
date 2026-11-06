import json
import sys
import types

sys.path.insert(0, "device")
text = json.load(sys.stdin)["text"]
sent, signed = [], []


class Keys:
    def __init__(self, physical=False):
        assert physical

    def pressed(self):
        return []


def ask(*args, **kwargs):
    for _ in range(10):
        assert kwargs["keys"].pressed() == []
    raise AssertionError("the pending prompt was not cancelled")


sys.modules["lcd"] = types.SimpleNamespace(Keys=Keys)
sys.modules["ui"] = types.SimpleNamespace(ask=ask, progress=lambda *a, **k: None, page=lambda *a, **k: None, INK=1, MUTED=2)
sys.modules["wedgie"] = types.SimpleNamespace(send=sent.append)
sys.modules["starproof_art"] = types.SimpleNamespace(MissionDisplay=object)
import starproof
from starproof_protocol import parse_action


class Reader:
    def __init__(self):
        self.lines = iter([
            json.dumps({"id": 6, "type": "starproof_state", "location": "sol", "fuel": 8, "credits": 8, "artifacts": 0}),
            json.dumps({"id": 7, "type": "press", "key": "A"}),
            json.dumps({"id": 8, "type": "starproof_cancel", "request": 40}),
            "not json",
            json.dumps({"id": 9, "type": "starproof_cancel", "request": 41}),
        ])

    def pump(self, poll):
        return next(self.lines, None)


starproof.reader = Reader()
starproof.d = types.SimpleNamespace(preview=None)
starproof.cert = "cached public certificate"
starproof.fingerprint = parse_action(text)["chip"]
starproof.chip = types.SimpleNamespace(sign=lambda *args: signed.append(args))
starproof.handle({"id": 41, "type": "starproof_sign", "text": text})
assert not signed
assert sent[0]["type"] == "error", "other commands must not execute inside approval"
assert next(value for value in sent if value.get("id") == 8) == {"id": 8, "type": "starproof_cancelled", "cancelled": False}
assert sent[-2] == {"id": 9, "type": "starproof_cancelled", "cancelled": True}
assert sent[-1] == {"id": 41, "type": "refused"}
starproof.handle({"id": 10, "type": "starproof_cancel", "request": 41})
assert sent[-1] == {"id": 10, "type": "starproof_cancelled", "cancelled": False}
print("device request cancellation OK")

starproof.linked = True
held = set()
starproof.keys = types.SimpleNamespace(held=lambda key: key in held)
starproof.time = types.SimpleNamespace(ticks_diff=lambda a,b: a-b, ticks_ms=lambda:250)
starproof.controls(["press"],100)
assert sent[-1] == {"type":"starproof_input","dx":0,"dy":0,"scan":True}
held.add("right")
starproof.controls([],200)
assert sent[-1]["dx"] == 1
held.clear()
starproof.controls([],220)
assert sent[-1]["dx"] == 0
before = dict(starproof.game_stats)
try: starproof.handle({"id":20,"type":"starproof_state","location":"sol","fuel":99,"credits":0,"artifacts":0})
except ValueError: pass
else: raise AssertionError("invalid display stats accepted")
assert starproof.game_stats == before
starproof.handle({"id":21,"type":"starproof_state","location":"borealis","fuel":4,"credits":16,"artifacts":7})
assert starproof.game_stats["location"] == "borealis"
assert sent[-1] == {"id":21,"type":"starproof_state","ok":True}
assert not signed
print("physical joystick and browser stats stay separate from approval OK")
