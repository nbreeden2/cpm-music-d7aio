"""compose_voice_tests.py — Build 6 .MUS test files, one per timbre.

Each file plays a steady A4 (440 Hz) on Part 1 only, using a single
timbre, for ~30 seconds. Parts 2-4 are silent (step=0). This means:

    DAC port 19h (channel 1) = Part 1 alone -> the timbre's waveform
    DAC port 1Bh (channel 3) = silent       -> steady 0 V reference

So an o-scope probe on port 19h shows the unmixed wavetable being
read out at 440 Hz (period ~2.27 ms). At 2 ms/div sweep, you see
~11 cycles per screen — easy to identify each timbre by shape.

File mapping (1-indexed file name, 0-indexed timbre):
    VOICE1.MUS -> timbre 0 (sine)
    VOICE2.MUS -> timbre 1 (even-harmonic double-hump)
    VOICE3.MUS -> timbre 2 (skewed saw)
    VOICE4.MUS -> timbre 3 (octave-shifter)
    VOICE5.MUS -> timbre 4 (square)
    VOICE6.MUS -> timbre 5 (three-cycle hybrid)
"""

import struct

from _paths import VOICE_TESTS, NEW_DISK

VOICE_TESTS.mkdir(exist_ok=True)
NEW_DISK.mkdir(exist_ok=True)

# Test note: A4 = 440 Hz, step = round(440 * 65536 / SAMPLE_RATE).
SAMPLE_RATE = 11169  # calibrated to physical D+7A hardware (2026-05-09)
TEST_FREQ = 440.0
TEST_STEP = round(TEST_FREQ * 65536 / SAMPLE_RATE)
assert TEST_STEP == 0x0A16   # = 2582 at 11169 Hz (same as CALIB.MUS)

# Each command runs for tempo*dur samples. At SR=11169 Hz:
#   tempo=240, dur=250 -> 60000 samples = 5.37 sec per command
# Six commands -> 32.2 sec total (target was "~30 seconds").
TEMPO = 240
DUR = 250
N_REPEATS = 6

assert 1 <= TEMPO <= 255 and 1 <= DUR <= 255


def build_voice_test(timbre_idx: int) -> bytes:
    """Return the .MUS byte stream for one timbre's test file."""
    voice_byte = 0x81 + timbre_idx
    v12_word = (voice_byte << 8) | voice_byte    # high = v2, low = v1
    v34_word = (voice_byte << 8) | voice_byte    # high = v4, low = v3

    cmds = []

    # Command 0: set everything (bits 0x3F = pitches + timbres + tempo)
    cmds.append((0x3F << 8) | DUR)
    cmds.append(TEST_STEP)    # v1: A3
    cmds.append(0)            # v2: silent (step=0 -> wavetable[0]=0 V)
    cmds.append(0)            # v3: silent
    cmds.append(0)            # v4: silent
    cmds.append(v12_word)     # v1, v2 timbres (both unused for v2 since silent)
    cmds.append(v34_word)     # v3, v4 timbres (both unused, both silent)
    cmds.append(TEMPO)        # tempo (low byte used by the inner loop)

    # Commands 1..N-1: bits=0, just play current chord for DUR more ticks
    for _ in range(N_REPEATS - 1):
        cmds.append((0x00 << 8) | DUR)

    # End-of-song (cmd word with dur=0)
    cmds.append(0x0000)

    return b''.join(struct.pack('<H', w) for w in cmds)


def main():
    seconds_per_cmd = TEMPO * DUR / SAMPLE_RATE
    total_sec = seconds_per_cmd * N_REPEATS
    print(f"test note: {TEST_FREQ} Hz (A4), step=0x{TEST_STEP:04X}")
    print(f"each command: {seconds_per_cmd:.2f} sec, {N_REPEATS} commands "
          f"-> {total_sec:.2f} sec total")
    print()

    for timbre in range(6):
        data = build_voice_test(timbre)
        file_idx = timbre + 1
        for out_dir in (VOICE_TESTS, NEW_DISK):
            path = out_dir / f"VOICE{file_idx}.MUS"
            path.write_bytes(data)
            print(f"  wrote {path}  ({len(data)} bytes, timbre {timbre})")


if __name__ == "__main__":
    main()
