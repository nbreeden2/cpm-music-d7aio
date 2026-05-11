"""Inspect voice 3 byte-by-byte to understand the apparent backwards motion."""
from _paths import VOICES_MUS

PAGE = 256
SRC = VOICES_MUS


def s8(b): return b - 256 if b >= 128 else b


data = SRC.read_bytes()
v3 = data[3 * PAGE : 4 * PAGE]
samples = [s8(b) for b in v3]

# print every 8th sample
print("phase  signed  byte")
for i in range(0, PAGE, 8):
    print(f"  {i:3d}    {samples[i]:+4d}    0x{v3[i]:02X}")

print("\n-- Looking for monotonicity breaks (sample[i] vs sample[i-1]) --")
# spot any large jumps
big_jumps = []
for i in range(1, PAGE):
    delta = samples[i] - samples[i - 1]
    if abs(delta) > 8:
        big_jumps.append((i, samples[i - 1], samples[i], delta))
print(f"Found {len(big_jumps)} jumps >8 between adjacent samples")
for j in big_jumps[:20]:
    print(f"  phase {j[0]:3d}: {j[1]:+4d} -> {j[2]:+4d}  (delta {j[3]:+4d})")
