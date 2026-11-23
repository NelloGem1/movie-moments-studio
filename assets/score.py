"""Reusable synthesized score engine — trailer percussion + orchestra."""
import numpy as np, wave, os

SR = 48000


class Score:
    def __init__(self, dur):
        self.dur = dur
        self.n = int(SR * dur)
        self.mus = np.zeros((2, self.n), dtype=np.float32)
        self.rng = np.random.default_rng(7)

    def add(self, sig, t0, pan=0.0, gain=0.8):
        i = int(t0 * SR)
        if i >= self.n:
            return
        L = sig[:max(0, min(len(sig), self.n - i))]
        gl = np.sqrt(0.5 * (1 - pan)); gr = np.sqrt(0.5 * (1 + pan))
        self.mus[0, i:i + len(L)] += L * gl * gain
        self.mus[1, i:i + len(L)] += L * gr * gain

    @staticmethod
    def lp(x, a):
        y = np.empty_like(x); acc = 0.0
        for i, v in enumerate(x):
            acc += a * (v - acc); y[i] = acc
        return y

    def strings(self, freqs, t0, dur, vol=0.3, vib=5.0):
        L = int(SR * dur); t = np.arange(L) / SR
        sig = np.zeros(L)
        for f in freqs:
            for det in (-6, -2, 2, 6):
                ff = f * 2 ** (det / 1200)
                vibf = 1 + 0.004 * np.sin(2 * np.pi * vib * t)
                ph = 2 * np.pi * np.cumsum(ff * vibf) / SR
                sig += (2 * ((ph / np.pi) % 2 - 1)) * 0.25
        sig = self.lp(sig, 0.06)
        e = np.minimum(1, t / (dur * 0.3)) * np.minimum(1, (dur - t) * 3)
        self.add(sig * e * vol, t0)

    def note(self, freq, t0, dur, vol=0.3, bright=0.15):
        L = int(SR * dur); t = np.arange(L) / SR
        ph = 2 * np.pi * np.cumsum(freq * (1 + 0.003 * np.sin(2 * np.pi * 5.5 * t))) / SR
        sig = (2 * ((ph / np.pi) % 2 - 1)) * 0.5 + np.sin(ph) * 0.5
        sig = self.lp(sig, bright)
        e = np.minimum(1, t / 0.04) * np.exp(-t * 1.2) * np.minimum(1, (dur - t) * 8)
        self.add(sig * e * vol, t0)

    def brass(self, freqs, t0, dur=1.2, vol=0.35):
        L = int(SR * dur); t = np.arange(L) / SR
        sig = np.zeros(L)
        for f in freqs:
            for det in (-8, 0, 8):
                ff = f * 2 ** (det / 1200)
                ph = 2 * np.pi * np.cumsum(ff) / SR
                sig += (2 * ((ph / np.pi) % 2 - 1)) * 0.3
        sig = self.lp(sig, 0.12)
        e = np.minimum(1, t / 0.02) * np.exp(-t * 2.2)
        self.add(sig * e * vol, t0)

    def harp(self, freq, t0, vol=0.2):
        L = int(SR * 1.4); t = np.arange(L) / SR
        sig = sum(np.sin(2 * np.pi * freq * h * t) / h for h in (1, 2, 3, 4))
        self.add(sig * np.exp(-t * 3.5) * vol, t0)

    def celesta(self, freq, t0, vol=0.12):
        L = int(SR * 0.9); t = np.arange(L) / SR
        sig = (np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 3 * t)
               + 0.15 * np.sin(2 * np.pi * freq * 5 * t))
        self.add(sig * np.exp(-t * 6) * vol, t0)

    def timpani(self, t0, f=70, vol=0.7):
        L = int(SR * 0.9); t = np.arange(L) / SR
        fr = f * np.exp(-t * 4) + 35
        ph = 2 * np.pi * np.cumsum(fr) / SR
        self.add(np.sin(ph) * np.exp(-t * 5) * vol, t0)

    def timpani_roll(self, t0, dur, vol=0.4):
        hits = int(dur / 0.09)
        for k in range(hits):
            self.timpani(t0 + k * 0.09 * (1 - k / hits * 0.5),
                         70 + 30 * k / hits, vol * (0.4 + 0.6 * k / hits))

    def taiko(self, t0, f0=75, f1=42, dec=0.5, vol=0.9):
        L = int(SR * dec); t = np.arange(L) / SR
        f = f1 + (f0 - f1) * np.exp(-t * 18)
        ph = 2 * np.pi * np.cumsum(f) / SR
        env = np.exp(-t * 9)
        hit = np.sin(ph) * env
        click = self.lp(self.rng.standard_normal(L), 0.05) * np.exp(-t * 200) * 0.25
        self.add(hit + click, t0, vol * 0.9)

    def boom(self, t0, vol=0.9):
        L = int(SR * 1.2); t = np.arange(L) / SR
        f = 48 * np.exp(-t * 3) + 28
        ph = 2 * np.pi * np.cumsum(f) / SR
        env = np.minimum(1, t * 80) * np.exp(-t * 4)
        self.add(np.sin(ph) * env * vol, t0)

    def riser(self, t0, dur=3.0, vol=0.3):
        L = int(SR * dur); t = np.arange(L) / SR
        k = t / dur
        sweep = np.sin(2 * np.pi * np.cumsum(150 + 900 * k ** 2) / SR)
        noise = self.lp(self.rng.standard_normal(L), 0.05)
        self.add((sweep * 0.5 + noise * 0.8) * k ** 2.2 * vol, t0)

    def tick(self, t0, f=1800, vol=0.1):
        L = int(SR * 0.08); t = np.arange(L) / SR
        self.add(np.sin(2 * np.pi * f * t) * np.exp(-t * 60) * vol, t0)

    def write(self, path):
        self.mus = np.tanh(self.mus * 1.3)
        self.mus = self.mus / np.abs(self.mus).max() * 0.89
        pcm = (self.mus.T * 32767).astype(np.int16)
        w = wave.open(path, "wb")
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(pcm.tobytes()); w.close()


def make_score(dur, sections, path, key="Dm", use_arp=True):
    """Cinematic cue: pad intro, harp sparkle, ostinato+riser+hits at each
    section boundary, tutti near end, final impact."""
    s = Score(dur)
    D3, F3, A3 = 146.8, 174.6, 220.0
    D4, F4, A4 = 293.7, 349.2, 440.0
    s.strings([D3 * 0.5, F3 * 0.5, A3 * 0.5], 0, min(5, dur * 0.3), 0.26)
    # low string arp instead of harp/celesta (no piano-like timbre)
    if use_arp:
        arp = [A3 * 0.5, D4 * 0.5, F4 * 0.5, A4 * 0.5, F4 * 0.5, D4 * 0.5, A3 * 0.5, D4 * 0.5]
        for k, t0 in enumerate(np.arange(4, dur - 8, 2.4)):
            s.strings([arp[k % 8]], t0, 1.6, 0.12)
    # per-section: ostinato + riser into boundary + hit ON boundary
    for si, bt in enumerate(sections):
        # ostinato 8ths in last 60% before boundary
        ost = [D3, D3, F3, D3, A3 * 0.5, D3, D3, A4 * 0.5]
        start = max(0.0, bt - min(8.0, dur * 0.2))
        k = 0
        while start + k * 0.5 < bt - 0.1:
            s.note(ost[k % 8], start + k * 0.5, 0.4, 0.16, 0.08)
            k += 1
        if bt - 3.5 > 0:
            s.riser(bt - 3.5, 3.5, 0.28)
            s.timpani_roll(bt - 2.0, 2.0, 0.4)
        s.brass([D4, F4, A4], bt - 0.05, 1.3, 0.3)
        s.timpani(bt, 65, 0.7)
        s.taiko(bt, vol=0.9)
        s.boom(bt - 0.03, 0.8)
    # warm resolve + final hit
    s.strings([D3 * 0.5, F3 * 0.5, A3 * 0.5, D4 * 0.5], max(0, dur - 6), 5.5, 0.28)
    s.boom(dur - 1.5, 1.0); s.taiko(dur - 1.5, f0=85, f1=38, dec=1.0, vol=1.0)
    s.timpani(dur - 1.5, 55, 0.9)
    s.write(path)
    return path
