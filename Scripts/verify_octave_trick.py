"""Spectral verification that OCTAVE.MUS exhibits the V3/V5 octave-shift trick.

At t=0..0.5s the piece plays:
    Part 1 (V0 sine):       E4    -> we should see ~330 Hz peak
    Part 2 (V3 oct-shift):  E4    -> wave content sounds at ~660 Hz (E5)
    Part 3 (V0 sine):       C3    -> we should see ~131 Hz peak
    Part 4 (V5 12th-shift): C3    -> wave content sounds at ~392 Hz (G4)
"""
import math
import struct
import wave

from _paths import VOICE_TESTS

SR = 11169  # calibrated to physical D+7A hardware (2026-05-09)

# Read first 4000 samples (0.5 sec) of the simulated WAV
with wave.open(str(VOICE_TESTS / 'OCTAVE_sim.wav'), 'rb') as w:
    n_total = w.getnframes()
    raw = w.readframes(min(4000, n_total))
samples = list(struct.unpack(f'<{len(raw)//2}h', raw))
samples = samples[:4000]
N = len(samples)
print(f'analyzing first {N} samples ({N/SR:.2f} sec) of OCTAVE_sim.wav')

# DFT magnitudes for frequencies of interest (Goertzel-style)
def goertzel_mag(samples, target_hz):
    omega = 2 * math.pi * target_hz / SR
    cos_w = math.cos(omega)
    coeff = 2 * cos_w
    s_prev = s_prev2 = 0.0
    for s in samples:
        s_new = s + coeff * s_prev - s_prev2
        s_prev2, s_prev = s_prev, s_new
    return math.sqrt(s_prev2 ** 2 + s_prev ** 2 - coeff * s_prev * s_prev2) / N

targets = [
    ('C3 fundamental (Part 3 V0 bass)',     131.0),
    ('E4 fundamental (Part 1 V0 melody)',   330.0),
    ('G4 = C3 * 3 (Part 4 V5 trick)',       392.0),
    ('E5 = E4 * 2 (Part 2 V3 trick)',       659.0),
    # baselines: pitches we should NOT see strongly
    ('100 Hz (no signal expected)',         100.0),
    ('500 Hz (no signal expected)',         500.0),
    ('1000 Hz (no signal expected)',       1000.0),
]

print(f'\n{"target":50s}{"magnitude":>12s}')
print('-' * 65)
for label, hz in targets:
    mag = goertzel_mag(samples, hz)
    bar = '#' * int(mag / 50)
    print(f'{label:50s}{mag:12.1f}  {bar}')
