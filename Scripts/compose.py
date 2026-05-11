"""
compose.py - Build a .MUS song file from scratch.

The piece: an original 4-voice baroque-style minuet in G major.

Format reminders (all 16-bit little-endian words pushed/popped via the song
stack):

    word 0:  cmd       lo = duration (samples / 256 * tempo);
                       hi = bitmap of which params follow
                       (lo == 0  => end-of-song)
    if bit 0 set:  word -> v1 phase increment
    if bit 1 set:  word -> v2 phase increment
    if bit 2 set:  word -> v3 phase increment
    if bit 3 set:  word -> v4 phase increment
    if bit 4 set:  two words -> (v2<<8|v1) and (v4<<8|v3) timbre bytes
                                voice-byte encoding = 0x81 + table_index, 0..5
    if bit 5 set:  word -> tempo (low byte = LD B,n inner-loop reload)

Voice mixing on the Cromemco D+7A:
    DAC port 19h (channel 1) <- v1 + v2
    DAC port 1Bh (channel 3) <- v3 + v4
    Both DAC outputs sum into a single speaker.

Each voice has one of 6 timbres from VOICES.MUS:
    0 = sine   1 = ?   2 = ?   3 = ?   4 = ?   5 = ?
"""

import struct
import sys

SAMPLE_RATE = 11169  # calibrated to physical D+7A hardware (2026-05-09)

# ----- chromatic note -> phase increment ---------------------------------

def step(note: str) -> int:
    """'G3' / 'F#4' / 'Bb5' -> 16-bit phase increment for SR=11169 Hz."""
    if note == 'R' or note is None:
        return 0  # rest / silence

    # parse name + octave, allowing # or b
    if note[1] in '#b':
        name, octv = note[:2], int(note[2:])
    else:
        name, octv = note[:1], int(note[1:])

    semis = {'C':-9,'C#':-8,'Db':-8,'D':-7,'D#':-6,'Eb':-6,'E':-5,
             'F':-4,'F#':-3,'Gb':-3,'G':-2,'G#':-1,'Ab':-1,
             'A':0,'A#':1,'Bb':1,'B':2}[name] + (octv - 4) * 12
    f = 440.0 * (2 ** (semis / 12.0))
    return round(f * 65536 / SAMPLE_RATE)


# ----- compose --------------------------------------------------------------
#
# Smallest unit = an EIGHTH note. The piece is in 3/4 time, six eighths per
# bar.  Target: eighth = 0.25 sec, quarter = 0.5 sec = 120 BPM (minuet pace).
#
# At SR=11169 Hz, an eighth = 0.25 sec wants 2792 samples. Closest integer
# pair within byte range:
#   tempo (B reload) = 140   ->   duration = 20 ticks per eighth
# Total samples per eighth = 140 * 20 = 2800 -> 0.2507 sec/eighth, 119.7 BPM
# (~0.3% slow vs 120 BPM target -- inaudible).

EIGHTH = 20
QUARTER = 2 * EIGHTH       # 40
DOTTED_QTR = 3 * EIGHTH    # 60
HALF = 4 * EIGHTH          # 80
DOTTED_HALF = 6 * EIGHTH   # 120  (one bar in 3/4)
TEMPO = 140

# 4 voice timbres -- all six are available (0..5). Pick four contrasting ones.
TIMBRE = (0, 1, 2, 3)   # voice index for v1..v4


# Each entry below is one bar of three beats, each beat a list of
# (note_name, eighth_count) pairs. 'R' = rest. The four lists are the four
# voices: v1=soprano, v2=alto, v3=tenor, v4=bass.
#
# Soprano carries the tune. Bass walks through the chord roots. The two inner
# voices (alto, tenor) provide chord-tone padding -- usually whole-bar holds.

# A section -- 8 bars
v1_A = [
    # bar 1 (I=G):    D5 D5 D5 (each quarter)... let's mix it up
    [('D5',2),('B4',2),('G4',2)],            # bar 1: I, descending arp
    [('A4',2),('F#4',2),('D4',2)],           # bar 2: V, D arp going down
    [('G4',2),('B4',2),('D5',2)],            # bar 3: I, ascending arp
    [('D5',2),('C5',2),('B4',2)],            # bar 4: V7, C# absent (just C nat? No, V is D maj so C#) -- here we go to V via C nat as a passing tone (Cmaj7 sound)
    [('B4',2),('A4',2),('G4',2)],            # bar 5: I, descending stepwise
    [('A4',2),('B4',2),('C5',2)],            # bar 6: IV, ascending
    [('B4',2),('A4',2),('F#4',2)],           # bar 7: V
    [('G4',6)],                              # bar 8: I, dotted half (whole bar)
]
v2_A = [
    [('B4',6)],                              # bar 1: B (3rd of G)
    [('A4',6)],                              # bar 2: A (5th of D)
    [('B4',6)],                              # bar 3: B
    [('A4',6)],                              # bar 4: A
    [('D5',6)],                              # bar 5: D (5th of G)
    [('E4',6)],                              # bar 6: E (3rd of C)
    [('D4',6)],                              # bar 7: A above? -- pick D (5th of G as upper neighbor) -- err let me make it A (5th of D)
    [('B4',6)],                              # bar 8: B (3rd of G)
]
v3_A = [
    [('G4',6)],                              # bar 1: G root doubled up
    [('F#4',6)],                             # bar 2: F# (3rd of D)
    [('D4',6)],                              # bar 3: D
    [('F#4',6)],                             # bar 4: F#
    [('B3',6)],                              # bar 5: B (3rd of G)
    [('C4',6)],                              # bar 6: C root
    [('A3',6)],                              # bar 7: A
    [('D4',6)],                              # bar 8: D (5th of G)
]
v4_A = [
    [('G3',2),('D3',2),('G3',2)],            # bar 1: G - D - G (rocking bass)
    [('D3',2),('A3',2),('D3',2)],            # bar 2: D - A - D
    [('G3',2),('D3',2),('G3',2)],
    [('D3',2),('A3',2),('D3',2)],
    [('G3',2),('B3',2),('D4',2)],            # bar 5: walking bass G B D
    [('C3',2),('E3',2),('G3',2)],            # bar 6: walking bass C E G
    [('D3',2),('F#3',2),('A3',2)],           # bar 7: walking bass D F# A
    [('G3',6)],                              # bar 8: long G
]

# B section -- 8 bars (more varied harmony: vi, ii, etc.)
v1_B = [
    [('D5',2),('E5',2),('D5',2)],            # bar 9: I, melodic peak
    [('B4',2),('G4',2),('E4',2)],            # bar 10: vi (Em arp down)
    [('A4',2),('C5',2),('E5',2)],            # bar 11: ii (Am, ascending)
    [('D5',2),('C5',2),('A4',2)],            # bar 12: V (descending)
    [('B4',2),('D5',2),('G4',2)],            # bar 13: I
    [('C5',2),('B4',2),('A4',2)],            # bar 14: IV->V
    [('B4',2),('A4',2),('F#4',2)],           # bar 15: V
    [('G4',6)],                              # bar 16: I
]
v2_B = [
    [('B4',6)],                              # bar 9: B (3rd of G)
    [('G4',6)],                              # bar 10: G (3rd of Em)
    [('E4',6)],                              # bar 11: E (5th of Am)
    [('A4',6)],                              # bar 12: A (5th of D)
    [('D5',6)],                              # bar 13: D (5th of G)
    [('G4',6)],                              # bar 14: G
    [('A4',6)],                              # bar 15: A
    [('B4',6)],                              # bar 16: B
]
v3_B = [
    [('G4',6)],                              # bar 9: G
    [('E4',6)],                              # bar 10: E
    [('C4',6)],                              # bar 11: C
    [('F#4',6)],                             # bar 12: F#
    [('B3',6)],                              # bar 13: B
    [('E4',6)],                              # bar 14: E
    [('F#4',6)],                             # bar 15: F#
    [('D4',6)],                              # bar 16: D
]
v4_B = [
    [('G3',2),('D3',2),('G3',2)],            # bar 9: I bass
    [('E3',2),('B3',2),('E3',2)],            # bar 10: vi
    [('A3',2),('E3',2),('A3',2)],            # bar 11: ii
    [('D3',2),('A3',2),('D3',2)],            # bar 12: V
    [('G3',2),('D3',2),('G3',2)],            # bar 13: I
    [('C3',2),('D3',2),('D3',2)],            # bar 14: C->D walking
    [('A3',2),('D3',2),('F#3',2)],           # bar 15: V (3rd inversion-ish)
    [('G3',6)],                              # bar 16: G final
]


# ----- expand bar lists into per-eighth note arrays ------------------------

def expand(bars):
    """Turn list-of-bars (each = list of (note, eighths)) into a flat list
    of (note, eighth_count) events for the whole section."""
    flat = []
    for bar_idx, beats in enumerate(bars):
        total = sum(n for _, n in beats)
        if total != 6:
            raise ValueError(f'bar {bar_idx+1} has {total} eighths, expected 6')
        for note, count in beats:
            flat.append((note, count))
    return flat


def to_pitches(events):
    """Turn (note, count) list into a flat list of pitch values, one per
    eighth."""
    out = []
    for note, count in events:
        s = step(note)
        out.extend([s] * count)
    return out


# Build the four voice timelines for the whole piece.
# Form: A A B B (each section repeats once -- a real minuet has repeat marks).
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


# ----- merge into command stream -------------------------------------------
#
# Walk the timeline; whenever any voice's pitch changes, emit a command.
# Successive eighths with identical chords get coalesced into one command
# of duration = run_length * EIGHTH.

def build_command_stream():
    cmds = []  # list of 16-bit words

    # First command: set everything (timbres + tempo + initial pitches)
    bits = 0x3F
    chord0 = (piece_v1[0], piece_v2[0], piece_v3[0], piece_v4[0])

    # find duration of the first run
    run = 1
    while (run < N
           and piece_v1[run] == chord0[0]
           and piece_v2[run] == chord0[1]
           and piece_v3[run] == chord0[2]
           and piece_v4[run] == chord0[3]):
        run += 1
    dur = run * EIGHTH
    if dur > 255:
        # Not expected for our piece, but split if it ever happens.
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
            # Same chord across the run boundary -- shouldn't happen because
            # we already coalesce identical chords.
            raise RuntimeError(f'no-change run at eighth {i}')
        cmds.append((bits << 8) | dur)
        cmds.extend(pitches)
        prev = chord
        i += run

    # End-of-song marker
    cmds.append(0x0000)
    return cmds


def main():
    cmds = build_command_stream()
    out = bytearray()
    for w in cmds:
        out += struct.pack('<H', w)
    from _paths import NEW_DISK
    out_path = str(NEW_DISK / 'CLAUDE.MUS')
    with open(out_path, 'wb') as f:
        f.write(out)
    print(f'wrote {out_path}: {len(out)} bytes ({len(cmds)} words, '
          f'{len(cmds)*2} bytes)', file=sys.stderr)


if __name__ == '__main__':
    main()
