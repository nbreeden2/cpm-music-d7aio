"""compose_doremi.py — Build DOREMI.MUS, a diatonic ascent on voice 1
covering 6 full octaves plus a tonic landing.

Walks Do-Re-Mi-Fa-Sol-La-Ti (C-D-E-F-G-A-B) ascending from C1 through
B6, then resolves on C7. 43 notes total, 1 second per note, 43 seconds
total.

Range reasoning:
  - C1 (32.7 Hz) is the lowest cleanly scopable C. Below ~30 Hz the
    period exceeds typical scope sweep windows and small speakers
    can't reproduce.
  - C7 (2093 Hz) is a safe upper limit. At SR=11169 Hz, C7 yields
    ~5.3 samples per wavetable cycle; higher notes shrink that
    quickly and the output starts looking like a stair-stepped
    sawtooth on the scope.  Stopping at C7 keeps every note clean.

Voice routing (same as VOICE1.MUS / OCTAVES.MUS):
  v1 = sine timbre, plays the test note  -> DAC port 19h
  v2-v4 = silent (step=0)                 -> DAC port 1Bh = 0 V
"""

import struct

from _paths import VOICE_TESTS, NEW_DISK

VOICE_TESTS.mkdir(exist_ok=True)
NEW_DISK.mkdir(exist_ok=True)

SAMPLE_RATE = 11169  # calibrated to physical D+7A hardware (2026-05-09)

# Diatonic notes in Do-Re-Mi-Fa-Sol-La-Ti = C major scale
DIATONIC = ['C', 'D', 'E', 'F', 'G', 'A', 'B']

# 1 sec per note at SR=11169 Hz wants 11169 samples per command.
# 153 * 73 = 11169 exactly -> 1.0000 sec/note.
TEMPO = 153
DUR = 73

# Voice 1 = sine timbre (timbre 0). Other voices share the timbre but silent.
TIMBRE = 0


def step_for(name: str, octave: int) -> int:
    """Equal-temperament A=440 step value at Fs=SAMPLE_RATE."""
    semitone = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}[name]
    midi = 12 * (octave + 1) + semitone        # C4 = MIDI 60, A4 = MIDI 69
    freq = 440.0 * 2 ** ((midi - 69) / 12)
    return round(freq * 65536 / SAMPLE_RATE)


def main():
    # Build the note list: 6 full octaves (C1..B6) + closing C7
    notes = []
    for octave in range(1, 7):
        for name in DIATONIC:
            notes.append((name, octave))
    notes.append(('C', 7))    # final tonic, resolves the scale

    voice_byte = 0x81 + TIMBRE
    v12_word = (voice_byte << 8) | voice_byte
    v34_word = (voice_byte << 8) | voice_byte

    cmds = []

    # First command: set everything (4 pitches + 2 timbre words + tempo)
    first_step = step_for(*notes[0])
    cmds.append((0x3F << 8) | DUR)
    cmds.append(first_step)
    cmds.append(0)            # v2 silent
    cmds.append(0)            # v3 silent
    cmds.append(0)            # v4 silent
    cmds.append(v12_word)
    cmds.append(v34_word)
    cmds.append(TEMPO)

    # Subsequent commands: only v1's pitch changes
    for name, octave in notes[1:]:
        s = step_for(name, octave)
        cmds.append((0x01 << 8) | DUR)
        cmds.append(s)

    # End-of-song marker
    cmds.append(0x0000)

    data = b''.join(struct.pack('<H', w) for w in cmds)
    for out_dir in (VOICE_TESTS, NEW_DISK):
        out_path = out_dir / "DOREMI.MUS"
        out_path.write_bytes(data)
        print(f"wrote {out_path}: {len(data)} bytes ({len(cmds)} words)")

    sec_per_note = TEMPO * DUR / SAMPLE_RATE
    print(f"{len(notes)} notes x {sec_per_note:.1f} sec each "
          f"= {len(notes) * sec_per_note:.1f} sec total")
    print()
    print("schedule (showing edges of each octave):")
    for i, (name, octv) in enumerate(notes):
        s = step_for(name, octv)
        f_hz = s * SAMPLE_RATE / 65536
        is_edge = name in ('C', 'B') or i == 0 or i == len(notes) - 1
        if is_edge:
            print(f"  t={i*sec_per_note:5.1f}s   {name}{octv:<2}  "
                  f"step=0x{s:04X}  {f_hz:8.2f} Hz")


if __name__ == "__main__":
    main()
