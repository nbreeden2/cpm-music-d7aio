"""Check the wrap-point continuity of every voice.

When PLAY.COM plays a note, the phase accumulator goes 0..255..0..255 forever.
The audible 'jump' between successive cycles is |s[0] - s[255]| — that's how far
the DAC moves when the table wraps. Anything more than a few units could pop.
"""
from _paths import VOICES_MUS

PAGE = 256
SRC = VOICES_MUS

def s8(b): return b - 256 if b >= 128 else b

data = SRC.read_bytes()

print(f"{'V':<2} {'s[0]':>6} {'s[1]':>6} {'s[127]':>7} {'s[128]':>7} {'s[254]':>7} {'s[255]':>7}   "
      f"{'wrap |s[0]-s[255]|':<20} {'max neighbour delta'}")
print("-" * 110)
for idx in range(6):
    s = [s8(b) for b in data[idx * PAGE : (idx + 1) * PAGE]]
    # max delta between adjacent samples (over the full periodic loop incl wrap)
    max_d = 0
    where = -1
    for i in range(PAGE):
        d = abs(s[(i + 1) % PAGE] - s[i])
        if d > max_d:
            max_d = d
            where = i
    wrap = abs(s[0] - s[255])
    print(f"{idx:<2} {s[0]:>+6d} {s[1]:>+6d} {s[127]:>+7d} {s[128]:>+7d} {s[254]:>+7d} {s[255]:>+7d}   "
          f"{wrap:>3d} {' (' + str(s[0]) + 'to' + str(s[255]) + ')':<14}      "
          f"{max_d} at i={where}")
