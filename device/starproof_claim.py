"""Read the existing Safe key and prove an airdrop claim. Never writes or locks chip objects."""
import hashlib
import binascii
import ui
from starproof_actions import decode_fields, _CancellableKeys, _Cancelled

NAMES = ("origin", "chain", "token", "amount", "recipient", "distributor", "campaign", "chip", "expires", "nonce")
TOKEN = "0x469f27bc9ca19d78455867aafc7aa4186d3ccccc"
CAMPAIGN = "0x4a9511007a150029c797d9156da9c8039afd6665045bcc456da2a4483c320234"


def _hex(value, size, prefix=""):
    return isinstance(value, str) and value.startswith(prefix) and len(value) == size + len(prefix) and all(c in "0123456789abcdef" for c in value[len(prefix):])


def parse_claim(text):
    fields = decode_fields(text, "starproof_airdrop", NAMES)
    origin = fields["origin"]
    local = origin.startswith("http://localhost:") or origin.startswith("http://127.0.0.1:")
    if origin != "https://starproof-wedgie.vercel.app" and not (local and origin.rsplit(":", 1)[1].isdigit()):
        raise ValueError("unknown claim origin")
    if fields["chain"] != "8453" or fields["token"] != TOKEN or fields["amount"] != "1000000000000000000000" or fields["campaign"] != CAMPAIGN:
        raise ValueError("unknown airdrop")
    if not all(_hex(fields[name], 40, "0x") and fields[name] != "0x" + "0" * 40 for name in ("recipient", "distributor")):
        raise ValueError("invalid claim address")
    if not _hex(fields["chip"], 64) or not _hex(fields["nonce"], 64) or not fields["expires"].isdigit() or len(fields["expires"]) > 12:
        raise ValueError("invalid claim challenge")
    return fields


def wallet_public(chip):
    import optiga
    # Safe Signer's startup helper can lock unfinished setup; this path is strictly read-only.
    for oid in (optiga.KEY2, optiga.DATA[11]):
        if chip.metadata(oid).get(0xC0) != b"\x07":
            raise ValueError("Set up and lock your wallet in Safe Signer first")
    saved = chip.read(optiga.DATA[11])
    if len(saved) < 70 or saved[:6] != b"wsafe1":
        raise ValueError("No Safe wallet public key on this chip")
    return saved[6:70]


def prove(chip, display, text, cert, fingerprint, cancelled):
    fields = parse_claim(text)
    if fields["chip"] != fingerprint:
        raise ValueError("claim is for another chip")
    xy = wallet_public(chip)
    options = {"keys": _CancellableKeys(cancelled), "no": "decline", "ms": 60000}
    try:
        token = fields["token"]
        if not ui.ask(display, "Review token", ["Base mainnet / chain 8453", "Token contract:", token[:21], token[21:], "1000 STARPROOF"], yes="next", **options):
            return None
        recipient = fields["recipient"]
        if not ui.ask(display, "Claim 1000?", ["STARPROOF on Base", "Receive in this Safe:", recipient[:21], recipient[21:], "One claim per chip"], yes="claim", **options):
            return None
    except _Cancelled:
        return None
    if cancelled():
        return None
    import optiga
    ui.progress("Proving claim", "in the Trust M", bar=False)
    inner = hashlib.sha256((text + "\n" + fields["nonce"]).encode()).digest()
    digest = hashlib.sha256(b"wedgie prove\x00" + inner).digest()
    r, s = chip.sign(optiga.KEY2, digest)
    if not chip.verify(digest, r, s, b"\x04" + xy):
        raise ValueError("Safe key does not match its stored public key")
    if cancelled():
        return None
    fr, fs = chip.sign(optiga.FACTORY_KEY, hashlib.sha256(b"wedgie safe key\x00" + xy).digest())
    return {"text": text, "code": fields["nonce"], "x": "0x" + binascii.hexlify(xy[:32]).decode(), "y": "0x" + binascii.hexlify(xy[32:]).decode(),
        "r": "0x%064x" % r, "s": "0x%064x" % s, "cert": cert, "fr": "0x%064x" % fr, "fs": "0x%064x" % fs}
