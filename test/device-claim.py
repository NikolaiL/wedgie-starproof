import sys, json, types, hashlib
sys.path.insert(0, 'device')
payload = json.load(sys.stdin)
text = payload['text']
asks, calls = [], []
answers = [True, True]
class Keys:
    def __init__(self, physical=False): assert physical
    def pressed(self): return []
def ask(display, title, lines, **options):
    assert len(lines) <= 5 and all(len(line) <= 28 for line in lines)
    assert options['keys'].pressed() == []
    asks.append((title,lines));return answers.pop(0)
sys.modules['lcd'] = types.SimpleNamespace(Keys=Keys)
sys.modules['ui'] = types.SimpleNamespace(ask=ask,progress=lambda *a,**k:None)
sys.modules['optiga'] = types.SimpleNamespace(KEY2=2,FACTORY_KEY=1,DATA=list(range(12)))
import starproof_claim as C
class Chip:
    def metadata(self,oid): return {0xC0:b'\x07'}
    def read(self,oid):
        assert oid==11
        return b'wsafe1'+bytes.fromhex('ab'*64)
    def sign(self,slot,digest):
        calls.append((slot,digest.hex()))
        return (slot,slot+1)
    def verify(self,digest,r,s,pub):
        assert pub == b'\x04'+bytes.fromhex('ab'*64)
        return True
chip=Chip()
proof=C.prove(chip,object(),text,'cached certificate','c'*64,lambda:False)
f=C.parse_claim(text)
expected=hashlib.sha256(b'wedgie prove\0'+hashlib.sha256((text+'\n'+f['nonce']).encode()).digest()).hexdigest()
assert calls==[(2,expected),(1,hashlib.sha256(b'wedgie safe key\0'+bytes.fromhex('ab'*64)).hexdigest())]
assert proof['code']==f['nonce'] and proof['cert']=='cached certificate'
assert ''.join(asks[1][1][2:4])==f['recipient']
assert ''.join(asks[0][1][2:4])==f['token']
for replacements in [('chain=8453','chain=1'),('amount=1000000000000000000000','amount=1'),('starproof_airdrop/v1','starproof/v1'),('origin=http://localhost:4173','origin=https://evil.example')]:
    try:C.parse_claim(text.replace(*replacements))
    except ValueError:pass
    else:raise AssertionError('altered claim accepted')
for page in (0,1):
    calls.clear();answers[:]=[False] if page==0 else [True,False]
    assert C.prove(chip,object(),text,'cached certificate','c'*64,lambda:False) is None
    assert not calls
calls.clear();answers[:]=[True,True]
assert C.prove(chip,object(),text,'cached certificate','c'*64,lambda:True) is None
assert not calls
class Incomplete(Chip):
    def metadata(self,oid):return {0xC0:b'\x01'}
try:C.wallet_public(Incomplete())
except ValueError:pass
else:raise AssertionError('incomplete wallet accepted')
assert not calls
print('wallet claim parsing, approval, cancellation and read-only setup OK')
