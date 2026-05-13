"""midi2mus.py - Convert a MIDI file to a PLAYZ80 .MUS file.

Targets the encoding style of the original CDOS-era Bach inventions on
the music disk (BACH1.MUS etc.):

    Track 1 (upper voice) -> V1, with V3 doubling it using the
                             octave-shifter timbre (timbre 2)
    Track 2 (lower voice) -> V2, with V4 doubling it the same way
    Timbres (V1..V4) = (sine, even-harmonic, skewed-saw, octave-shift)
    TEMPO byte = 140; per-command duration encodes the per-cell sample
                 count at whatever MIDI tempo is in effect for that
                 cell.  Tempo changes (rubato, ritardando) within the
                 source MIDI are honored by varying the dur byte per
                 command -- no bit-5 tempo updates are needed because
                 TEMPO_BYTE stays constant.

Polyphony:
    --voices 1 (solo) detects chord moments in the single source
    track and allocates them to V1 (lowest), V2 (middle, only when
    three notes are sounding), and V3 (highest, with the skewed-saw
    timbre).  Single-note cells get V1 + V3 doubling for body; chord
    cells trade that doubling for the additional pitches, mirroring
    what a cellist does on a double-stop (less bow per string).

Tuning:
    --tuning defaults to 0 cents (concert pitch A=440) for new content.
    Pass --tuning -26 to match the original BACH .MUS files on the
    calibrated 11,169 Hz hardware (the original authoring tool was
    calibrated for ~11,335 Hz; on this hardware the originals come out
    26 cents flat, so new content rendered at -26 cents matches them).

Usage:
    python midi2mus.py SRC.MID OUT.MUS [--voices N] [--tuning CENTS]
"""

import argparse
import struct
import sys
from pathlib import Path

import mido

# ---------- tuning / timing constants -------------------------------------

SAMPLE_RATE  = 11169        # calibrated D+7AIO hardware rate
TEMPO_BYTE   = 140          # inner-loop reload (matches BACH1.MUS)

# Cell resolution: how many cells per MIDI quarter note.
#   8 -> 32nd-note cells (captures mordents / trills, ~2x file size)
#   4 -> 16th-note cells (loses sub-16th ornaments, more compact)
CELL_DIV = 8


# ---------- helpers --------------------------------------------------------

def midi_to_step(n: int, tuning_cents: float = 0.0) -> int:
    """MIDI note number -> 16-bit phase increment for the PLAYZ80 mix loop."""
    semitones = (n - 69) + (tuning_cents / 100.0)
    freq = 440.0 * (2.0 ** (semitones / 12.0))
    return round(freq * 65536.0 / SAMPLE_RATE) & 0xFFFF


def extract_notes(track):
    """Return sorted list of (start_tick, end_tick, midi_note) for one MIDI track."""
    out = []
    open_notes = {}
    t = 0
    for msg in track:
        t += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            open_notes[msg.note] = t
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in open_notes:
                start = open_notes.pop(msg.note)
                out.append((start, t, msg.note))
    # Close any still-open notes at last event time (safety net)
    for n, start in open_notes.items():
        out.append((start, t, n))
    return sorted(out)


def note_at_cell(notes, t_lo, t_hi):
    """Return the MIDI note sounding during [t_lo, t_hi).  If multiple notes
    overlap the cell (mordent / trill / chord), prefer the EARLIEST attack
    -- that's typically the structural / principal note; the rest are
    32nd-note ornaments lost to 16th-cell quantization."""
    cand = [(s, n) for (s, e, n) in notes if s < t_hi and e > t_lo]
    if not cand:
        return None
    return min(cand, key=lambda c: c[0])[1]


def notes_at_cell(notes, t_lo, t_hi, max_voices=3):
    """Return up to max_voices MIDI notes sounding during [t_lo, t_hi),
    sorted ascending by pitch.  Used by mode '1' to detect chord moments
    in a single source track.

    When polyphony exceeds max_voices, score each note by
    (cell-coverage * total-note-duration) and keep the top max_voices.
    Both factors favor structural / sustained notes; short trill or
    mordent notes lose on both axes and are dropped.  This prevents a
    sustained two-note bass plus a fast half-cell trill from collapsing
    to "bass + both trill notes," which would pin two adjacent semitones
    together and produce audible beats at the difference frequency."""
    scored = []
    for (s, e, n) in notes:
        if s >= t_hi or e <= t_lo:
            continue
        coverage = min(e, t_hi) - max(s, t_lo)
        total = e - s
        scored.append((n, coverage * total, s))
    if not scored:
        return []
    if len(scored) <= max_voices:
        return sorted({n for n, _, _ in scored})
    # Rank by score descending; break ties by earlier attack.
    scored.sort(key=lambda x: (-x[1], x[2]))
    return sorted({n for n, _, _ in scored[:max_voices]})


def build_tempo_map(mid):
    """Walk every track and collect (tick, tempo_us_per_quarter) events
    sorted by absolute tick.  Always returns at least one entry; if the
    MIDI has no set_tempo events, defaults to 120 BPM (500,000 us/quarter)
    starting at tick 0."""
    events = []
    for track in mid.tracks:
        t = 0
        for msg in track:
            t += msg.time
            if msg.type == 'set_tempo':
                events.append((t, msg.tempo))
    events.sort()
    if not events or events[0][0] > 0:
        events.insert(0, (0, 500_000))
    return events


def tempo_at_tick(tempo_map, tick):
    """Return the tempo (us/quarter) in effect at the given absolute tick."""
    current = tempo_map[0][1]
    for et, etempo in tempo_map:
        if et <= tick:
            current = etempo
        else:
            break
    return current


def dur_byte_for_tempo(tempo_us_per_quarter: int) -> int:
    """Compute the .MUS duration byte that makes one cell play for one
    32nd-note (or CELL_DIV-th of a quarter) at the given MIDI tempo on
    the calibrated hardware."""
    us_per_cell = tempo_us_per_quarter / float(CELL_DIV)
    samples_per_cell = (us_per_cell / 1_000_000.0) * SAMPLE_RATE
    dur = round(samples_per_cell / TEMPO_BYTE)
    return max(1, min(255, dur))


# ---------- conversion ----------------------------------------------------

def convert(mid_path: str, mus_path: str, mode: str = '2', tuning_cents: float = 0.0):
    if mode not in ('1', '2', '3', '2of3'):
        sys.exit(f"mode must be '1', '2', '3', or '2of3', got {mode!r}")

    # tracks_to_extract is how many MIDI voice tracks we need to read.
    #   '1'    -> 1 voice  (solo, e.g. cello suite -- V1 sine + V3 skewed-saw doubling)
    #   '2'    -> 2 voices (BACH inventions)
    #   '3'    -> 3 voices (sinfonias, faithful)
    #   '2of3' -> 3 voices (sinfonias, soprano gets BACH-style octave doubling)
    tracks_to_extract = {'1': 1, '2': 2, '3': 3, '2of3': 3}[mode]

    mid = mido.MidiFile(mid_path)
    ppqn = mid.ticks_per_beat
    cell_ticks = ppqn // CELL_DIV   # one cell in MIDI ticks (32nd at CELL_DIV=8)

    needed_tracks = tracks_to_extract + 1   # +1 conductor track
    if len(mid.tracks) < needed_tracks:
        sys.exit(f"error: mode={mode!r} needs {needed_tracks} tracks "
                 f"(conductor + {tracks_to_extract} voices), got {len(mid.tracks)}")

    # Extract each voice track's notes
    voice_notes = [extract_notes(mid.tracks[i + 1]) for i in range(tracks_to_extract)]

    last_t = max((e for vt in voice_notes for _, e, _ in vt), default=0)
    n_cells = (last_t + cell_ticks - 1) // cell_ticks

    tempo_map = build_tempo_map(mid)
    initial_tempo = tempo_map[0][1]
    initial_bpm = 60_000_000 / initial_tempo

    # Per-cell dur byte (rubato support: varies as MIDI tempo changes).
    durs = []
    for c in range(n_cells):
        t = tempo_at_tick(tempo_map, c * cell_ticks)
        durs.append(dur_byte_for_tempo(t))
    tempo_changes = sum(1 for a, b in zip(durs, durs[1:]) if a != b)

    # Build the V1..V4 step arrays plus the timbre tuple, depending on mode.
    # Modes 2 / 3 / 2of3 follow the original "one MIDI track per voice"
    # model (monophonic per track).  Mode 1 reads a single track and
    # allocates polyphony to V1/V2/V3 dynamically per cell.
    #
    #   '2'    : V1+V3 carry track-1 (V3's timbre 2 is a normal skewed-saw,
    #            so V3 doubles V1 with a different waveform at the same pitch),
    #            V2+V4 carry track-2 (V4's timbre 3 is the octave-shifter, so
    #            V4 sounds an octave above V2).  This is the original BACH style.
    #   '3'    : V1, V2, V3 carry tracks 1, 2, 3 independently.  V4 is silent;
    #            its timbre is forced to 0 (sine) so the wavetable[0] DC offset
    #            contribution is minimal.
    #   '2of3' : Sinfonia, soprano gets BACH-style octave doubling.
    #              V1 = soprano (timbre 1, even-harm -- has fundamental)
    #              V3 = soprano (timbre 3, octave-shifter -- adds octave-up sparkle)
    #              V2 = alto    (timbre 0, sine -- clean solo)
    #              V4 = bass    (timbre 2, skewed-saw -- present, not octave-shifted)
    #            All three sinfonia voices remain audible at their written pitch;
    #            soprano gains body from the V1+V3 fundamental+octave pair.
    if mode == '1':
        # Solo with chord-moment handling.
        #   Single note  : V1 = note (sine), V3 = note (saw)         -- doubled
        #   Two notes    : V1 = lowest, V3 = highest (saw on melody) -- no doubling
        #   Three notes  : V1 = low, V2 = mid (sine), V3 = high (saw)
        # V2 timbre is 0 (sine) so its silent cells park at wavetable[0][0]=0.
        # V4 is always silent.
        v1 = [0] * n_cells
        v2 = [0] * n_cells
        v3 = [0] * n_cells
        v4 = [0] * n_cells
        chord_cells = 0
        for c in range(n_cells):
            t0 = c * cell_ticks
            t1 = (c + 1) * cell_ticks
            chord = notes_at_cell(voice_notes[0], t0, t1)
            if not chord:
                continue
            if len(chord) == 1:
                s = midi_to_step(chord[0], tuning_cents)
                v1[c] = s
                v3[c] = s
            elif len(chord) == 2:
                v1[c] = midi_to_step(chord[0], tuning_cents)
                v3[c] = midi_to_step(chord[1], tuning_cents)
                chord_cells += 1
            else:
                v1[c] = midi_to_step(chord[0], tuning_cents)
                v2[c] = midi_to_step(chord[1], tuning_cents)
                v3[c] = midi_to_step(chord[2], tuning_cents)
                chord_cells += 1
        timbres = (0, 0, 2, 0)
    elif mode == '2':
        voice_steps = []
        for vt in voice_notes:
            steps = []
            for c in range(n_cells):
                t0 = c * cell_ticks
                t1 = (c + 1) * cell_ticks
                n = note_at_cell(vt, t0, t1)
                steps.append(midi_to_step(n, tuning_cents) if n is not None else 0)
            voice_steps.append(steps)
        v1, v2 = voice_steps
        v3, v4 = list(v1), list(v2)
        timbres = (0, 1, 2, 3)
        chord_cells = 0
    elif mode == '3':
        voice_steps = []
        for vt in voice_notes:
            steps = []
            for c in range(n_cells):
                t0 = c * cell_ticks
                t1 = (c + 1) * cell_ticks
                n = note_at_cell(vt, t0, t1)
                steps.append(midi_to_step(n, tuning_cents) if n is not None else 0)
            voice_steps.append(steps)
        v1, v2, v3 = voice_steps
        v4 = [0] * n_cells
        timbres = (0, 1, 2, 0)
        chord_cells = 0
    else:  # '2of3'
        voice_steps = []
        for vt in voice_notes:
            steps = []
            for c in range(n_cells):
                t0 = c * cell_ticks
                t1 = (c + 1) * cell_ticks
                n = note_at_cell(vt, t0, t1)
                steps.append(midi_to_step(n, tuning_cents) if n is not None else 0)
            voice_steps.append(steps)
        sop, alt, bas = voice_steps
        v1 = sop
        v2 = alt
        v3 = list(sop)
        v4 = bas
        timbres = (1, 0, 3, 2)
        chord_cells = 0

    # ---- emit .MUS command stream ----
    cmds = []

    # Cmd 0: full setup (bits 0x3F = 4 pitches + 2 timbre words + tempo)
    cmds.append((0x3F << 8) | durs[0])
    cmds.append(v1[0])
    cmds.append(v2[0])
    cmds.append(v3[0])
    cmds.append(v4[0])
    v12 = ((0x81 + timbres[1]) << 8) | (0x81 + timbres[0])
    v34 = ((0x81 + timbres[3]) << 8) | (0x81 + timbres[2])
    cmds.append(v12)
    cmds.append(v34)
    cmds.append(TEMPO_BYTE)

    # Subsequent commands: bit-encoded per-voice changes, with each
    # command's dur drawn from durs[i] so MIDI tempo changes show up
    # as varying-length cells.
    i = 1
    while i < n_cells:
        c1 = (v1[i] != v1[i - 1])
        c2 = (v2[i] != v2[i - 1])
        c3 = (v3[i] != v3[i - 1])
        c4 = (v4[i] != v4[i - 1])

        if c1 or c2 or c3 or c4:
            bits = 0
            if c1: bits |= 0x01
            if c2: bits |= 0x02
            if c3: bits |= 0x04
            if c4: bits |= 0x08
            cmds.append((bits << 8) | durs[i])
            if bits & 0x01: cmds.append(v1[i])
            if bits & 0x02: cmds.append(v2[i])
            if bits & 0x04: cmds.append(v3[i])
            if bits & 0x08: cmds.append(v4[i])
            i += 1
        else:
            # Hold run: cells with no voice change AND identical dur.
            # A tempo change in the middle of an otherwise-held passage
            # breaks the run so the new cells get their own dur values.
            j = i
            while (j < n_cells
                   and v1[j] == v1[i - 1] and v2[j] == v2[i - 1]
                   and v3[j] == v3[i - 1] and v4[j] == v4[i - 1]
                   and durs[j] == durs[i]):
                j += 1
            held_cells = j - i
            samples_to_hold = held_cells * durs[i]
            while samples_to_hold > 0:
                chunk = min(255, samples_to_hold)
                cmds.append((0x00 << 8) | chunk)
                samples_to_hold -= chunk
            i = j

    # End-of-song marker
    cmds.append(0x0000)

    # ---- write file ----
    data = b''.join(struct.pack('<H', w) for w in cmds)
    Path(mus_path).write_bytes(data)

    cell_name = {4: '16th', 8: '32nd', 16: '64th'}.get(CELL_DIV, f'1/{CELL_DIV*4}')
    mode_label = {
        '1':    '1-voice solo (V1 sine + V3 skewed-saw doubling, V2/V4 silent)',
        '2':    '2-voice (BACH style: V1+V3, V2+V4 doubled)',
        '3':    '3-voice (V1, V2, V3 independent; V4 silent)',
        '2of3': '2of3 sinfonia (V1+V3 soprano fund+octave, V2 alto, V4 bass)',
    }[mode]
    min_bpm = 60_000_000 / max(t for _, t in tempo_map)
    max_bpm = 60_000_000 / min(t for _, t in tempo_map)
    tempo_summary = (f"{initial_bpm:.1f} BPM" if min_bpm == max_bpm
                     else f"{initial_bpm:.1f} BPM initial, {min_bpm:.1f}..{max_bpm:.1f} BPM range")
    print(f"  source:        {mid_path}")
    print(f"  mode:          {mode_label}")
    print(f"  ppqn:          {ppqn}")
    print(f"  cell:          {cell_ticks} MIDI ticks ({cell_name} note, CELL_DIV={CELL_DIV})")
    print(f"  cells total:   {n_cells}")
    print(f"  MIDI tempo:    {tempo_summary} ({len(tempo_map)} tempo events, {tempo_changes} cell-level changes)")
    print(f"  dur byte:      {min(durs)}..{max(durs)} (rubato)" if min(durs) != max(durs)
          else f"  dur byte:      {durs[0]}  ({durs[0]*TEMPO_BYTE/SAMPLE_RATE*1000:.2f} ms per cell)")
    if mode == '1':
        print(f"  chord cells:   {chord_cells} of {n_cells}")
    print(f"  tuning offset: {tuning_cents:+g} cents")
    print(f"  output:        {mus_path}  ({len(data)} bytes, {len(cmds)} words)")


# ---------- CLI -----------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('source_mid')
    ap.add_argument('output_mus')
    ap.add_argument('--voices', default='2', choices=['1', '2', '3', '2of3'],
                    help="1 = solo (V1 sine + V3 saw doubling; V2/V4 silent); "
                         "2 = invention (V1+V3, V2+V4 doubled); "
                         "3 = sinfonia faithful (V1,V2,V3; V4 silent); "
                         "2of3 = sinfonia w/ soprano octave-doubled (V1+V3 sop, V2 alto, V4 bass)")
    ap.add_argument('--tuning', type=float, default=0.0, metavar='CENTS',
                    help="tuning offset from A=440 in cents (default 0; "
                         "use -26 to match the original BACH .MUS files on "
                         "calibrated 11,169 Hz hardware)")
    args = ap.parse_args()
    convert(args.source_mid, args.output_mus, args.voices, args.tuning)


if __name__ == '__main__':
    main()
