"""Plot all 6 VOICES.MUS wavetables stacked, sharing the phase axis."""
import matplotlib.pyplot as plt

from _paths import VOICES_MUS, VOICES_ANALYSIS

PAGE = 256
SRC = VOICES_MUS
OUT_DIR = VOICES_ANALYSIS
OUT_DIR.mkdir(exist_ok=True)


def s8(b): return b - 256 if b >= 128 else b


data = SRC.read_bytes()
tables = [
    [s8(b) for b in data[i * PAGE : (i + 1) * PAGE]]
    for i in range(len(data) // PAGE)
]

# stacked subplots, shared x-axis
fig, axes = plt.subplots(
    nrows=len(tables),
    ncols=1,
    sharex=True,
    figsize=(12, 9),
)
fig.suptitle("VOICES.MUS — six 256-byte wavetables, signed 8-bit PCM", fontsize=13)

# Draw 0..256 inclusive — the value at x=256 is the same as x=0 (start of
# next cycle). This makes the periodic loop closure visually obvious.
x = list(range(PAGE + 1))
labels = [
    "Voice 0 (page 0x07) — sine",
    "Voice 1 (page 0x08) — even-harmonic double-hump",
    "Voice 2 (page 0x09) — skewed saw-ish",
    "Voice 3 (page 0x0A) — octave-shifter (no fundamental)",
    "Voice 4 (page 0x0B) — square",
    "Voice 5 (page 0x0C) — three-cycle hybrid",
]

for ax, samples, label in zip(axes, tables, labels):
    closed = samples + [samples[0]]   # append start sample so loop closes visually
    ax.plot(x, closed, linewidth=1.2)
    ax.axhline(0, color="gray", linewidth=0.5, linestyle="--")
    ax.set_ylim(-70, 70)
    ax.set_yticks([-60, 0, 60])
    ax.set_ylabel("amp", fontsize=8)
    ax.grid(True, alpha=0.3)
    ax.text(
        0.01, 0.95, label,
        transform=ax.transAxes,
        fontsize=9,
        va="top",
        ha="left",
        bbox=dict(boxstyle="round,pad=0.25", facecolor="white", edgecolor="lightgray"),
    )

axes[-1].set_xlabel("phase (table offset 0..255; sample at x=256 = next cycle's sample 0)")
axes[-1].set_xlim(0, PAGE)

fig.tight_layout(rect=[0, 0, 1, 0.97])

png = OUT_DIR / "voices_stacked.png"
svg = OUT_DIR / "voices_stacked.svg"
fig.savefig(png, dpi=140)
fig.savefig(svg)
print(f"wrote {png}")
print(f"wrote {svg}")
