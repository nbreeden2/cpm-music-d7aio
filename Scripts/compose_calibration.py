"""compose_calibration.py -- Build CALIB.MUS, a ~30-second calibration tone.

Plays A4 (440 Hz) on Part 1 only with timbre 0 (sine wave).  Parts 2-4
are silent so channel 1 (port 19h) shows a clean unmixed sine and
channel 3 (port 1Bh) sits at 0 V.

Purpose: measure the played pitch on the physical D+7A hardware to
verify (or recalibrate) the player's actual sample rate.  The step
value below is encoded for SAMPLE_RATE = 11,169 Hz (calibrated against
A4 measured at 440 +/- 1 Hz on physical hardware, 2026-05-09).

If the played pitch is no longer 440 Hz (e.g., hardware changed,
different system, additional wait states), the actual rate is:

    R_actual = F_measured * 65536 / step

where step = TEST_STEP below.  Then update SAMPLE_RATE in compose.py,
simulate.py, and the other compose_*.py scripts to R_actual.
"""

import os
import struct

from _paths import NEW_DISK

# Calibrated hardware sample rate (verified 2026-05-09).  If you measure
# something other than 440 Hz when you play CALIB.MUS, update this.
SAMPLE_RATE = 11169

# Calibration note: A4 = 440 Hz (standard concert pitch).
TEST_FREQ = 440.0
TEST_STEP = round(TEST_FREQ * 65536 / SAMPLE_RATE)
# = round(440 * 65536 / 11169) = 2582 = 0x0A16

# Duration: aim for ~30.0 sec at SAMPLE_RATE.
# samples_total = TEMPO * DUR * N_REPEATS = 255 * 224 * 6 = 342,720
# 342,720 / 11,169 Hz = 30.68 sec
TEMPO = 255
DUR = 224
N_REPEATS = 6

assert 1 <= TEMPO <= 255 and 1 <= DUR <= 255 and N_REPEATS >= 1


def build_calibration_file() -> bytes:
    """Return the .MUS byte stream for the calibration tone."""
    voice_byte = 0x81           # voice 1 = sine (timbre index 0)
    v12_word = (voice_byte << 8) | voice_byte
    v34_word = (voice_byte << 8) | voice_byte

    cmds = []

    # Command 0: full setup (bits 0x3F = pitches + timbres + tempo).
    cmds.append((0x3F << 8) | DUR)
    cmds.append(TEST_STEP)      # v1: A4
    cmds.append(0)               # v2: silent (step=0 -> wavetable[0] = 0 V)
    cmds.append(0)               # v3: silent
    cmds.append(0)               # v4: silent
    cmds.append(v12_word)        # v1 + v2 timbres
    cmds.append(v34_word)        # v3 + v4 timbres
    cmds.append(TEMPO)           # tempo (low byte = inner-loop reload)

    # Commands 1..N-1: bits=0, just hold the chord for DUR more ticks each.
    for _ in range(N_REPEATS - 1):
        cmds.append((0x00 << 8) | DUR)

    # End-of-song marker (dur=0).
    cmds.append(0x0000)

    return b''.join(struct.pack('<H', w) for w in cmds)


def main():
    samples_total = TEMPO * DUR * N_REPEATS
    sec_at_rate = samples_total / SAMPLE_RATE
    print(f"Test note: {TEST_FREQ} Hz (A4)")
    print(f"Hardware sample rate: {SAMPLE_RATE} Hz")
    print(f"Step value: 0x{TEST_STEP:04X} = {TEST_STEP}")
    print(f"Total samples: {samples_total}")
    print(f"Expected duration: {sec_at_rate:.2f} sec at {SAMPLE_RATE} Hz")
    print()

    data = build_calibration_file()
    path = NEW_DISK / "CALIB.MUS"
    path.write_bytes(data)
    print(f"  wrote {path} ({len(data)} bytes)")


if __name__ == "__main__":
    main()
