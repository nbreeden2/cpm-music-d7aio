"""midi2mus.py - Convert a MIDI file to a PLAYZ80 .MUS file.

Targets the encoding style of the original CDOS-era Bach inventions on
the music disk (BACH1.MUS etc.):

    Track 1 (upper voice) -> V1, with V3 doubling it using the
                             octave-shifter timbre (timbre 2)
    Track 2 (lower voice) -> V2, with V4 doubling it the same way
    Timbres (V1..V4) = (sine, even-harmonic, skewed-saw, octave-shift)
    TEMPO byte = 140; per-command duration computed so one 16th-note
                 cell plays at the MIDI's embedded tempo
    Tuning offset -26 cents from A=440, matching the original BACH
                  files' pitch (the original tool was calibrated for
                  hardware at ~11,335 Hz; on the user's 11,169 Hz
                  hardware the originals come out 26 cents flat).

Usage:
    python midi2mus.py SRC.MID OUT.MUS
"""

import argparse
import struct
import sys
from pathlib import Path

import mido

# ---------- tuning / timing constants -------------------------------------

SAMPLE_RATE  = 11169        # calibrated D+7AIO hardware rate
TEMPO_BYTE   = 140          # inner-loop reload (matches BACH1.MUS)
TUNING_CENTS = -26          # offset from A=440 -- matches original BACH tuning
TIMBRES      = (0, 1, 2, 3) # V1=sine, V2=even-harm, V3=skewed-saw, V4=oct-shift

# Cell resolution: how many cells per MIDI quarter note.
#   8 -> 32nd-note cells (captures mordents / trills, ~2x file size)
#   4 -> 16th-note cells (loses sub-16th ornaments, more compact)
CELL_DIV = 8


# ---------- helpers --------------------------------------------------------

def midi_to_step(n: int) -> int:
    """MIDI note number -> 16-bit phase increment for the PLAYZ80 mix loop."""
    semitones = (n - 69) + (TUNING_CENTS / 100.0)
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


def get_midi_tempo(mid):
    """First set_tempo meta message in microseconds-per-quarter; default 120 BPM."""
    for track in mid.tracks:
        for msg in track:
            if msg.type == 'set_tempo':
                return msg.tempo
    return 500_000


def compute_dur_byte(midi_tempo_us_per_quarter: int) -> int:
    """Compute the .MUS duration byte that makes one cell play at the MIDI's
    embedded tempo on the calibrated hardware.  Cell size is set by CELL_DIV
    (cells per quarter note)."""
    us_per_cell = midi_tempo_us_per_quarter / float(CELL_DIV)
    samples_per_cell = (us_per_cell / 1_000_000.0) * SAMPLE_RATE
    dur = round(samples_per_cell / TEMPO_BYTE)
    return max(1, min(255, dur))


# ---------- conversion ----------------------------------------------------

def convert(mid_path: str, mus_path: str, mode: str = '2'):
    if mode not in ('2', '3', '2of3'):
        sys.exit(f"mode must be '2', '3', or '2of3', got {mode!r}")

    # tracks_to_extract is how many MIDI voice tracks we need to read.
    #   '2'    -> 2 voices (BACH inventions)
    #   '3'    -> 3 voices (sinfonias, faithful)
    #   '2of3' -> 3 voices (sinfonias, soprano gets BACH-style octave doubling)
    tracks_to_extract = 2 if mode == '2' else 3

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

    midi_tempo = get_midi_tempo(mid)
    bpm = 60_000_000 / midi_tempo
    dur = compute_dur_byte(midi_tempo)

    # Per-cell step values for each voice (0 = silent for that cell)
    voice_steps = []
    for vt in voice_notes:
        steps = []
        for c in range(n_cells):
            t0 = c * cell_ticks
            t1 = (c + 1) * cell_ticks
            n = note_at_cell(vt, t0, t1)
            steps.append(midi_to_step(n) if n is not None else 0)
        voice_steps.append(steps)

    # Build the full V1..V4 arrays plus the timbre tuple, depending on mode.
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
    if mode == '2':
        v1, v2 = voice_steps
        v3, v4 = list(v1), list(v2)
        timbres = (0, 1, 2, 3)
    elif mode == '3':
        v1, v2, v3 = voice_steps
        v4 = [0] * n_cells
        timbres = (0, 1, 2, 0)
    else:  # '2of3'
        sop, alt, bas = voice_steps
        v1 = sop
        v2 = alt
        v3 = list(sop)
        v4 = bas
        timbres = (1, 0, 3, 2)

    # ---- emit .MUS command stream ----
    cmds = []

    # Cmd 0: full setup (bits 0x3F = 4 pitches + 2 timbre words + tempo)
    cmds.append((0x3F << 8) | dur)
    cmds.append(v1[0])
    cmds.append(v2[0])
    cmds.append(v3[0])
    cmds.append(v4[0])
    v12 = ((0x81 + timbres[1]) << 8) | (0x81 + timbres[0])
    v34 = ((0x81 + timbres[3]) << 8) | (0x81 + timbres[2])
    cmds.append(v12)
    cmds.append(v34)
    cmds.append(TEMPO_BYTE)

    # Subsequent commands: bit-encoded per-voice changes.  In 2-voice mode,
    # bit 0 and bit 2 always flip together (since v3==v1), and bit 1 and bit 3
    # always flip together (since v4==v2), reproducing the BACH1.MUS pattern
    # of 0x05 / 0x0A / 0x0F bits.  In 3-voice mode each voice is independent
    # so any combination of bits 0..2 is possible; bit 3 never fires.
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
            cmds.append((bits << 8) | dur)
            if bits & 0x01: cmds.append(v1[i])
            if bits & 0x02: cmds.append(v2[i])
            if bits & 0x04: cmds.append(v3[i])
            if bits & 0x08: cmds.append(v4[i])
            i += 1
        else:
            # Hold run: cells with no change in any voice
            j = i
            while (j < n_cells
                   and v1[j] == v1[i - 1] and v2[j] == v2[i - 1]
                   and v3[j] == v3[i - 1] and v4[j] == v4[i - 1]):
                j += 1
            held_cells = j - i
            samples_to_hold = held_cells * dur
            while samples_to_hold > 0:
                chunk = min(255, samples_to_hold)
                chunk = (chunk // dur) * dur
                if chunk == 0:
                    chunk = dur
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
        '2':    '2-voice (BACH style: V1+V3, V2+V4 doubled)',
        '3':    '3-voice (V1, V2, V3 independent; V4 silent)',
        '2of3': '2of3 sinfonia (V1+V3 soprano fund+octave, V2 alto, V4 bass)',
    }[mode]
    print(f"  source:        {mid_path}")
    print(f"  mode:          {mode_label}")
    print(f"  ppqn:          {ppqn}")
    print(f"  cell:          {cell_ticks} MIDI ticks ({cell_name} note, CELL_DIV={CELL_DIV})")
    print(f"  cells total:   {n_cells}")
    print(f"  MIDI tempo:    {bpm:.1f} BPM ({midi_tempo} us/quarter)")
    print(f"  dur byte:      {dur}  ({dur*TEMPO_BYTE/SAMPLE_RATE*1000:.2f} ms per cell)")
    print(f"  tuning offset: {TUNING_CENTS:+d} cents")
    print(f"  output:        {mus_path}  ({len(data)} bytes, {len(cmds)} words)")


# ---------- CLI -----------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('source_mid')
    ap.add_argument('output_mus')
    ap.add_argument('--voices', default='2', choices=['2', '3', '2of3'],
                    help="2 = invention (V1+V3, V2+V4 doubled); "
                         "3 = sinfonia faithful (V1,V2,V3; V4 silent); "
                         "2of3 = sinfonia w/ soprano octave-doubled (V1+V3 sop, V2 alto, V4 bass)")
    args = ap.parse_args()
    convert(args.source_mid, args.output_mus, args.voices)


if __name__ == '__main__':
    main()
