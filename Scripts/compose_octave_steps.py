"""compose_octave_steps.py — Build OCTAVES.MUS, a power-of-2 octave sweep
on voice 1 (sine timbre) covering the player's full practical range.

Each note plays for 5 seconds. The seven steps are exact bit-shifts of one
another (0x0100, 0x0200, 0x0400, ..., 0x4000), so each note doubles the
previous frequency precisely. Easy to verify on a scope by halving the
sweep rate at every transition.

Pitch list (at SR=11169 Hz):
    step=0x0100  ->    43.63 Hz   (~F1)
    step=0x0200  ->    87.27 Hz   (~F2)
    step=0x0400  ->   174.5  Hz   (~F3)
    step=0x0800  ->   349.0  Hz   (~F4)
    step=0x1000  ->   698.1  Hz   (~F5)
    step=0x2000  ->  1396.1  Hz   (~F6)
    step=0x4000  ->  2792.3  Hz   (~F7, last clean sine before Nyquist degrades it)

Why these limits:
    Lowest:  below ~30 Hz the cycle period exceeds typical scope sweep
             windows and small speakers can't reproduce.
    Highest: step=0x8000 (Nyquist = SR/2 = 5584.5 Hz) makes the sine
             table land on its zero crossings -> silent. step=0x6000
             gives 2.67 samples/cycle which looks like jagged sawtooth
             on scope. step=0x4000 gives exactly 4 samples/cycle -- a
             clean 4-point sine -- regardless of SR.

Voice routing:
    v1 = sine timbre, plays the test note     -> DAC port 19h shows it
    v2 = silent (step=0)                       -> DAC port 19h shows v1 alone
    v3 = silent                                -> DAC port 1Bh = 0 V steady
    v4 = silent                                -> DAC port 1Bh = 0 V steady
"""

import struct

from _paths import VOICE_TESTS, NEW_DISK

VOICE_TESTS.mkdir(exist_ok=True)
NEW_DISK.mkdir(exist_ok=True)

SAMPLE_RATE = 11169  # calibrated to physical D+7A hardware (2026-05-09)

# Power-of-2 octave sweep, 7 notes
STEPS = [
    0x0100,   # 31.25 Hz
    0x0200,   # 62.5 Hz
    0x0400,   # 125 Hz
    0x0800,   # 250 Hz
    0x1000,   # 500 Hz
    0x2000,   # 1000 Hz
    0x4000,   # 2000 Hz
]

# 5 sec per note at SR=11169 Hz wants 55845 samples per command.
# 255 * 219 = 55845 exactly -> 5.0000 sec/note.
TEMPO = 255
DUR = 219

# Voice 1 uses sine (timbre 0). Other voices share the timbre but are silent.
TIMBRE = 0


def main():
    voice_byte = 0x81 + TIMBRE
    v12_word = (voice_byte << 8) | voice_byte
    v34_word = (voice_byte << 8) | voice_byte

    cmds = []

    # First command: bits=0x3F (set all 4 pitches + 2 timbre words + tempo).
    # Voice 1 plays first step; others silent.
    cmds.append((0x3F << 8) | DUR)
    cmds.append(STEPS[0])    # v1 pitch
    cmds.append(0)           # v2 silent
    cmds.append(0)           # v3 silent
    cmds.append(0)           # v4 silent
    cmds.append(v12_word)
    cmds.append(v34_word)
    cmds.append(TEMPO)

    # Subsequent commands: bits=0x01 (only v1 pitch changes), one per octave.
    for s in STEPS[1:]:
        cmds.append((0x01 << 8) | DUR)
        cmds.append(s)

    # End-of-song
    cmds.append(0x0000)

    data = b''.join(struct.pack('<H', w) for w in cmds)
    for out_dir in (VOICE_TESTS, NEW_DISK):
        out_path = out_dir / "OCTAVES.MUS"
        out_path.write_bytes(data)
        print(f"wrote {out_path}: {len(data)} bytes")
    print(f"{len(STEPS)} notes x {TEMPO * DUR / SAMPLE_RATE:.1f} sec each = "
          f"{len(STEPS) * TEMPO * DUR / SAMPLE_RATE:.1f} sec total")
    print()
    print("note schedule:")
    for i, s in enumerate(STEPS):
        f = s * SAMPLE_RATE / 65536
        print(f"  t={i*5:5.1f}s   step=0x{s:04X} ({s:>5d})   freq={f:7.2f} Hz   "
              f"period={1000/f:6.2f} ms")


if __name__ == "__main__":
    main()
