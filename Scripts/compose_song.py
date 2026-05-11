"""
compose_song.py - Transcribe the song from bigger1.png + bigger2.png into a
.MUS file.

Score:
    - Key: G major (1 sharp)
    - Time: 4/4
    - Tempo: quarter = 60 BPM
    - 54 measures, single-voice melody with chord symbols
    - Solfege labels: do=C, re=D, mi=E, fa=F (fa#=F#), sol=G, la=A, si=B

Tempo math:
    SAMPLE_RATE = 11169.
    Want quarter = 1.0 sec  =>  11169 samples/quarter  =>  2792 samples/16th.
    samples_per_command = duration_byte * tempo_byte.
    Pick TEMPO=200, SIXTEENTH=14  =>  2800 samples per 16th, quarter ~= 1.003
    sec ~= 59.8 BPM (~0.3% slow vs 60 BPM target -- inaudible).

Single-voice melody on v1 (sine timbre). v2/v3/v4 are kept silent by leaving
their phase increments at 0 throughout.
"""

import struct
import sys

SAMPLE_RATE = 11169  # calibrated to physical D+7A hardware (2026-05-09)

# ----- pitch table ---------------------------------------------------------

def step(note):
    """Note name like 'G4', 'F#4', 'A3' -> 16-bit phase increment.
    'R' or None -> 0 (rest / silence)."""
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

# ----- timing --------------------------------------------------------------

# At SR=11169 Hz, 60 BPM (quarter = 1 sec) wants 2792 samples/16th.
# Constraint: SIXTEENTH * 16 <= 255 (whole note must fit in one dur byte).
# Pick SIXTEENTH=14, TEMPO=200  ->  2800 samples/16th, max held = 18 sixteenths.
SIXTEENTH = 14
TEMPO     = 200
# samples per 16th = 2800 -> 16 sixteenths/bar = 44800 samples = 4.011 sec/bar
# quarter ~= 1.003 sec ~= 59.8 BPM (~0.3% slow vs 60 BPM target).

# ----- the melody ----------------------------------------------------------
#
# Each bar is a list of (note, sixteenth_count) tuples. Bar must total 16
# sixteenths (4/4 time). 'R' = rest. Pitches in scientific notation.
#
# Symbol decoding rule used throughout:
#   "lá si ré" pickups (under low/below-staff notes)  -> A3 B3 D4
#   "mi sol mi" mid-staff figures                      -> E4 G4 E4
#   "mi ré si" descending mid-staff                    -> E4 D4 B3
#   "dó si sol" upper figure                            -> C5 B4 G4
#   "fá# mi ré" descending around F#4                   -> F#4 E4 D4
#   "lá fá# mi ré" descending                           -> A4 F#4 E4 D4
#
# Where rhythm is ambiguous I default to:
#   long sustained notes (clearly half/dotted-half/whole)  -> 8/12/16 sixteenths
#   short pickups of 3 notes at end of bar                  -> 3 eighths (6 sixteenths)
#   sixteenth-note runs                                     -> 1 each

# Page 1, mm. 1-33

bars_p1 = [
    # m1 (Em) -- pickup bar: HR + 8R + [la3 si3 re4]
    [('R', 8), ('R', 2), ('A3', 2), ('B3', 2), ('D4', 2)],
    # m2 (G):  H mi + 8R + [mi sol mi]
    [('E4', 8), ('R', 2), ('E4', 2), ('G4', 2), ('E4', 2)],
    # m3 (Em): H re + 8R + [la3 si3 re4]
    [('D4', 8), ('R', 2), ('A3', 2), ('B3', 2), ('D4', 2)],
    # m4 (Em): H mi + 8R + [mi sol mi]
    [('E4', 8), ('R', 2), ('E4', 2), ('G4', 2), ('E4', 2)],
    # m5 (G):  H re + 8R + [la3 si3 re4]
    [('D4', 8), ('R', 2), ('A3', 2), ('B3', 2), ('D4', 2)],
    # m6 (Em): H mi + 8R + [mi re si]
    [('E4', 8), ('R', 2), ('E4', 2), ('D4', 2), ('B3', 2)],
    # m7 (D):  DH la + [la si re mi] sixteenths
    [('A3', 12), ('A3', 1), ('B3', 1), ('D4', 1), ('E4', 1)],
    # m8 (Em): H mi + 8R + [mi re si]
    [('E4', 8), ('R', 2), ('E4', 2), ('D4', 2), ('B3', 2)],
    # m9 (D):  DH la + [la si re] (3 eighths fits in 6 sixteenths -> tighten)
    # Actually the score shows DH la then [lá si ré] eighth pickup at end - call it 12 + 4
    [('A3', 12), ('A3', 1), ('B3', 1), ('D4', 1), ('E4', 1)],
    # m10 (G): whole sol3 (pedal point)
    [('G3', 16)],
    # m11 (G): DH sol3 + 8R + 16-16 [do si] pickup
    [('G3', 12), ('R', 2), ('C5', 1), ('B4', 1)],
    # m12 (C): 8R + [do si sol] + 8R + [do si do si sol la] (sixteenths)
    [('R', 2), ('C5', 2), ('B4', 2), ('G4', 2),
     ('R', 2), ('C5', 1), ('B4', 1), ('C5', 1), ('B4', 1), ('G4', 1), ('A4', 1)],
    # m13 (D): "fá# mi ré" + ... - approximate as descending fragment
    # Score shows pickup [fa# mi re] then [re si re mi] type patterns
    [('F#4', 2), ('E4', 2), ('D4', 2), ('R', 2),
     ('D4', 1), ('B3', 1), ('D4', 1), ('E4', 1), ('R', 2), ('D4', 2)],
    # m14 (G or no chord change?): "ré si ré mi - ré" + "mi mi ré si ré"
    [('D4', 1), ('B3', 1), ('D4', 1), ('E4', 1), ('D4', 4),
     ('R', 2), ('E4', 1), ('E4', 1), ('D4', 1), ('B3', 1), ('D4', 2)],
    # m15: "si dó dó si sol"  -- ascend to high, fall to G
    [('R', 4), ('B4', 2), ('C5', 2), ('C5', 2), ('B4', 2), ('G4', 4)],
    # m16 (D, with triplet): "lá fá# mi ré - ré ré ré (3plet) - si - dó si sol"
    [('A4', 2), ('F#4', 2), ('E4', 2), ('D4', 2),
     ('D4', 1), ('D4', 1), ('D4', 1), ('B3', 1),
     ('C5', 1), ('B4', 1), ('G4', 2)],
    # m17 (C): "sol ré dó si dó" - ascending up to high register
    [('G4', 2), ('D4', 2), ('R', 2), ('C5', 2),
     ('C5', 2), ('B4', 1), ('C5', 1), ('B4', 1), ('C5', 1), ('B4', 1), ('R', 1)],
    # m18 (Am): "dó si dó si sol sol"
    [('C5', 2), ('B4', 2), ('C5', 2), ('B4', 2),
     ('G4', 2), ('G4', 2), ('R', 2), ('R', 2)],
    # m19 (G): "dó si só ré ré mi - ré dó sol"
    [('C5', 2), ('B4', 2), ('G4', 2), ('D4', 2),
     ('D4', 2), ('E4', 2), ('D4', 2), ('C5', 1), ('G4', 1)],
    # m20 (C): "mi mi ré si"
    [('R', 2), ('E4', 2), ('E4', 2), ('D4', 2), ('B3', 2),
     ('R', 2), ('E4', 2), ('R', 2)],
    # m21 (D): "ré lá - ré ré si ré"
    [('D4', 4), ('A3', 4), ('R', 2), ('D4', 2), ('D4', 1), ('B3', 1), ('D4', 2)],
    # m22 (Am): "mi ré si - mi mi ré si ré"
    [('E4', 2), ('D4', 2), ('B3', 4), ('E4', 2), ('E4', 1), ('D4', 1), ('B3', 2), ('D4', 2)],
    # m23 (G): "ré (long, dotted)"
    [('D4', 12), ('E4', 1), ('D4', 1), ('B3', 1), ('G4', 1)],
    # m24 (D, triplet): "fá# mi ré - ré ré dó si dó - si sol - dó"
    [('F#4', 2), ('E4', 2), ('D4', 2), ('R', 2),
     ('D4', 1), ('D4', 1), ('C5', 1), ('B4', 1),
     ('C5', 1), ('B4', 1), ('G4', 1), ('C5', 1)],
    # m25 (C): "ré dó dó si sol dó"
    [('R', 2), ('D5', 2), ('C5', 2), ('D5', 2),
     ('C5', 2), ('B4', 1), ('G4', 1), ('C5', 1), ('R', 1), ('R', 2)],
    # m26 (Am): "mi mi dó dó sol mi dó si sol"
    [('E4', 2), ('R', 2), ('E4', 2), ('C5', 2),
     ('C5', 1), ('G4', 1), ('E4', 1), ('C5', 1), ('B4', 2), ('G4', 2)],
    # m27 (G): "lá si ré mi" pickup (continuing pattern from m1-style)
    [('R', 8), ('R', 2), ('A3', 2), ('B3', 2), ('D4', 2)],
    # m28 (Em): "mi mi sol mi - ré"
    [('E4', 8), ('R', 2), ('E4', 2), ('G4', 2), ('E4', 2)],
    # m29 (G): "ré - lá si ré" (return to m3-like)
    [('D4', 8), ('R', 2), ('A3', 2), ('B3', 2), ('D4', 2)],
    # m30 (Em): H mi + 8R + [mi sol mi]
    [('E4', 8), ('R', 2), ('E4', 2), ('G4', 2), ('E4', 2)],
    # m31 (G): H re + 8R + [la si re]
    [('D4', 8), ('R', 2), ('A3', 2), ('B3', 2), ('D4', 2)],
    # m32 (Em): H mi + 8R + [mi re si]
    [('E4', 8), ('R', 2), ('E4', 2), ('D4', 2), ('B3', 2)],
    # m33 (D): DH la + [la si re]
    [('A3', 12), ('A3', 1), ('B3', 1), ('D4', 2)],
]

# Page 2, mm. 34-54
bars_p2 = [
    # m34 (Em): H mi + 8R + [mi re si]
    [('E4', 8), ('R', 2), ('E4', 2), ('D4', 2), ('B3', 2)],
    # m35 (D): DH la + [la si re]
    [('A3', 12), ('A3', 1), ('B3', 1), ('D4', 2)],
    # m36 (G): whole sol3 (pedal)
    [('G3', 16)],
    # m37 (C): 8R + [do si do si sol] + 8R + [do si do si sol la]
    [('R', 2), ('C5', 1), ('B4', 1), ('C5', 1), ('B4', 1), ('G4', 2),
     ('R', 2), ('C5', 1), ('B4', 1), ('C5', 1), ('B4', 1), ('G4', 1), ('A4', 1)],
    # m38 (D): tied long re + pickup [si re mi mi mi mi mi mi]
    [('D4', 4), ('R', 2), ('R', 2), ('B3', 1), ('D4', 1),
     ('E4', 1), ('E4', 1), ('E4', 1), ('E4', 1), ('R', 2)],
    # m39 (Am): "mi mi mi mi re mi re mi mi" - lots of E4s
    [('E4', 2), ('E4', 1), ('E4', 1), ('E4', 1), ('E4', 1),
     ('D4', 2), ('E4', 1), ('D4', 1), ('E4', 1), ('E4', 1), ('R', 2)],
    # m40 (G): "re re si re" - approximate
    [('R', 2), ('D4', 2), ('D4', 2), ('B3', 2), ('D4', 2), ('R', 2), ('R', 2)],
    # m41 (D, triplet): "re do# re do la re" + "re re re" triplet + "re"
    [('R', 2), ('D5', 1), ('C#5', 1), ('D5', 1), ('C5', 1),
     ('A4', 1), ('D5', 1), ('D5', 4), ('R', 2)],
    # m42 (C): "re re do re do si sol sol re do si"
    [('R', 2), ('D5', 1), ('R', 1), ('D5', 1), ('C5', 1), ('D5', 2),
     ('C5', 1), ('B4', 1), ('G4', 1), ('G4', 1), ('D5', 1), ('C5', 1), ('B4', 2)],
    # m43 (Am G): "do - do do si sol do si sol"
    [('C5', 4), ('R', 2), ('C5', 1), ('C5', 1), ('B4', 1), ('G4', 1),
     ('C5', 1), ('B4', 1), ('G4', 2)],
    # m44 (Em G): "la si re mi - mi sol mi re"
    [('A3', 1), ('B3', 1), ('D4', 1), ('E4', 1),
     ('R', 2), ('E4', 2), ('G4', 2), ('E4', 2), ('R', 2), ('D4', 2)],
    # m45 (Em? continuing): "la si re"
    [('R', 8), ('R', 2), ('A3', 2), ('B3', 2), ('D4', 2)],
    # m46 (Em G): "mi sol mi re"
    [('E4', 4), ('G4', 2), ('E4', 2), ('R', 2), ('D4', 2),
     ('A3', 1), ('B3', 1), ('D4', 2)],
    # m47 (Em): H mi + 8R + [mi sol mi re]
    [('E4', 8), ('R', 2), ('E4', 2), ('G4', 2), ('E4', 2)],
    # m48 (G): half re + pickup
    [('D4', 8), ('R', 2), ('A3', 2), ('B3', 2), ('D4', 2)],
    # m49 (Em): "mi - fá# sol mi re si"
    [('E4', 4), ('F#4', 2), ('G4', 2), ('E4', 2), ('D4', 2), ('B3', 4)],
    # m50 (D): DH la + [la si re]
    [('A3', 12), ('A3', 1), ('B3', 1), ('D4', 2)],
    # m51 (Em): DQ mi + 8 fá# + [sol mi re si]
    [('E4', 6), ('F#4', 2), ('G4', 2), ('E4', 2), ('D4', 2), ('B3', 2)],
    # m52 (D): DH la + quarter rest? Just hold la
    [('A3', 12), ('A3', 1), ('B3', 1), ('D4', 2)],
    # m53 (G): half la + pickup [la si re]
    [('A3', 8), ('R', 2), ('A3', 2), ('B3', 2), ('D4', 2)],
    # m54 (G): final whole sol
    [('G3', 16)],
]

bars = bars_p1 + bars_p2

# ----- expand into per-16th pitch list -------------------------------------

def expand(bars):
    pitches = []
    for bar_idx, bar in enumerate(bars):
        total = sum(n for _, n in bar)
        if total != 16:
            print(f'WARN bar {bar_idx+1}: total {total} sixteenths (expected 16); '
                  'truncating/padding', file=sys.stderr)
            if total > 16:
                # truncate from the end
                running = 0
                new_bar = []
                for note, n in bar:
                    if running + n <= 16:
                        new_bar.append((note, n))
                        running += n
                    else:
                        new_bar.append((note, 16 - running))
                        running = 16
                        break
                bar = new_bar
            else:
                bar = bar + [('R', 16 - total)]
        for note, n in bar:
            s = step(note)
            pitches.extend([s] * n)
    return pitches

melody = expand(bars)
N = len(melody)
print(f'piece length: {N} sixteenths = {N // 16} bars '
      f'= {N * SIXTEENTH * TEMPO / SAMPLE_RATE:.1f} seconds', file=sys.stderr)


# ----- merge into command stream -------------------------------------------

def build_command_stream():
    cmds = []

    # First command: set everything
    bits = 0x3F
    p0 = melody[0]
    run = 1
    while run < N and melody[run] == p0:
        run += 1
    # split runs that overflow 8-bit duration
    while run * SIXTEENTH > 255:
        # emit a command for (255 // SIXTEENTH) sixteenths
        chunk = 255 // SIXTEENTH
        cmds_first_partial = chunk
        run -= chunk

    # Build the commands by walking the timeline
    cmds = []
    # Initial setup command
    initial_run = 1
    while initial_run < N and melody[initial_run] == melody[0]:
        initial_run += 1

    # We may need to split if dur > 255
    def emit_chunks(initial, run, voice_changed_bits, pitch):
        # split run into chunks of <= MAX_PER_CHUNK sixteenths
        MAX = 255 // SIXTEENTH
        out = []
        first = True
        remaining = run
        while remaining > 0:
            chunk = min(remaining, MAX)
            dur = chunk * SIXTEENTH
            if first and initial:
                out.append((0x3F, dur, 'init'))
            elif first:
                out.append((voice_changed_bits, dur, 'change'))
            else:
                # continuation: no params change, but we still need a command...
                # Actually if we don't change any voice and don't change tempo, the bits will be 0,
                # which means duration only applies. cmd = bits<<8 | dur with bits=0.
                out.append((0x00, dur, 'continue'))
            remaining -= chunk
            first = False
        return out

    # Walk melody, emit per-run command chains
    i = 0
    prev = None
    is_first = True
    while i < N:
        pitch = melody[i]
        run = 1
        while i + run < N and melody[i + run] == pitch:
            run += 1

        if is_first:
            # First command: initialize all voices, timbres, tempo.
            # Emit initial chunk
            MAX = 255 // SIXTEENTH
            chunk = min(run, MAX)
            dur = chunk * SIXTEENTH
            cmds.append((0x3F << 8) | dur)
            cmds.append(pitch)            # v1
            cmds.append(0)                # v2 silent
            cmds.append(0)                # v3 silent
            cmds.append(0)                # v4 silent
            # timbre v1=sine v2=sine v3=sine v4=sine -> 0x81 each
            cmds.append((0x81 << 8) | 0x81)
            cmds.append((0x81 << 8) | 0x81)
            cmds.append(TEMPO)
            run -= chunk
            is_first = False
            prev = pitch
            # any leftover continues as bits=0 commands
            while run > 0:
                chunk = min(run, MAX)
                dur = chunk * SIXTEENTH
                cmds.append((0x00 << 8) | dur)
                run -= chunk
        else:
            MAX = 255 // SIXTEENTH
            # emit change command first
            change = (pitch != prev)
            first_chunk = True
            while run > 0:
                chunk = min(run, MAX)
                dur = chunk * SIXTEENTH
                if first_chunk and change:
                    cmds.append((0x01 << 8) | dur)  # bit 0 = v1 change
                    cmds.append(pitch)
                else:
                    cmds.append((0x00 << 8) | dur)
                run -= chunk
                first_chunk = False
            prev = pitch
        i += (1 if run == 0 else run)  # actually i should advance by total run consumed
        # Recompute properly:
        # Wait, the inner loop already consumed everything. Need to reset.
        # The bug: above I set run from the outer while, then decremented inside.
        # i should advance by the original run length.

    # Redo properly:
    return cmds


def build_command_stream_v2():
    """Cleaner implementation."""
    cmds = []
    MAX_TICKS = 255  # 8-bit dur byte
    MAX_16THS_PER_CMD = MAX_TICKS // SIXTEENTH

    # Walk the melody
    i = 0
    prev = None
    is_first = True
    while i < N:
        pitch = melody[i]
        run = 1
        while i + run < N and melody[i + run] == pitch:
            run += 1

        # Emit (possibly multiple) commands covering this run
        first_chunk = True
        remaining = run
        while remaining > 0:
            chunk = min(remaining, MAX_16THS_PER_CMD)
            dur = chunk * SIXTEENTH
            if is_first and first_chunk:
                # Initialize: bits=0x3F (v1+v2+v3+v4+timbre+tempo)
                cmds.append((0x3F << 8) | dur)
                cmds.append(pitch)        # v1 phase increment
                cmds.append(0)            # v2 silent
                cmds.append(0)            # v3 silent
                cmds.append(0)            # v4 silent
                cmds.append((0x81 << 8) | 0x81)  # timbre v1,v2 = sine
                cmds.append((0x81 << 8) | 0x81)  # timbre v3,v4 = sine
                cmds.append(TEMPO)
                is_first = False
            elif first_chunk and pitch != prev:
                # v1 changes
                cmds.append((0x01 << 8) | dur)
                cmds.append(pitch)
            else:
                # No change, just hold for `dur` ticks.
                cmds.append((0x00 << 8) | dur)
            remaining -= chunk
            first_chunk = False
        prev = pitch
        i += run

    cmds.append(0x0000)  # end of song
    return cmds


def main():
    cmds = build_command_stream_v2()
    out = bytearray()
    for w in cmds:
        out += struct.pack('<H', w)
    from _paths import NEW_DISK
    out_path = str(NEW_DISK / 'SONG.MUS')
    with open(out_path, 'wb') as f:
        f.write(out)
    print(f'wrote {out_path}: {len(out)} bytes ({len(cmds)} words)',
          file=sys.stderr)


if __name__ == '__main__':
    main()
