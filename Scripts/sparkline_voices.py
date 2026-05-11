"""Render each voice in VOICES.MUS as an ASCII waveform."""
from _paths import VOICES_MUS

PAGE = 256
SRC = VOICES_MUS


def s8(b): return b - 256 if b >= 128 else b


def ascii_wave(samples, width=64, height=15):
    """Return list of strings forming an ASCII plot of the waveform.

    Each row is enclosed in '|' edge characters so trailing whitespace
    cannot be stripped by a markdown renderer or editor.
    """
    step = len(samples) // width
    pts = [samples[i * step] for i in range(width)]
    rows = []
    # top border
    rows.append("+" + "-" * width + "+")
    for r in range(height, -height - 1, -1):
        thresh_hi = (r + 0.5) * 64 / height
        thresh_lo = (r - 0.5) * 64 / height
        line = ["|"]
        for v in pts:
            if thresh_lo <= v < thresh_hi:
                line.append("*")
            elif r == 0:
                line.append("-")  # zero axis
            else:
                line.append(" ")
        line.append("|")
        rows.append("".join(line))
    # bottom border
    rows.append("+" + "-" * width + "+")
    return rows


data = SRC.read_bytes()
for idx in range(6):
    raw = data[idx * PAGE : (idx + 1) * PAGE]
    samples = [s8(b) for b in raw]
    print(f"\n=== Voice {idx} (page 0x{0x07+idx:02X}) ===")
    for line in ascii_wave(samples):
        print(line)
