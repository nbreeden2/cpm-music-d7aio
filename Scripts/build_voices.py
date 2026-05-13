"""build_voices.py - Assemble a 6-page VOICES.MUS from a library of timbres.

PLAY.COM, PLAYCDOS, and PLAYZ80 all expect VOICES.MUS to be exactly
1536 bytes (6 wavetable pages of 256 signed-8-bit samples each).  This
script lets you swap individual pages without changing that layout, so
the player and every existing .MUS file keep working unchanged.  The
intended use is one VOICES.MUS per CP/M disk image -- the cello-suite
disk gets a cello-flavored slot 2, the Bach disk keeps the original
skewed-saw, and so on.

Available voices
================
Six come from the original CDOS VOICES.MUS (read verbatim from
Original_CPM_Files/VOICES.MUS):

    sine        slot 0   pure sine
    even_harm   slot 1   even-harmonic double-hump
    saw         slot 2   skewed saw
    oct_up      slot 3   octave-shifter (weak fundamental)
    square      slot 4   pure square
    three_cyc   slot 5   three-cycle hybrid (octave+fifth shifter)

Synthetic voices are listed below in VOICE_LIBRARY.

Usage
=====
Build a complete 6-slot bank by naming each slot:

    python build_voices.py -o OUT.MUS \\
        --slots sine even_harm cello1 oct_up square three_cyc

Or start from an existing bank and replace one slot:

    python build_voices.py -o OUT.MUS \\
        --base Original_CPM_Files/VOICES.MUS --replace 2=cello1

List the library, or audition a single voice as a 3-second A4 WAV:

    python build_voices.py --list
    python build_voices.py --audition cello1 -o cello1_A4.wav
"""

import argparse
import math
import struct
import sys
import wave
from pathlib import Path

from _paths import ORIGINAL_DISK, VOICES_MUS

PAGE = 256
N_SLOTS = 6
SAMPLE_RATE = 11169       # calibrated D+7AIO rate; used for auditioning only
PEAK = 60                 # signed-8-bit headroom per voice (matches original)


# ---------- synthetic voice generators -------------------------------------

def synth_cello(lowpass_corner: float = 10.0,
                formant_amp: float = 0.5,
                formant_center: float = 3.0,
                formant_width: float = 2.0,
                n_harmonics: int = 20) -> bytes:
    """Cello-flavored wavetable, parameterized.

    Built from a sawtooth-style additive series (a_n = 1/n -- Helmholtz
    motion of a bowed string), with two shaping factors:

      formant emphasis : 1 + formant_amp * exp(-((n - center) / width)**2)
                         -- Gaussian boost centered on a harmonic where a
                            real cello's body resonance might live for
                            mid-range notes.  (NB: the 'formant' moves
                            with pitch in wavetable synthesis -- this
                            only approximates the colour of a real
                            fixed-frequency body resonance, can't
                            reproduce it.)

      low-pass         : 1 / (1 + (n / lowpass_corner)**4)
                         -- 4th-order soft low-pass.  Tames the harsh
                            upper saw harmonics without making the
                            timbre dull; lower corner = darker.

    All harmonics in sine phase (zero at i=0).  Peak-normalized to +/-PEAK
    so two-voice sums never exceed the 8-bit DAC's +/-127 range.
    """
    samples = [0.0] * PAGE
    for n in range(1, n_harmonics + 1):
        base = 1.0 / n
        formant = 1.0 + formant_amp * math.exp(
            -((n - formant_center) / formant_width) ** 2)
        lowpass = 1.0 / (1.0 + (n / lowpass_corner) ** 4)
        amp = base * formant * lowpass
        for i in range(PAGE):
            samples[i] += amp * math.sin(2.0 * math.pi * n * i / PAGE)
    peak = max(abs(s) for s in samples)
    scale = PEAK / peak
    return _quantize(samples, scale)


def synth_cello1() -> bytes:
    """Baseline cello: bright (low-pass at H10), strong formant (0.5 @ H3)."""
    return synth_cello(lowpass_corner=10.0, formant_amp=0.5)


def synth_cello2() -> bytes:
    """Darker than cello1 (low-pass at H7); formant unchanged."""
    return synth_cello(lowpass_corner=7.0, formant_amp=0.5)


def synth_cello3() -> bytes:
    """Darker than cello1 (low-pass at H7) AND gentler formant (0.25 @ H3)."""
    return synth_cello(lowpass_corner=7.0, formant_amp=0.25)


def synth_pulse(duty: float = 0.5) -> bytes:
    """Pulse wave with adjustable duty cycle.

      duty = 0.50  -> pure square (odd harmonics only, amplitude 1/n).
                      Already in the original VOICES.MUS at slot 4.
      duty = 0.25  -> classic Game Boy / NES "thin pulse" lead.  Has both
                      odd AND even harmonics with notches at every 4th
                      harmonic; sounds brighter and "thinner" than a 50%
                      square but less buzzy because the spectrum is
                      different in character.
      duty = 0.125 -> very sharp "spike" pulse; nasal / piercing.

    Peak-normalized to +/-PEAK; the wave is a hard step so wrap and
    transition discontinuities are large (=2*PEAK), but no larger than
    the original square voice already at slot 4.
    """
    samples = [0.0] * PAGE
    pulse_end = max(1, min(PAGE - 1, int(PAGE * duty)))
    for i in range(PAGE):
        samples[i] = 1.0 if i < pulse_end else -1.0
    return _quantize(samples, PEAK)


def synth_pulse25() -> bytes:
    """25% duty pulse -- classic chiptune lead alternative to pure square."""
    return synth_pulse(0.25)


def synth_pulse12() -> bytes:
    """12.5% duty pulse -- piercing / nasal chiptune lead."""
    return synth_pulse(0.125)


def synth_triangle() -> bytes:
    """Triangle wave -- NES / Game Boy bass voice.

    Pure analog triangle (not the NES's 16-step staircase): linear ramp
    up to peak at i=PAGE/4, down through zero at i=PAGE/2, to trough at
    i=3*PAGE/4, then back up to ~0 by i=PAGE-1 ready for the wrap.

    Useful as a bass voice in chiptune-style music where a pure square
    on every voice gets too buzzy.  Triangle has odd-harmonic content
    like square but with amplitudes falling as 1/n^2 (vs square's 1/n)
    -- so it sounds softer / less edgy / less "buzzy" while still
    carrying clear pitched bass content.
    """
    samples = [0.0] * PAGE
    for i in range(PAGE):
        phase = 4.0 * i / PAGE          # 0..4 over one cycle
        if phase < 1:
            samples[i] = phase           # 0 -> +1
        elif phase < 3:
            samples[i] = 2.0 - phase     # +1 -> -1
        else:
            samples[i] = phase - 4.0     # -1 -> 0
    return _quantize(samples, PEAK)


def _quantize(samples, scale):
    """Round float samples to signed 8-bit, clamp, return as little-endian
    page (each byte is two's-complement signed-8-bit)."""
    out = bytearray(PAGE)
    for i, s in enumerate(samples):
        v = round(s * scale)
        if v < -128: v = -128
        if v > 127:  v = 127
        out[i] = v & 0xFF
    return bytes(out)


# ---------- voice registry -------------------------------------------------

ORIGINAL_NAMES = ['sine', 'even_harm', 'saw', 'oct_up', 'square', 'three_cyc']
SYNTHETIC = {
    'cello1':   synth_cello1,
    'cello2':   synth_cello2,
    'cello3':   synth_cello3,
    'triangle': synth_triangle,
    'pulse25':  synth_pulse25,
    'pulse12':  synth_pulse12,
}


def list_voices():
    """Return a list of (name, source_description) tuples."""
    out = []
    for i, n in enumerate(ORIGINAL_NAMES):
        out.append((n, f'original VOICES.MUS slot {i}'))
    for n in SYNTHETIC:
        out.append((n, 'synthetic'))
    return out


def get_voice(name: str) -> bytes:
    """Return the 256-byte wavetable for the named voice."""
    if name in SYNTHETIC:
        return SYNTHETIC[name]()
    if name in ORIGINAL_NAMES:
        idx = ORIGINAL_NAMES.index(name)
        raw = VOICES_MUS.read_bytes()
        if len(raw) < (idx + 1) * PAGE:
            sys.exit(f"error: {VOICES_MUS} is only {len(raw)} bytes; "
                     f"slot {idx} needs at least {(idx + 1) * PAGE}")
        return raw[idx * PAGE:(idx + 1) * PAGE]
    sys.exit(f"error: unknown voice {name!r}; "
             f"run with --list to see available voices")


# ---------- build ----------------------------------------------------------

def build_bank(slot_names: list) -> bytes:
    if len(slot_names) != N_SLOTS:
        sys.exit(f"error: need exactly {N_SLOTS} slot names, got {len(slot_names)}")
    return b''.join(get_voice(n) for n in slot_names)


def parse_replace(spec: str):
    """Parse 'IDX=NAME' into (int, str)."""
    if '=' not in spec:
        sys.exit(f"error: --replace expects IDX=NAME, got {spec!r}")
    idx_s, name = spec.split('=', 1)
    try:
        idx = int(idx_s)
    except ValueError:
        sys.exit(f"error: --replace slot index {idx_s!r} is not an integer")
    if not 0 <= idx < N_SLOTS:
        sys.exit(f"error: --replace slot index {idx} out of range 0..{N_SLOTS - 1}")
    return idx, name


def build_from_base(base_path: Path, replacements: list) -> bytes:
    """Read base VOICES.MUS, override the listed slots, return 1536 bytes."""
    raw = base_path.read_bytes()
    if len(raw) != N_SLOTS * PAGE:
        sys.exit(f"error: base file {base_path} is {len(raw)} bytes, expected {N_SLOTS * PAGE}")
    out = bytearray(raw)
    for spec in replacements:
        idx, name = parse_replace(spec)
        out[idx * PAGE:(idx + 1) * PAGE] = get_voice(name)
    return bytes(out)


# ---------- audition -------------------------------------------------------

def audition_voice(name: str, out_wav: str, duration_sec: float = 3.0,
                   note_freq: float = 440.0):
    """Render a single voice playing one tone to a mono WAV at SAMPLE_RATE."""
    table = get_voice(name)
    step = round(note_freq * 65536.0 / SAMPLE_RATE) & 0xFFFF
    n_samples = int(SAMPLE_RATE * duration_sec)
    phase = 0
    pcm = bytearray()
    for _ in range(n_samples):
        phase = (phase + step) & 0xFFFF
        b = table[phase >> 8]
        if b >= 128:
            b -= 256
        pcm += struct.pack('<h', b * 256)   # scale 8-bit -> 16-bit
    with wave.open(out_wav, 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(bytes(pcm))
    print(f"wrote {out_wav}: {name} at {note_freq:.1f} Hz for {duration_sec:.1f} s")


# ---------- CLI ------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--list', action='store_true',
                    help='list available voice names and exit')
    ap.add_argument('--audition', metavar='NAME',
                    help='render a 3-second A4 tone of this voice to --out (.wav)')
    ap.add_argument('--slots', nargs=N_SLOTS, metavar='NAME',
                    help=f'name {N_SLOTS} slots explicitly (slot 0 .. slot {N_SLOTS - 1})')
    ap.add_argument('--base', type=Path, default=VOICES_MUS,
                    help='base VOICES.MUS to start from (default: Original_CPM_Files/VOICES.MUS)')
    ap.add_argument('--replace', action='append', default=[], metavar='IDX=NAME',
                    help='replace slot IDX of --base with voice NAME (can repeat)')
    ap.add_argument('-o', '--out', metavar='PATH',
                    help='output path (.MUS for bank, .wav for --audition)')
    args = ap.parse_args()

    if args.list:
        print(f"{'name':12} source")
        print('-' * 50)
        for name, source in list_voices():
            print(f"{name:12} {source}")
        return

    if args.audition:
        if not args.out:
            sys.exit("error: --audition needs -o OUT.wav")
        audition_voice(args.audition, args.out)
        return

    if not args.out:
        sys.exit("error: -o OUT.MUS is required")

    if args.slots:
        if args.replace:
            sys.exit("error: --slots and --replace are mutually exclusive")
        data = build_bank(args.slots)
        sources = args.slots
    else:
        if not args.replace:
            sys.exit("error: pass either --slots NAME...NAME or --replace IDX=NAME")
        data = build_from_base(args.base, args.replace)
        sources = [f'(from {args.base.name})'] * N_SLOTS
        for spec in args.replace:
            idx, name = parse_replace(spec)
            sources[idx] = name

    Path(args.out).write_bytes(data)
    print(f"wrote {args.out}: {len(data)} bytes ({N_SLOTS} x {PAGE})")
    for i, s in enumerate(sources):
        print(f"  slot {i}: {s}")


if __name__ == '__main__':
    main()
