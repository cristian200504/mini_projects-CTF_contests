"""Recover the AES-128 key from the supplied Joulescope trace using CPA."""
import re
import numpy as np
from pyjls import Reader

TRACE = "trace/embedded_encryptor.jls"
SOURCE = "extracted/handout/zephyrapp/src/main.c"
OUTPUT = "extracted/handout/output.txt"
IV = bytes.fromhex("10 9a 41 bc a7 71 bd 4b e3 52 27 71 2f d8 63 98")

AES_SOURCE = "extracted/handout/zephyrapp/src/aes.c"

def main():
    aes_source = open(AES_SOURCE, encoding="utf-8").read()
    sbox_text = re.search(r'static const uint8_t sbox\[256\] = \{(.*?)\};', aes_source, re.S).group(1)
    sbox = np.array([int(x, 16) for x in re.findall(r'0x[0-9a-f]+', sbox_text)], dtype=np.uint8)
    assert len(sbox) == 256
    source = open(SOURCE, encoding="utf-8").read()
    literal = re.search(r'char havamal\[\] = "(.*?)";\s*\n\s*int main', source, re.S).group(1)
    plaintext = literal.encode() + b'\0'
    lines = open(OUTPUT, encoding="utf-8").read()
    ciphertext = bytes.fromhex(' '.join(' '.join(m) for m in re.findall(r'^\s*([0-9a-f]{2}(?: [0-9a-f]{2}){7})  ([0-9a-f]{2}(?: [0-9a-f]{2}){7})', lines, re.M)))
    n = len(ciphertext) // 16
    print(f"{n} blocks; source has {len(plaintext)} bytes")
    assert n == len(plaintext) // 16
    data = np.frombuffer(plaintext[:n * 16], dtype=np.uint8).reshape(-1, 16).copy()
    data[0] ^= np.frombuffer(IV, dtype=np.uint8)
    data[1:] ^= np.frombuffer(ciphertext, dtype=np.uint8).reshape(-1, 16)[:-1]

    with Reader(TRACE) as reader:
        waveform = reader.fsr(1, 4_650_000, 8_850_000)
    coarse = waveform[:len(waveform)//100*100].reshape(-1, 100).mean(1) > .012
    transitions = np.diff(np.r_[False, coarse, False].astype(np.int8))
    starts = np.flatnonzero(transitions == 1) * 100
    ends = np.flatnonzero(transitions == -1) * 100
    pairs = [(s, e) for s, e in zip(starts, ends) if 3000 < e-s < 5000]
    starts = np.array([s + np.flatnonzero(waveform[max(0,s-100):s+100] > .012)[0] - 100 for s, _ in pairs])
    assert len(starts) == n, (len(starts), n)
    # Sub-sample scheduler jitter would otherwise smear the short instruction-level
    # leakage.  Register each execution to the common instruction waveform.
    padded = np.stack([waveform[s-80:s+3580] for s in starts]).astype(np.float64)
    offsets = np.zeros(n, dtype=int)
    for _ in range(3):
        template = np.stack([padded[i, 80 + offsets[i]:3580 + offsets[i]] for i in range(n)]).mean(axis=0)
        template = template - template.mean()
        for i, row in enumerate(padded):
            scores = [np.dot(row[80 + shift:3580 + shift] - row[80 + shift:3580 + shift].mean(), template)
                      for shift in range(-60, 61)]
            offsets[i] = np.argmax(scores) - 60
    print("alignment offsets:", offsets.min(), offsets.max(), np.bincount(offsets + 60).argmax() - 60)
    traces = np.stack([padded[i, 80 + offsets[i]:3580 + offsets[i]] for i in range(n)])
    traces -= traces.mean(axis=0)
    denom_t = np.sqrt((traces * traces).sum(axis=0))
    hw = np.array([i.bit_count() for i in range(256)])
    key = []
    candidates = np.arange(256, dtype=np.uint8)
    print("Input-XOR leakage candidates:")
    for byte in range(16):
        model = hw[np.bitwise_xor(data[:, byte, None], candidates)]
        model = model - model.mean(axis=0)
        corr = (model.T @ traces) / (np.sqrt((model * model).sum(axis=0))[:, None] * denom_t[None, :])
        peaks = np.max(np.abs(corr), axis=1)
        best = np.argsort(peaks)[-2:][::-1]
        print(byte, ' '.join(f'{k:02x}:{peaks[k]:.4f}' for k in best))
    print("S-box-output leakage candidates:")
    for byte in range(16):
        model = hw[sbox[np.bitwise_xor(data[:, byte, None], candidates)]]
        model = model - model.mean(axis=0)
        corr = (model.T @ traces) / (np.sqrt((model * model).sum(axis=0))[:, None] * denom_t[None, :])
        peaks = np.max(np.abs(corr), axis=1)
        best = np.argsort(peaks)[-3:][::-1]
        key.append(int(best[0]))
        print(byte, ' '.join(f'{k:02x}:{peaks[k]:.4f}' for k in best))
        if byte < 8:
            expected = b'NNS{leak'[byte]
            print(f"    expected {expected:02x}: rank {(peaks > peaks[expected]).sum() + 1}, corr {peaks[expected]:.4f}")
    print('KEY =', bytes(key).hex())

if __name__ == '__main__':
    main()
