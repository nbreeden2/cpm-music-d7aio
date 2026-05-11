"""
compose_octave_trick.py — Build OCTAVE.MUS, a piece that deliberately
exercises the voice-3 (octave-up) and voice-5 (octave + fifth-up) timbres
to get free harmonic doubling out of PLAY.COM's 4-voice engine.

The trick:

    Part 1 (timbre 0 = sine)               -> plays MELODY at written pitch
    Part 2 (timbre 3 = octave-shifter)     -> plays the SAME step values as
                                              Part 1 -> auto-doubles melody
                                              at the octave above
    Part 3 (timbre 0 = sine)               -> plays BASS at written pitch
    Part 4 (timbre 5 = octave+fifth)       -> plays the SAME step values as
                                              Part 3 -> auto-decorates each
                                              bass note with the twelfth
                                              above (octave + fifth)

So the listener hears a 4-pitch chord at every beat — fundamental melody,
melody one octave up, fundamental bass, bass + 19 semitones — even though
PLAY.COM only ever runs 4 voices. The trick exploits the fact that
voices 3 and 5 have weak/missing fundamentals and dominant upper
harmonics, so the perceived pitch of those wavetables is N times the
played pitch (N=2 for V3, N=3 for V5).

Form: AABB, 8-bar A and 8-bar B sections, 3/4 time. Key C major.
Total ~32 bars, ~16 seconds at the chosen tempo.
"""

import struct
import sys

SAMPLE_RATE = 11169  # calibrated to physical D+7A hardware (2026-05-09)


# ----- chromatic note -> phase increment ---------------------------------

def step(note: str) -> int:
    """'G3' / 'F#4' / 'Bb5' -> 16-bit phase increment for SR=SAMPLE_RATE.
    'R' or None = rest (silent, step=0)."""
    if note == 'R' or note is None:
        return 0
    if note[1] in '#b':
        name, octv = note[:2], int(note[2:])
    else:
        name, octv = note[:1], int(note[1:])
    semis = {'C':-9,'C#':-8,'Db':-8,'D':-7,'D#':-6,'Eb':-6,'E':-5,
             'F':-4,'F#':-3,'Gb':-3,'G':-2,'G#':-1,'Ab':-1,
             'A':0,'A#':1,'Bb':1,'B':2}[name] + (octv - 4) * 12
    f = 440.0 * (2 ** (semis / 12.0))
    return round(f * 65536 / SAMPLE_RATE)


# ----- timing / tempo -----------------------------------------------------
#
# 3/4 time, 6 eighths per bar.
# At SR=11169 Hz, eighth = 0.25 sec wants 2792 samples. Closest fit:
# TEMPO=140, EIGHTH=20 -> 2800 samples/eighth = 0.2507 sec/eighth =
# quarter at 119.7 BPM (~0.3% slow vs 120 BPM target).

EIGHTH      =  20
QUARTER     =  2 * EIGHTH        # 40
DOTTED_HALF =  6 * EIGHTH        # 120 = one full bar in 3/4
TEMPO       = 140


# ----- timbre choice -----------------------------------------------------
#
# Critical: this is where the trick lives.
#   v1 = 0 (sine)   -> renders melody at written pitch
#   v2 = 3          -> renders Part 2's step stream an OCTAVE up perceptually
#   v3 = 0 (sine)   -> renders bass at written pitch
#   v4 = 5          -> renders Part 4's step stream an OCTAVE + FIFTH up
#                       perceptually
TIMBRE = (0, 3, 0, 5)


# ----- composition --------------------------------------------------------
#
# Each list of bars is 8 entries; each bar is a list of (note, eighth_count)
# pairs that must sum to 6 (3/4 time, 6 eighths/bar). 'R' = rest.

# Part 1: MELODY (sine, written pitch)
v1_A = [
    [('E4', 2), ('G4', 2), ('C5', 2)],   # bar 1 (I = C):    C arp up
    [('F4', 2), ('A4', 2), ('F4', 2)],   # bar 2 (IV = F):   F-A-F
    [('G4', 2), ('B4', 2), ('D5', 2)],   # bar 3 (V = G):    G arp up
    [('C5', 6)],                          # bar 4 (I = C):    rest on tonic
    [('A4', 2), ('C5', 2), ('E5', 2)],   # bar 5 (vi = Am):  Am arp up
    [('A4', 2), ('F4', 2), ('D4', 2)],   # bar 6 (IV = F):   F-A-F-D motion
    [('G4', 2), ('B4', 2), ('D5', 2)],   # bar 7 (V = G):    G arp up
    [('C5', 6)],                          # bar 8 (I = C):    final tonic
]

# Part 1 B-section: melodic variation, same chord progression
v1_B = [
    [('C5', 2), ('E5', 2), ('G5', 2)],   # bar 9  (I):  ascend higher
    [('A4', 2), ('F4', 2), ('A4', 2)],   # bar 10 (IV): descend then up
    [('B4', 2), ('D5', 2), ('G5', 2)],   # bar 11 (V):  ascend
    [('E5', 6)],                          # bar 12 (I):  hold on E (3rd of C)
    [('E5', 2), ('C5', 2), ('A4', 2)],   # bar 13 (vi): descend
    [('F4', 2), ('A4', 2), ('C5', 2)],   # bar 14 (IV): F arp up
    [('B4', 2), ('D5', 2), ('B4', 2)],   # bar 15 (V):  oscillate
    [('C5', 6)],                          # bar 16 (I):  final
]

# Part 2: SAME step values as Part 1 — but timbre 3 will perceptually
# raise it an octave. We don't write a separate v2 list; we copy v1.
v2_A = v1_A
v2_B = v1_B


# Part 3: BASS (sine, written pitch). Walks chord roots & fifths.
v3_A = [
    [('C3', 2), ('G2', 2), ('C3', 2)],   # bar 1 (I):  C-G-C rocking
    [('F2', 2), ('C3', 2), ('F2', 2)],   # bar 2 (IV): F-C-F
    [('G2', 2), ('D3', 2), ('G2', 2)],   # bar 3 (V):  G-D-G
    [('C3', 6)],                          # bar 4 (I):  hold
    [('A2', 2), ('E3', 2), ('A2', 2)],   # bar 5 (vi): A-E-A
    [('F2', 2), ('C3', 2), ('F2', 2)],   # bar 6 (IV)
    [('G2', 2), ('D3', 2), ('G2', 2)],   # bar 7 (V)
    [('C3', 6)],                          # bar 8 (I)  hold
]

v3_B = [
    [('C3', 2), ('E3', 2), ('G3', 2)],   # bar 9  (I):  walking up
    [('F2', 2), ('A2', 2), ('C3', 2)],   # bar 10 (IV): walking up
    [('G2', 2), ('B2', 2), ('D3', 2)],   # bar 11 (V):  walking up
    [('C3', 6)],                          # bar 12 (I):  hold
    [('A2', 2), ('C3', 2), ('E3', 2)],   # bar 13 (vi): walking up
    [('F2', 2), ('A2', 2), ('C3', 2)],   # bar 14 (IV): walking up
    [('G2', 2), ('B2', 2), ('D3', 2)],   # bar 15 (V):  walking up
    [('C3', 6)],                          # bar 16 (I):  final
]

# Part 4: SAME step values as Part 3 — timbre 5 makes it sound an
# octave + fifth above. So every bass note has a high twelfth-up
# decoration "for free."
v4_A = v3_A
v4_B = v3_B


# ----- expand bar lists into per-eighth pitch arrays ----------------------

def expand(bars):
    flat = []
    for bar_idx, beats in enumerate(bars):
        total = sum(n for _, n in beats)
        if total != 6:
            raise ValueError(f'bar {bar_idx+1} has {total} eighths, expected 6')
        for note, count in beats:
            flat.append((note, count))
    return flat


def to_pitches(events):
    out = []
    for note, count in events:
        s = step(note)
        out.extend([s] * count)
    return out


def section_pitches(v1, v2, v3, v4):
    p1 = to_pitches(expand(v1))
    p2 = to_pitches(expand(v2))
    p3 = to_pitches(expand(v3))
    p4 = to_pitches(expand(v4))
    n = len(p1)
    assert len(p2) == n and len(p3) == n and len(p4) == n
    return p1, p2, p3, p4


A1, A2, A3, A4 = section_pitches(v1_A, v2_A, v3_A, v4_A)
B1, B2, B3, B4 = section_pitches(v1_B, v2_B, v3_B, v4_B)

# AABB form
piece_v1 = A1 + A1 + B1 + B1
piece_v2 = A2 + A2 + B2 + B2
piece_v3 = A3 + A3 + B3 + B3
piece_v4 = A4 + A4 + B4 + B4

assert len(piece_v1) == len(piece_v2) == len(piece_v3) == len(piece_v4)
N = len(piece_v1)
print(f'piece length: {N} eighths = {N // 6} bars '
      f'= {N * 0.25:.1f} seconds at 120 BPM', file=sys.stderr)


# ----- merge into command stream -----------------------------------------

def build_command_stream():
    cmds = []

    # Initial command: set everything (timbres + tempo + initial pitches)
    bits = 0x3F
    chord0 = (piece_v1[0], piece_v2[0], piece_v3[0], piece_v4[0])

    run = 1
    while (run < N
           and piece_v1[run] == chord0[0]
           and piece_v2[run] == chord0[1]
           and piece_v3[run] == chord0[2]
           and piece_v4[run] == chord0[3]):
        run += 1
    dur = run * EIGHTH
    if dur > 255:
        raise RuntimeError(f'first run dur={dur} > 255')

    cmds.append((bits << 8) | dur)
    cmds.extend(chord0)
    v12 = ((0x81 + TIMBRE[1]) << 8) | (0x81 + TIMBRE[0])
    v34 = ((0x81 + TIMBRE[3]) << 8) | (0x81 + TIMBRE[2])
    cmds.append(v12)
    cmds.append(v34)
    cmds.append(TEMPO)

    prev = chord0
    i = run
    while i < N:
        chord = (piece_v1[i], piece_v2[i], piece_v3[i], piece_v4[i])
        run = 1
        while (i + run < N
               and piece_v1[i + run] == chord[0]
               and piece_v2[i + run] == chord[1]
               and piece_v3[i + run] == chord[2]
               and piece_v4[i + run] == chord[3]):
            run += 1
        bits = 0
        pitches = []
        for b in range(4):
            if chord[b] != prev[b]:
                bits |= (1 << b)
                pitches.append(chord[b])
        dur = run * EIGHTH
        if dur > 255:
            raise RuntimeError(f'run dur={dur} > 255 at eighth {i}')
        if bits == 0:
            raise RuntimeError(f'no-change run at eighth {i}')
        cmds.append((bits << 8) | dur)
        cmds.extend(pitches)
        prev = chord
        i += run

    cmds.append(0x0000)
    return cmds


def main():
    cmds = build_command_stream()
    out = bytearray()
    for w in cmds:
        out += struct.pack('<H', w)
    from _paths import NEW_DISK
    out_path = str(NEW_DISK / 'OCTAVE.MUS')
    with open(out_path, 'wb') as f:
        f.write(out)
    print(f'wrote {out_path}: {len(out)} bytes ({len(cmds)} words)',
          file=sys.stderr)


if __name__ == '__main__':
    main()
