"""Procedural sound design for the effort video, synced to timeline.json.

Pure stdlib so it runs anywhere: python3 scripts/sfx.py -> public/sfx.wav
"""

import json
import math
import os
import random
import struct
import wave

SR = 48000
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TL = json.load(open(os.path.join(ROOT, "timeline.json")))
DUR = TL["duration"]
N = int(SR * DUR)
L = [0.0] * N
R = [0.0] * N
random.seed(11)

PROMPT_1 = "redesign the /config menu"
PROMPT_2 = "build an HTML sanitizer"


def put(t, samples, gain=1.0, pan=0.0):
    i0 = int(t * SR)
    ang = (pan + 1) * math.pi / 4
    gl, gr = gain * math.cos(ang), gain * math.sin(ang)
    for k, s in enumerate(samples):
        i = i0 + k
        if 0 <= i < N:
            L[i] += s * gl
            R[i] += s * gr


def bandnoise(n, fc_at, q=0.8):
    """White noise through a state-variable band-pass; fc_at(k) gives cutoff per sample."""
    low = band = 0.0
    out = []
    for k in range(n):
        f = 2 * math.sin(math.pi * min(fc_at(k), SR / 6) / SR)
        x = random.uniform(-1, 1)
        low += f * band
        high = x - low - q * band
        band += f * high
        out.append(band)
    return out


def click(freq=1800, dur=0.05):
    n = int(dur * SR)
    out = []
    for k in range(n):
        tt = k / SR
        s = math.sin(2 * math.pi * freq * tt) * math.exp(-tt / 0.012)
        s += random.uniform(-1, 1) * math.exp(-tt / 0.0015) * 0.6
        out.append(s)
    return out


def key():
    n = int(0.018 * SR)
    fc = random.uniform(2400, 4200)
    noise = bandnoise(n, lambda k: fc, q=0.5)
    thock = random.uniform(160, 220)
    return [
        noise[k] * math.exp(-k / (0.0025 * SR)) * 2.2
        + math.sin(2 * math.pi * thock * k / SR) * math.exp(-k / (0.006 * SR)) * 0.5
        for k in range(n)
    ]


def blip(freq, dur=0.35, tau=0.12):
    n = int(dur * SR)
    out = []
    ph = 0.0
    for k in range(n):
        tt = k / SR
        ph += 2 * math.pi * freq / SR
        a = min(1, tt / 0.003) * math.exp(-tt / tau)
        out.append(a * (math.sin(ph) + 0.25 * math.sin(2 * ph) + 0.08 * math.sin(3 * ph)))
    return out


def pop(f0, f1, dur=0.16):
    n = int(dur * SR)
    out = []
    ph = 0.0
    for k in range(n):
        tt = k / SR
        f = f0 * (f1 / f0) ** min(1, tt / 0.06)
        ph += 2 * math.pi * f / SR
        a = min(1, tt / 0.002) * math.exp(-tt / 0.045)
        out.append(a * math.sin(ph))
    return out


def chime(freqs, dur=1.8, tau=0.7):
    n = int(dur * SR)
    out = [0.0] * n
    for j, f in enumerate(freqs):
        ph1 = ph2 = 0.0
        g = 1.0 / (1 + j * 0.35)
        for k in range(n):
            tt = k / SR
            ph1 += 2 * math.pi * f / SR
            ph2 += 2 * math.pi * f * 2.76 / SR
            a = min(1, tt / 0.004) * math.exp(-tt / tau)
            out[k] += g * a * (math.sin(ph1) + 0.18 * math.sin(ph2) * math.exp(-tt / 0.15))
    return out


def whoosh(dur, f0, f1, peak=0.6, q=0.9):
    n = int(dur * SR)
    p = math.log(0.5) / math.log(peak)
    noise = bandnoise(n, lambda k: f0 * (f1 / f0) ** (k / n), q=q)
    return [noise[k] * math.sin(math.pi * (k / n) ** p) ** 2 * 1.6 for k in range(n)]


def riser(dur, f0=260, f1=5200):
    n = int(dur * SR)
    noise = bandnoise(n, lambda k: f0 * (f1 / f0) ** (k / n), q=0.6)
    out = []
    ph = 0.0
    for k in range(n):
        x = k / n
        ph += 2 * math.pi * (180 * (4.0 ** x)) / SR
        tail = min(1, (n - k) / (0.02 * SR))
        out.append((noise[k] * 1.3 + 0.35 * math.sin(ph)) * x ** 2.2 * tail)
    return out


def impact(dur=1.2):
    n = int(dur * SR)
    out = []
    ph = 0.0
    lp = 0.0
    for k in range(n):
        tt = k / SR
        f = 38 + 60 * math.exp(-tt / 0.07)
        ph += 2 * math.pi * f / SR
        lp += 0.08 * (random.uniform(-1, 1) - lp)
        s = math.sin(ph) * math.exp(-tt / 0.38)
        s += lp * math.exp(-tt / 0.05) * 3.0
        out.append(math.tanh(1.6 * s))
    return out


def scratch(dur):
    """Pencil-on-paper texture for the sketch draw-on."""
    n = int(dur * SR)
    noise = bandnoise(n, lambda k: 3800 + 1400 * math.sin(k / SR * 23), q=0.35)
    out = []
    for k in range(n):
        tt = k / SR
        stroke = max(0.0, math.sin(tt * 2 * math.pi * 7.5)) ** 3
        env = math.sin(math.pi * k / n)
        out.append(noise[k] * stroke * env * 1.4)
    return out


def pad():
    chord_a = [146.83, 220.0, 293.66, 369.99, 554.37]
    chord_b = [146.83, 220.0, 293.66, 440.0, 587.33, 739.99]
    t_switch = TL["s4"]["irisOut"]

    duck, lift = TL["s4"]["merge"], TL["s4"]["irisOut"]

    def vol(t):
        v = min(1.0, t / 1.4)
        if duck < t < lift:
            v *= 1 - 0.65 * min(1, (t - duck) / 0.3)
        if t >= lift:
            v = 0.35 + 0.8 * min(1, (t - lift) / 0.5)
        if t > DUR - 1.2:
            v *= max(0.0, 1 - (t - (DUR - 1.2)) / 1.2)
        return v

    phl = [0.0] * len(chord_a)
    phr = [0.0] * len(chord_a)
    for i in range(N):
        t = i / SR
        v = vol(t) * 0.028
        if v <= 0:
            continue
        mix = min(1, max(0, (t - t_switch) / 0.35))
        trem = 0.85 + 0.15 * math.sin(2 * math.pi * 0.23 * t)
        sl = sr = 0.0
        for j, f in enumerate(chord_a):
            phl[j] += 2 * math.pi * (f - 0.6) / SR
            phr[j] += 2 * math.pi * (f + 0.6) / SR
            g = (1 - mix) / (1 + j * 0.5)
            sl += g * math.sin(phl[j])
            sr += g * math.sin(phr[j])
        if mix > 0:
            for j, f in enumerate(chord_b):
                g = mix / (1 + j * 0.45)
                sl += g * math.sin(2 * math.pi * (f - 0.5) * t)
                sr += g * math.sin(2 * math.pi * (f + 0.5) * t)
        L[i] += sl * v * trem
        R[i] += sr * v * trem


s1, s2, s3, s4 = TL["s1"], TL["s2"], TL["s3"], TL["s4"]

pad()

# scene 1
put(s1["spark"], chime([1318.5, 1975.5, 2637.0], dur=1.6, tau=0.5), 0.10, 0.0)
put(s1["spark"], whoosh(0.9, 200, 1400, peak=0.3), 0.10)
for i, w in enumerate([s1["line1"], s1["line1"] + 0.09, s1["line2"], s1["line2"] + 0.09]):
    put(w, whoosh(0.28, 500, 2400, peak=0.45), 0.10, -0.3 + i * 0.2)
    put(w + 0.12, blip(98 if i < 2 else 110, dur=0.3, tau=0.08), 0.22)
put(s1["bar"], pop(420, 180), 0.25)
put(s1["sparkDock"], whoosh(0.5, 2600, 700, peak=0.5), 0.12, -0.4)
put(s1["sparkDock"] + 0.48, click(2400), 0.18, -0.5)

for k in range(len(PROMPT_1)):
    tk = s1["typeStart"] + (s1["typeEnd"] - s1["typeStart"]) * k / len(PROMPT_1)
    put(tk + random.uniform(-0.006, 0.006), key(), random.uniform(0.16, 0.26), random.uniform(-0.3, 0.3))

put(s1["exit"], whoosh(0.42, 600, 3200, peak=0.4), 0.16)
put(s1["flipStart"], whoosh(s1["flipEnd"] - s1["flipStart"], 400, 2200, peak=0.55), 0.2, 0.2)

# scene 2
put(s2["drawOn"] + 0.05, scratch(1.2), 0.12, 0.1)
notes = [659.25, 739.99, 880.0, 987.77]
for i, st in enumerate(s2["steps"]):
    put(st, click(1600 + i * 250), 0.28, -0.1 + i * 0.07)
    put(st + 0.01, blip(notes[i], dur=0.5, tau=0.14), 0.16, -0.1 + i * 0.07)
    if i in (1, 2):
        put(st + 0.08, whoosh(0.5, 1800, 7000, peak=0.35, q=0.5), 0.07)
arrive_max = s2["steps"][3] + 0.2
put(arrive_max, chime([987.77, 1479.98, 1975.53], dur=1.8, tau=0.6), 0.16, 0.1)
for i, c in enumerate(s2["callouts"]):
    put(c, pop(900 + i * 180, 380 + i * 80), 0.32, [0.4, -0.5, 0.3][i])
put(s2["exit"], whoosh(0.5, 3000, 500, peak=0.45), 0.2)

# scene 3
for k in range(6):
    put(s3["rewind"] + k * 0.035, click(2600 - k * 260, dur=0.03), 0.14 * (1 - k * 0.1), 0.3 - k * 0.1)
for k in range(len(PROMPT_2)):
    tk = s3["retypeStart"] + (s3["retypeEnd"] - s3["retypeStart"]) * k / len(PROMPT_2)
    put(tk + random.uniform(-0.004, 0.004), key(), random.uniform(0.14, 0.22), random.uniform(-0.3, 0.3))
for i in range(5):
    put(s3["enter"] + 0.15 + i * 0.06, click(900 + i * 60, dur=0.04), 0.06, (i - 2) * 0.3)
put(s3["lowResult"], pop(1200, 520), 0.3, -0.5)
put(s3["lowResult"] + 0.02, blip(880, dur=0.4), 0.1, -0.5)
for i in range(1, 5):
    put(s3["lowResult"] + 0.1 + i * 0.05, blip(146.8, dur=0.2, tau=0.05), 0.2, (i - 2) * 0.3)
put(s3["climb"] - 0.05, riser(s3["arrive"] - s3["climb"] + 0.05), 0.22)
for i, c in enumerate(s3["chips"]):
    put(c, pop(1500 + i * 120, 900), 0.14, -0.4 + i * 0.27)
put(s3["arrive"], click(2000), 0.22)
pop_notes = [1046.5, 1318.5, 1568.0, 2093.0]
for i, pp in enumerate(s3["pops"]):
    put(pp, pop(pop_notes[i] * 0.9, pop_notes[i] * 0.45), 0.34, -0.25 + i * 0.25)
    put(pp + 0.005, blip(pop_notes[i] / 2, dur=0.4, tau=0.12), 0.1, -0.25 + i * 0.25)
put(s3["pops"][3] + 0.08, chime([523.25, 783.99, 1046.5, 1318.5], dur=2.0, tau=0.8), 0.14)

# transition + finale
put(s4["merge"] - 0.05, whoosh(0.3, 3500, 800, peak=0.8), 0.18)
put(s4["irisIn"], whoosh(s4["irisOut"] - s4["irisIn"] + 0.05, 300, 4200, peak=0.85, q=0.7), 0.32)
put(s4["irisOut"] - 0.01, impact(), 0.34)
put(s4["irisOut"], whoosh(0.7, 5000, 300, peak=0.15, q=0.6), 0.14)
for i in range(4):
    put(s4["setup"] + i * 0.07 + 0.1, blip(220 * (1.5 if i % 2 else 1), dur=0.25, tau=0.05), 0.08)
put(s4["line1"] + 0.12, blip(73.4, dur=0.7, tau=0.25), 0.35)
put(s4["line1"] + 0.12, click(900), 0.08)
put(s4["line2"] + 0.12, blip(82.4, dur=0.7, tau=0.25), 0.35)
put(s4["line2"] + 0.12, click(1100), 0.08)
put(s4["mini"], pop(700, 350), 0.14)
put(s4["miniTravel"], riser(s4["miniArrive"] - s4["miniTravel"], 600, 3800), 0.1)
put(s4["miniArrive"], chime([587.33, 880.0, 1174.66, 1479.98], dur=1.1, tau=0.5), 0.2)
put(s4["miniArrive"], click(2200), 0.2)
put(s4["footer"], pop(1100, 600), 0.1, -0.6)

# master: normalize, soft clip, short fade-out
# DRIVE sets loudness, CEIL leaves headroom for AAC overshoot (target -14 LUFS, true peak <= -1 dBFS)
DRIVE = 1.8
CEIL = 0.76
peak = max(max(abs(x) for x in L), max(abs(x) for x in R)) or 1.0
fade_n = int(0.25 * SR)
os.makedirs(os.path.join(ROOT, "public"), exist_ok=True)
path = os.path.join(ROOT, "public", "sfx.wav")
with wave.open(path, "wb") as wf:
    wf.setnchannels(2)
    wf.setsampwidth(2)
    wf.setframerate(SR)
    frames = bytearray()
    drive = math.tanh(DRIVE)
    for i in range(N):
        g = 1.0 if i < N - fade_n else (N - i) / fade_n
        l = math.tanh(DRIVE * L[i] / peak) / drive * CEIL * g
        r = math.tanh(DRIVE * R[i] / peak) / drive * CEIL * g
        frames += struct.pack("<hh", int(l * 32767), int(r * 32767))
    wf.writeframes(bytes(frames))
print("wrote", path, f"{DUR}s peak(pre)={peak:.3f}")
