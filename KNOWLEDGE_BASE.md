# CP/M Music Player — Knowledge Base

A single-file reference covering everything we know about the Cromemco CDOS
"music player" (PLAY.COM) and its CP/M 2.2 ports.  Audience: anyone working
on the player, the file format, or an emulator that needs to reproduce the
audio faithfully (notably the High Nibble IMSAI 8080 emulator).

Deep-dive companions on disk:
- `PLAY_COM_ANALYSIS.md` — full Z80 disassembly + analysis of PLAY.COM.
- `VOICES_MUS_ANALYSIS.md` — wavetable bank shapes, harmonics, headroom.
- `PLAYCDOS.MAC` — Z80 source that reassembles bit-perfect to PLAY.COM.
- `PLAY8080.MAC` / `PLAYZ80.MAC` — CP/M 2.2 ports (8080 + Z80).

---

## 1. Overview

**The player** is a Cromemco-era 4-voice wavetable music program for the
Cromemco D+7AIO analog interface card.  Each of four "Parts" (voices)
sweeps a 16-bit phase accumulator through a 256-byte single-cycle
wavetable; pairs of voices sum into two 8-bit DACs.  No real-time MIDI,
no envelopes, no portamento — just four parallel oscillators reading
from one of six pre-baked wavetables, plus a tempo knob.

**The four variants now on disk:**

| File | Host OS | CPU | Mix loop | Status |
|---|---|---|---|---|
| `PLAY.COM` | Cromemco CDOS | Z80 | original | binary only, 1408 bytes |
| `PLAYCDOS.MAC` | Cromemco CDOS | Z80 | byte-perfect to PLAY.COM | reassembles bit-identical |
| `PLAY8080.MAC` | CP/M 2.2 | 8080 | structurally similar | works on IMSAI 8080 |
| `PLAYZ80.MAC` | CP/M 2.2 | Z80 | bytes 0562h..0621h byte-identical to PLAY.COM | works on physical CDOS-style hardware |

PLAYZ80 is the most useful build for the modern user: it runs on stock
CP/M 2.2, sounds identical to the original CDOS PLAY.COM on the same
hardware, and has all the modern conveniences (in-program filename
parser, interactive params-change UI, etc.) that CDOS-specific code in
PLAY.COM relied on the BDOS for.

---

## 2. Hardware Platform

### 2.1 Cromemco D+7AIO card

S-100 analog interface, base port 18h.  This player uses two of the
seven analog output channels:

| Port | Channel | Drives |
|---|---|---|
| `19h` (AN1) | analog channel 1 | Voices 1 + 2 (summed in software) |
| `1Bh` (AN3) | analog channel 3 | Voices 3 + 4 (summed in software) |

Outputs are 8-bit signed (two's complement), nominal range ±127, but
the wavetables are kept inside ±60 so two-voice sums never clip.

### 2.2 The D+7AIO WAIT state (critical for emulator parity)

The D+7AIO card asserts the S-100 **PRDY** line for ~5 µs after each
`OUT (n),A` to one of its DAC ports.  The Z80 / 8080 idles in that
period — on the IMSAI front panel this manifests as the **WAIT LED**
glowing dimly during music playback (steady-state visible-dim
brightness means the CPU is in WAIT for a meaningful fraction of each
cycle).

This is **not optional**.  It's how the DAC manufacturer guaranteed
the analog output had time to settle before the next write.  Software
that targets the D+7AIO — including PLAY.COM — was written assuming
the WAIT exists, and runs faster than designed if it doesn't.

**Why this matters for emulators:**

| Quantity | Physical D+7AIO | Emulator without WAIT |
|---|---|---|
| Sample rate | ~11,169 Hz | ~12,500 Hz |
| BACH8.MUS runtime | 43.7 sec | ~38.6 sec |
| Pitch (A4 target) | 440 Hz | ~493 Hz (+5.7 semitones) |

The ~5 second runtime difference and the 1.13× pitch shift come from
the same source.  For BACH8.MUS specifically: 1,010,400 port writes
× 5 µs WAIT each = 5.05 sec of CPU idle that the emulator skips.

### 2.3 BACH8.MUS as a calibration target

Empirical port-write counts on BACH8.MUS (from emulator instrumentation):

- 505,200 writes to port 19h
- 505,200 writes to port 1Bh
- **1,010,400 total port writes**
- × 5 µs WAIT each = **5.05 seconds of WAIT-induced delay**
- Physical hardware runtime: **43.7 seconds**
- Predicted emulator runtime *without* WAIT: 43.7 − 5.05 = **38.65 sec**

If your emulator plays BACH8.MUS in ~38.6 sec instead of ~43.7 sec,
that's the WAIT signal.  Add a 5 µs stall on every OUT to 19h/1Bh
(more generally, every OUT to a D+7AIO DAC port: 19h, 1Bh, 1Dh, 1Fh)
and pitch + duration should both come into line.

### 2.4 Reference host

Calibration was done on a physical system consisting of:

- a Cromemco D+7AIO analog interface card,
- a Cromemco ZPU CPU card (4 MHz Z80),
- an SDH-100 hardware emulator providing RAM and floppy-controller
  emulation,

all installed in an IMSAI 8080 chassis on the S-100 bus.

### 2.5 Minimal audio mixer

The D+7AIO presents two analog outputs (port 19h = channel 1 carries
V1+V2, port 1Bh = channel 3 carries V3+V4).  To drive a single mono
amplifier they have to be summed externally.  A passive three-part
network suffices:

```
   DAC1 (port 19h) ─────[ R1 = 10 kΩ ]─────┐
                                            │
                                            ├──● Audio Out ──── audio jack tip + ring
                                            │                   (L and R tied → mono)
   DAC2 (port 1Bh) ─────[ R2 = 10 kΩ ]─────┘
                                            │
                                       [ C1 = 10 nF ]
                                            │
                                            ▼
                                       analog GND
                                      (D+7AIO ref)
```

**Component roles:**

- **R1, R2 (10 kΩ each):** passive 2-input voltage summer.  The
  junction sees `(DAC1 + DAC2) / 2`.  Source impedance at the
  junction = R1 ‖ R2 = **5 kΩ**.
- **C1 (10 nF, Audio Out → GND):** reconstruction / anti-imaging
  low-pass filter.  Corner frequency:
  `f_c = 1 / (2π × 5 kΩ × 10 nF) ≈ 3.2 kHz`.
- **GND:** must be the D+7AIO's **analog ground**, not the S-100
  digital ground.  The card brings analog and digital grounds out
  separately to keep DAC switching noise off the audio reference.
- **Output:** Audio Out drives both L and R conductors of a 1/8"
  stereo jack tied together; the speakers play mono.  No level pot
  needed — powered speakers have their own volume control.

**What the LPF does:**

The 3.2 kHz corner sits below the player's Nyquist (5.58 kHz at
SR = 11,169), so C1 acts as both anti-imaging and treble shaping:

1. **Anti-imaging.** The DAC's 11.2 kHz stair-step output has
   spectral copies of the audio centered on 11.2 kHz and 22.4 kHz.
   The LPF rolls them off by ~11 dB at 11.2 kHz and ~20 dB at
   22.4 kHz — not a brick wall, but enough that the imaging
   doesn't dominate.
2. **Treble shaping.** A4 fundamental plus the first three
   harmonics (440 / 880 / 1320 / 1760 Hz) pass essentially flat;
   content above ~3 kHz rolls off at -20 dB/decade.  Subjectively
   the staircase is smoothed and the "digital hash" character is
   tamed.

This is the mixer used on the reference hardware that produced the
SR = 11,169 Hz calibration in §6.1.

---

## 3. The `.MUS` File Format

A `.MUS` file is a little-endian 16-bit word stream consumed as a
**stack** by the mix loop — the player redirects `SP` into the file
image and uses `POP` instructions to pull commands and parameters.

### 3.1 First command (offset 0..15)

The first command always sets all four voices' pitches, all four
timbres, and the tempo.  This puts everything an .MUS file needs at
predictable byte offsets, which is what the interactive
"change-starting-parameters" UI in PLAY / PLAYCPM / PLAYZ80 patches.

| Offset | Bytes | Meaning |
|---|---|---|
| 0..1  | dispatch (`0x3F`) + duration | first-command word |
| 2..3  | V1 step (16-bit phase increment) |
| 4..5  | V2 step |
| 6..7  | V3 step |
| 8..9  | V4 step |
| 10    | V1 timbre byte (`0x81 + idx`) |
| 11    | V2 timbre byte |
| 12    | V3 timbre byte |
| 13    | V4 timbre byte |
| 14    | tempo byte (inner-loop sample count per "tick") |
| 15    | tempo high byte (unused, conventionally 0) |

### 3.2 Generic command word

Each command is one 16-bit word `(bits, dur)`:

```
hi byte = dispatch bits      lo byte = duration in ticks
```

Dispatch bits (low → high):

| Bit | If set, next words are |
|---|---|
| 0 | V1 step (1 word) |
| 1 | V2 step (1 word) |
| 2 | V3 step (1 word) |
| 3 | V4 step (1 word) |
| 4 | V1+V2 timbres (1 word: lo=V1 byte, hi=V2 byte), then V3+V4 timbres (1 word) |
| 5 | tempo word (1 word, low byte used) |
| 6 | (unused) |
| 7 | (unused) |

A command with `bits = 0` is "hold the current chord for `dur` more
ticks" — useful as a sustain.

**End-of-song marker:** a command word with `dur = 0`.  PLSNG's
`NXCMD` dispatcher recognizes this and returns to the caller.

### 3.3 Position-independent voice encoding

Timbre bytes in the song stream are stored as `0x81 + index` (so
voices 0..5 ride at 0x81..0x86).  At PLSNG entry the dispatcher
patches a `SUB n` immediate in the inner loop so this number maps
onto `HIGH(VLOAD) + index` — i.e., the high byte of the chosen
wavetable's memory address.  The constant `n` is computed at runtime
from where VOICES.MUS got loaded, so the same .MUS files work no
matter where VOICES.MUS lives in memory.

### 3.4 Stack-based decode

The mix loop swaps `SP` to the song-stream base before pulling
commands:

```asm
LD   SP,(SADDR)      ; SP -> song base
NXCMD: POP   BC      ; B = dispatch bits, C = duration
       XOR   A
       OR    C
       JP    Z,end   ; dur=0 -> end of song
       JP    DSPCMD  ; else dispatch per bit
```

`DSPCMD` shifts B right one bit at a time; on each carry it does a
`POP HL` to consume the next parameter word.  The "stack" is just
the song stream marching forward in memory.

This is **why no subroutine `CALL`s are allowed inside the playback
section** — any `CALL` would push its return address onto whatever
`SP` is currently pointing at (which is *the song stream*), corrupting
the song.  Everything in PLSNG is inline.

---

## 4. Mix-loop Algorithm

The heart of the player is a tight phase-accumulator loop at memory
0562h..0621h.  These 192 bytes are **byte-identical between PLAY.COM,
PLAYCDOS.COM, and PLAYZ80.COM**.  That's the design constraint that
makes the three sound the same: the loop body, the byte addresses of
the self-modified operands, and the wedge-state spacing are all
literally the same machine code.

**Why this matters.** The inner loop is what produces the byte stream
that goes out to the two DACs (channel 1 at port 19h, channel 3 at
port 1Bh).  If the instructions are byte-identical and the CPU is the
same model at the same clock with the same WAIT-state behavior, then
the *byte stream is identical at every output port write* and the
*time between writes is identical*.  In other words: the audio that
PLAYZ80 produces on a 4 MHz Z80 with a D+7AIO is bit-exactly what
PLAY.COM produces on the same machine.  No "close enough" — literally
the same waveform, sample-for-sample.

This is a stronger guarantee than "same algorithm."  Two
implementations of the same algorithm can produce subtly different
samples (different rounding order, different instruction timing
between OUTs).  Byte-identity rules that out by construction.

PLAY8080 is **not** part of this guarantee.  Its mix loop is
structurally similar but uses 8080 instructions, runs on a 2 MHz CPU,
and consequently runs at roughly half the sample rate of the Z80
versions on equivalent hardware (and has different per-OUT spacing,
which the D+7AIO WAIT then modulates differently).  PLAY8080 will sound
like PLAY.COM in *content* — same notes, same timbres, same tempo
relationships — but not in *audio fidelity*.  It is a different player
that happens to read the same file format.

### 4.1 Per-sample work

For each output sample:

```
For each voice v in [1, 2]:
    phase_v   += step_v                    ; 16-bit add, wraps mod 65536
    sample_v   = wavetable[v][phase_v >> 8]  ; high byte of phase indexes table
A = sample_1 + sample_2                     ; signed 8-bit add (sw mix)
OUT (19h), A                                ; channel 1 DAC

For each voice v in [3, 4]:
    phase_v   += step_v
    sample_v   = wavetable[v][phase_v >> 8]
A = sample_3 + sample_4
OUT (1Bh), A                                ; channel 3 DAC
```

The two software-summed pairs then mix acoustically at the speaker
(channel-1 + channel-3 ≈ 4-voice summed audio).

### 4.2 Loop hierarchy

Three nested loops control timing:

```
NXCMD:               ; one command from song stream
  DSPCMD             ; absorb dispatch bits + their parameters
  OUTITR:            ; outer "tick" loop -- runs `dur` times
    LD B,<tempo>     ; reload inner counter from tempo byte
    INRLP:           ; inner sample loop -- runs `tempo` times
      <per-sample work above>
      DEC B
      JP NZ,L05D4    ; wedge between samples
    DEC C            ; outer counter
    JP NZ,OUTITR
  JP NXCMD
```

So total samples per command = `tempo × dur`.  At SR ≈ 11,169 Hz that
gives the time scale: e.g. `tempo=240, dur=250` → 60,000 samples →
~5.37 seconds.

### 4.3 The L05D4 wedge

Between adjacent inner-loop samples the loop branches to a tiny
6-byte wedge:

```asm
L05D4:  NOP                  ; 4 T
        LD   A, 0            ; 7 T
        JP   INRLP           ; 10 T
        ; total = 21 T-states
```

This is **deliberate timing slack**.  It pins the per-sample CPU time
to a value the original designer wanted.  The wedge's 6-byte budget
is locked by the addresses of OUTITR (05DAh) and INRLP (05DCh),
which can't move — the SMC dispatcher patches immediates inside
INRLP at fixed absolute addresses (TMPIMM=05DBh, V1STIM=05E0h, etc).

### 4.4 Per-sample T-state budget (Z80, 4 MHz)

| Block | T-states |
|---|---|
| 4 × voice update (LD HL,nn + LD DE,nn + ADD HL,DE + LD (nn),HL + LD L,H + LD H,n + LD A,(HL) / ADD A,(HL)) | 4 × 65 = 260 |
| 2 × `OUT (n),A` | 2 × 11 = 22 |
| `DEC B` + `JP NZ,L05D4` | 14 |
| Wedge (NOP / LD A,0 / JP) | 21 |
| **CPU per sample** | **317 T = ~79.25 µs at 4 MHz** |
| 2 × D+7AIO WAIT @ 5 µs | 10 µs |
| **Total per sample** | **~89 µs → ~11,200 Hz** |

Measured on physical hardware: ~11,169 Hz.  The ~0.3 % gap suggests
the D+7AIO WAIT is closer to 5.1 µs in practice (or my T-state count is
off by ~1 T per sample — irrelevant either way).

### 4.5 Why the mix loop must stay byte-identical

Three reasons not to "improve" it:

1. **Sample rate** is determined by exact T-states.  Even a NOP swap
   changes the rate, which shifts pitch and tempo.
2. **SMC operand addresses** (TMPIMM at 05DBh, V1STIM..V4STIM,
   V1PGIM..V4PGIM) are referenced from outside (the PLSNG dispatcher
   patches them by absolute address).  Move any instruction and the
   dispatcher patches the wrong byte.
3. **Aural match** with PLAY.COM (the CDOS original) is the design
   contract for PLAYZ80.  Keep the bytes identical, sound is identical
   on equivalent hardware.

---

## 5. Wavetable Bank (`VOICES.MUS`)

6 wavetables × 256 bytes = 1536 bytes, loaded page-aligned.  Each is
a single cycle, signed 8-bit, peak bounded to ±60 so 2-voice sums
stay inside ±127.

| Voice byte | Index | Timbre | Notes |
|---|---|---|---|
| `0x81` | 0 | Pure sine | ±60, fundamental only |
| `0x82` | 1 | Even-harmonic double-hump | two peaks per cycle |
| `0x83` | 2 | Skewed saw |  |
| `0x84` | 3 | Octave-shifter | weak fundamental → perceived 1 octave up |
| `0x85` | 4 | Pure square | ±60 |
| `0x86` | 5 | Three-cycle hybrid (octave+fifth shifter) | three peaks per cycle |

Voices 3 and 5 deserve a callout: their wavetables have multiple
period-equivalent peaks within the 256-byte cycle, so a step value
that *would* play A4 with a sine plays an octave above (or octave +
fifth above) when these timbres are selected.  Composers use this as a
free transposition — patch the timbre, get a shifted octave without
changing pitch numbers.

This is why **only VOICE1.MUS and VOICE5.MUS (sine and square) are
useful for calibration** — those are the only timbres that produce
the literal frequency `step × SR / 65536`.  See §6.4 below for the
calibration workflow that uses them.

See `VOICES_MUS_ANALYSIS.md` for the harmonic content of each
wavetable.

---

## 6. Timing & Sample-Rate Calibration

### 6.1 Calibrated value (2026-05-09)

```
SAMPLE_RATE = 11,169 Hz
```

on a Cromemco ZPU (4 MHz Z80) + D+7AIO on SDH-based S-100 bus.

### 6.2 How it was determined

`compose_calibration.py` builds `CALIB.MUS`: a 30-second steady A4
(440 Hz target) on voice 1 (sine), parts 2-4 silent.  The step value
is computed for an assumed sample rate; the user plays the file on
physical hardware and measures the produced pitch:

```
R_actual = F_measured * 65536 / TEST_STEP
```

First-pass at SR_assumed = 11,429 (from VOICE1.MUS duration) →
TEST_STEP = 2523 → user measured 430 Hz → R_actual = 11,169 Hz.

Second pass at SR = 11,169 → TEST_STEP = 2582 = 0x0A16 → user measured
440 ± 1 Hz, duration 30.7 sec.  Locked.

### 6.3 Cross-checks

- T-state count predicts 11,200 Hz (within 0.3 % of measured).
- BACH8.MUS port-write count × 5 µs WAIT predicts a 5.05-sec
  difference between physical hardware and a WAIT-less emulator —
  the actual difference is ~5.1 sec.  Consistent.
- VOICE1.MUS recompiled at the new rate produces 440 Hz on
  hardware (confirmed independently).

### 6.4 VOICE1.MUS and VOICE5.MUS as calibration targets

`CALIB.MUS` is the canonical reference tone (30-second A4, voice 1),
but `VOICE1.MUS` and `VOICE5.MUS` from the `compose_voice_tests.py`
batch are also valid calibration files.  Both encode **A4 = 440 Hz**
on Part 1, with parts 2-4 silent, and both should measure 440 Hz on a
scope or audio tuner *if the player's sample rate is calibrated
correctly for the running hardware*.

**Why these two and not the others.** All six `VOICE*.MUS` files
encode the same step value (0x0A16 at SAMPLE_RATE = 11169), but each
picks a different timbre from `VOICES.MUS`:

| File | Timbre | Waveform shape over 256 wavetable bytes | Measured frequency |
|---|---|---|---|
| `VOICE1.MUS` | 0 (sine)               | **1 cycle**  | 440 Hz |
| `VOICE2.MUS` | 1 (even-harmonic hump) | 2 cycles     | 880 Hz |
| `VOICE3.MUS` | 2 (skewed saw)         | 1 cycle, asymmetric → harmonics dominate | varies, not 440 Hz |
| `VOICE4.MUS` | 3 (octave-shifter)     | 2 cycles, weak fundamental | 880 Hz |
| `VOICE5.MUS` | 4 (square)             | **1 cycle**  | 440 Hz |
| `VOICE6.MUS` | 5 (three-cycle hybrid) | 3 cycles, octave+fifth shifter | ~1320 Hz |

The phase accumulator's job is to step through one wavetable in 256
"phase units" — but the wavetable can contain any number of audible
cycles in those 256 samples.  Sine (timbre 0) and square (timbre 4)
are the only single-cycle wavetables, so they're the only ones whose
played fundamental matches the literal arithmetic `step × SR / 65536`.
Multi-peak wavetables produce an output whose perceived/measured
fundamental is a *multiple* of that — which is exactly the
V3/V5 "octave-trick" feature, useful for composers but useless for
calibration.

**Why use two when one is enough.** Independent measurements at the
same target frequency cross-check each other:

- **Both read 440 Hz** → sample rate is correctly calibrated, and the
  wavetable loader is healthy (correct voice byte → correct
  wavetable page).
- **Both read the same wrong frequency** → sample rate calibration is
  off; back-solve `R_actual = F_measured × 65536 / 0x0A16` and update
  `SAMPLE_RATE` everywhere.
- **One reads 440 Hz, the other doesn't** → something specific to one
  voice path is broken (e.g., the SMC `SUB n` operand for that voice
  index landed on the wrong byte, or VOICES.MUS only partially
  loaded, or wavetable 0 and wavetable 4 were swapped — this is
  exactly the kind of bug PLAYZ80's `LDFILE` issue produced when only
  the first two records of VOICES.MUS loaded).

**Bonus: waveform-shape validation on the scope.** VOICE1 should
trace a clean sine (smooth peak-to-peak swing); VOICE5 should trace a
clean square (flat tops, sharp transitions).  If a "sine" file is
producing a square (or vice versa), that proves the voice-byte
indexing is wrong — the player loaded the right pitch but the wrong
timbre — which is a different class of bug than a sample-rate
mismatch.

**Procedure for using VOICE1/VOICE5 as a calibration:**

1. Make sure the `.MUS` file on disk matches the currently-calibrated
   `SAMPLE_RATE` (regenerate with `python Scripts/compose_voice_tests.py`
   if in doubt).
2. `PLAYZ80 VOICE1.MUS` on hardware.  Skip the params prompt.
3. Probe DAC channel 1 (port 19h) with a scope or feed the speaker
   output to a tuner.
4. Expected: 440 Hz, clean sine shape, ~32 seconds runtime.
5. Repeat with VOICE5.MUS.  Expected: 440 Hz, clean square shape,
   ~32 seconds.
6. If pitches don't match 440 Hz, back-solve sample rate as in §6.5
   (the step value is `0x0A16` = 2582 — same as `CALIB.MUS`).

### 6.5 Recalibration procedure (for new hardware)

1. Edit `compose_calibration.py`: set `SAMPLE_RATE` to your best
   guess.
2. `python Scripts/compose_calibration.py` (writes
   `New_CPM_Files/CALIB.MUS`).
3. `PLAYZ80 CALIB.MUS` on the target hardware.  Skip params, 1 rep.
4. Measure played frequency with a tuner / scope / phone tuner app.
5. Compute `R_actual = F_measured * 65536 / TEST_STEP` (the script
   prints TEST_STEP).
6. Update `SAMPLE_RATE` to `R_actual` in:
   - `compose.py`, `compose_doremi.py`, `compose_song.py`,
     `compose_octave_steps.py`, `compose_octave_trick.py`,
     `compose_voice_tests.py`, `compose_calibration.py`
   - `analyze_voices.py`, `simulate.py`, `decode_mus.py`,
     `verify_octave_trick.py`
7. Re-run each `compose_*.py` to regenerate the `.MUS` files at the
   new rate.

---

## 7. The `.py` Toolchain

All in `MUSIC/Scripts/`.  Each reads `SAMPLE_RATE` from a constant
near the top and imports directory locations from `_paths.py`
(`Scripts/_paths.py` is the single source of truth for project
directory layout — update it in one place after a reorg).

| File | Purpose |
|---|---|
| `_paths.py` | Shared directory constants (PROJECT_ROOT, ORIGINAL_DISK, NEW_DISK, VOICE_TESTS, VOICES_ANALYSIS, VOICES_MUS, PLAY_COM) |
| `compose.py` | 4-voice composer (Bach-style minuet template) → `New_CPM_Files/CLAUDE.MUS` |
| `compose_doremi.py` | Diatonic ascent test (C1 → C7) → `Voice_Tests/` + `New_CPM_Files/` |
| `compose_song.py` | Single-melody transcription (from PNG) → `New_CPM_Files/SONG.MUS` |
| `compose_octave_trick.py` | Same composition with V3/V5 octave-trick on one part → `New_CPM_Files/OCTAVE.MUS` |
| `compose_octave_steps.py` | Power-of-2 step sweep (each step doubles freq) → both `Voice_Tests/` + `New_CPM_Files/` |
| `compose_voice_tests.py` | One file per timbre, steady A4 — for scope/tuner work → both `Voice_Tests/` + `New_CPM_Files/` |
| `compose_calibration.py` | CALIB.MUS — the 30-second 440 Hz reference tone → `New_CPM_Files/CALIB.MUS` |
| `simulate.py` | Sample-accurate WAV renderer (mix loop in Python).  `--voices` defaults to `Original_CPM_Files/VOICES.MUS` |
| `decode_mus.py` | Pretty-print a `.MUS` command-by-command |
| `analyze_voices.py` | Harmonic / waveform analysis → `voices_analysis/` |
| `plot_voices.py` | Matplotlib stacked plot of all 6 wavetables → `voices_analysis/voices_stacked.{png,svg}` |
| `sparkline_voices.py` | ASCII rendering of each wavetable |
| `check_symmetry.py`, `check_wrap.py`, `inspect_voice3.py` | Wavetable spot-checks (continuity, symmetry, byte-level inspect) |
| `verify_octave_trick.py` | Spectral verification of the V3/V5 octave-shift |
| `disasm.py` | Z80 linear-sweep disassembler harness (reads `Original_CPM_Files/PLAY.COM`) |
| `disasm_m80.py` | Generate a regenerated M80-format source (writes `PLAYCDOS_regenerated.MAC` to project root; do **not** clobber the hand-edited `New_CPM_Files/PLAYCDOS.MAC`) |
| `CPMFMT.PY` (top level) | Convert .MAC/.INC files to CP/M text format (CRLF + Ctrl-Z) |

### 7.1 `simulate.py` caveat

`simulate.py` reproduces the mix-loop math exactly, but its
sample-rate parameter is a free constant — it does *not* model the
T-state count of the real Z80 or the D+7AIO WAIT.  If you change the
hardware, you change the .py constant; the simulator faithfully
generates a WAV at *that* rate, which now corresponds to the new
hardware behavior.  The 100 % byte-equality validation against a
prior hardware capture is meaningful only at whatever rate the
capture was taken at — not a proof that the captured rate was correct.

---

## 8. PLAY.* Variant Differences

### 8.1 What's the same

All four variants share:
- The phase-accumulator mix loop algorithm.
- The same `.MUS` file format.
- The same `VOICES.MUS` wavetable bank.
- Two DACs: ports 19h (V1+V2) and 1Bh (V3+V4).

### 8.2 What differs

| | PLAY.COM / PLAYCDOS | PLAY8080 | PLAYZ80 |
|---|---|---|---|
| Host OS | CDOS | CP/M 2.2 | CP/M 2.2 |
| CPU | Z80 | 8080 | Z80 |
| Mix loop bytes | (canonical) | structurally similar, **not byte-identical** | bytes 0562h..0621h **byte-identical to PLAY.COM** |
| Filename parser | CDOS BDOS fn 86h | in-program (`read_filename`) | in-program (`PARSE`) |
| File load (LDFILE) | assumes DE preserved across BDOS | save/restore on stack | save/restore on stack |
| FCB layout | CDOS-style | CP/M 2.2 default FCB at 005Ch | same as PLAY8080 |
| Memory layout | runtime-computed via CDOS BFBAS | compile-time fixed | compile-time fixed (VLOAD=0700h, SBUF=0D00h) |
| Banner version | 00.02 (pinned) | 01.0N | 01.0N |

### 8.3 Why bytes 0562h..0621h are the constraint

That's the mix loop.  Pinning it byte-for-byte from PLAY.COM
guarantees:
1. Same instruction sequence → same T-state count → same sample rate
   on equivalent hardware.
2. Same SMC operand addresses → the dispatcher's absolute patches
   land in the right bytes.
3. Same wedge → same per-sample timing slack.

Everything *outside* that 192-byte window in PLAYZ80 is rewritten
for CP/M 2.2.  The point of byte-identity is **audio fidelity**, not
source-level cloning.

---

## 9. Gotchas / Lessons Learned

### 9.1 CP/M 2.2 BDOS clobbers user registers

DR CP/M 2.2's BDOS does not preserve `DE`, `HL`, `BC`, `IX`, or `IY`
across a `CALL 0005`.  CDOS's BDOS apparently did preserve `DE` for at
least some functions (notably `SETDMA` / function 26).

Consequence: code that looked correct on CDOS — like the original
`LDFILE` loop that reuses `DE` across back-to-back `SETDMA` / `RDSEQ`
calls — fails on CP/M 2.2 after the first iteration.  Symptom in
PLAYZ80: VOICES.MUS only loaded 2 records of 12, then the rest of
the program ran on garbage.  Took hours to find.

**Fix pattern:** save load address and FCB pointer on the program
stack (or in static memory) around every `CALL 0005`; never trust a
register to survive.  See `PLAY8080.MAC`'s `load_voices` for the
reference style, and `PLAYZ80.MAC`'s `LDFILE` for the same in Z80.

### 9.2 SP-swap pattern and CALL discipline

The mix loop redirects `SP` into the song stream so it can `POP`
commands.  Any `CALL` inside that region would push its return
address onto the song stream and corrupt the song.  Rule: **no
`CALL`s allowed between `LD SP,(SADDR)` and `LD SP,(SVDSP)`**.
Everything in the playback hot path is inline.

### 9.3 HL preservation around BDOS in interactive UIs

PLAY8080's `change_params` had a real bug in the tempo branch:
after `CALL puts / CALL read_yn`, HL was no longer pointing at
`song+14` (the tempo byte).  The "Present starting tempo" line read
random bytes from wherever BDOS left HL (consistently 0xC3 = JP
opcode, hence the "195" mystery), and the "New starting tempo" wrote
to the same garbage address.  Two-line fix (`PUSH H / POP H` around
the chgtempo prompt block).

This is a sibling of 9.1: any time you cross a BDOS call, you need to
either save/restore the registers you care about, or reload them
from a known source on the other side.

### 9.4 PLAYZ80's wedge can't easily slow down

If the calibrated sample rate is "too fast" and you'd like to bring
it back down to a target like 8 kHz, the only software knob is the
L05D4 wedge — and it's locked to 6 bytes by the surrounding mix loop's
fixed addresses.  At 4 MHz Z80 you can add maybe 24 T-states of NOPs
in 6 bytes; to drop from 11,169 Hz to 8 kHz you'd need ~144 T-states.
Doesn't fit.

The honest options are:

1. **Accept the hardware's natural rate.**  This is what we did, but
   with an important scope limit: we only re-encoded the `.MUS` files
   *we* created during this work via the `compose_*.py` scripts.  The
   original CDOS-era `.MUS` files on the disk image were generated by
   an unknown authoring tool calibrated for an unknown sample rate
   and we have no way to faithfully "recalibrate" them — there's no
   intermediate format to recompile from.  They were **not changed**:

   ```
   BACH1.MUS    BACH12.MUS   BACH13.MUS   BACH14.MUS   BACH15.MUS
   BACH2.MUS    BACH3.MUS    BACH4.MUS    BACH8.MUS
   ENT.MUS      GOLDEN.MUS   JILLA.MUS    LOVEBLUE.MUS MICHAEL.MUS
   ML.MUS       NEWWORLD.MUS POMP.MUS     TEST.MUS     VOICES.MUS
   ```

   These files play at whatever pitch the player's actual sample rate
   produces from their encoded step values.  On the current 11,169 Hz
   hardware, they sound ~5.7 semitones sharper than they did on
   whatever the original CDOS reference hardware was running.
   That's a fact of the file format, not a bug we can fix in the
   player.

2. **Break byte-identity** with PLAY.COM by extending the mix loop
   structure to make room for a counter loop in the wedge.
3. **Add hardware WAIT states** (memory waits, M1 wait, etc.) outside
   software's control.

Option 1 is what's currently in tree (for the files we made).
Options 2 and 3 were not taken.

### 9.5 Per-rebuild banner-version bump

Standing rule: bump the version string in `PLAY8080.MAC`'s `banner_msg`
and `PLAYZ80.MAC`'s `MBANR` every time you reassemble.  Without it,
debugging on physical hardware is miserable because you can't tell if
you're running the latest source or a stale binary.  PLAY.MAC and
PLAYCDOS.MAC stay pinned at "00.02" — they're bit-identical
reassemblies and any visible change breaks that contract.

---

## 10. Terminology Cheat-sheet

| Term | Meaning |
|---|---|
| **Voice** / **Part** | One of four parallel oscillators.  "Part 1..4" in the UI; "voice" in code/comments. |
| **Timbre** | One of six wavetables in VOICES.MUS.  Encoded as `0x81 + idx` in song streams. |
| **Step** / **Phase increment** | 16-bit value added to a voice's phase accumulator each sample.  Encodes pitch as `freq = step × SR / 65536`. |
| **Phase** | 16-bit accumulator per voice.  Wraps at 65536; the high byte indexes into the wavetable. |
| **Command** | 2-byte unit of the song stream: high byte = dispatch bits, low byte = duration in ticks. |
| **Tempo byte** | Inner-loop sample count per "tick".  Patched into the `LD B,n` immediate at TMPIMM=05DBh.  Larger = slower. |
| **Duration byte** | Outer-loop tick count for a command (C register reload).  `samples_per_command = tempo × duration`. |
| **Tick** | One outer-loop iteration = `tempo` samples = ~`tempo / SR` seconds. |
| **WAIT state** | D+7AIO's per-OUT delay (~5 µs at ports 19h and 1Bh).  Counts toward sample period. |
| **SR** / **Sample rate** | Actual rate of DAC writes.  Calibrated to 11,169 Hz on the reference hardware. |
| **SMC** | Self-modifying code.  The mix loop's `LD DE,n` operands and `SUB n` immediates are rewritten by the dispatcher each command. |
| **PLSNG** | Entry point of the playback section (0562h).  Patches SMC bytes, saves caller's SP, switches SP to song stream, runs loop until end-of-song. |
| **Wedge (L05D4)** | 6-byte timing pad between inner-loop samples.  Locks the per-sample T-state count. |
| **V3/V5 octave trick** | Selecting timbre 3 or 5 raises the perceived pitch by an octave (V3) or octave+fifth (V5) without changing the step value.  Composer feature, not a bug. |
| **The wedge can't grow** | The 192-byte mix loop window is fixed by SMC operand addresses; the wedge has 6 bytes of room and no more. |

---

## 11. References

Project layout (after the 2026-05-11 reorganization):

```
MUSIC/
├── KNOWLEDGE_BASE.md          (this file)
├── PLAY_COM_ANALYSIS.md       (full disassembly + analysis of PLAY.COM)
├── VOICES_MUS_ANALYSIS.md     (wavetable timbre analysis)
├── CPMFMT.PY                  (CP/M text-format converter)
├── Original_CPM_Files/        (CDOS-shipped disk image, preserved as-is)
│   ├── PLAY.COM
│   ├── VOICES.MUS
│   └── BACH*.MUS, ENT.MUS, GOLDEN.MUS, ... (18 originals)
├── New_CPM_Files/             (modern CP/M disk)
│   ├── PLAYCDOS.MAC / .COM    (bit-perfect Z80 reassembly source)
│   ├── PLAY8080.MAC / .COM    (8080 CP/M 2.2 port)
│   ├── PLAYZ80.MAC / .COM     (Z80 CP/M 2.2 port; mix loop byte-identical to PLAY.COM)
│   ├── M80.COM, L80.COM       (Microsoft assembler + linker)
│   ├── VOICES.MUS, BACH*.MUS  (originals copied here for playback)
│   └── CALIB / CLAUDE / DOREMI / OCTAVE / OCTAVES / SONG / VOICE1-6.MUS (regenerated)
├── Scripts/                   (all .py tooling)
│   └── _paths.py              (single source of truth for project paths)
├── Voice_Tests/               (timbre tests: .MUS + matching _sim.wav)
└── voices_analysis/           (analyze_voices.py / plot_voices.py outputs)
```

Annotated source/disassembly for PLAY.COM lives in
`New_CPM_Files/PLAYCDOS.MAC` (the M80 source) — heavily commented with
addresses, bytes, and SMC patch points.  Reassembles bit-identical to
`Original_CPM_Files/PLAY.COM`.

In agent memory (`.claude/projects/d--VisualStudio-MUSIC/memory/`):

- `play_com_analysis.md` — short summary of the PLAY.* family.
- `hardware_sample_rate.md` — calibration value, derivation, recalibration recipe.
- `bdos_register_clobbering.md` — the CDOS-vs-CP/M-2.2 register-preservation gotcha.
- `mus_authoring.md` — composer toolchain pointers.
- `voices_mus_analysis.md` — wavetable analysis pointer.
- `composer_project_design.md` — design notes for the in-progress
  BDS-C tracker / Windows MIDI importer.
- `feedback_cpmfmt.md` — CPMFMT.PY rule.
- `feedback_playcpm_versioning.md` — banner-version bump rule.

---

*Last updated 2026-05-11.  Calibration verified against a physical
system using a Cromemco D+7AIO, a Cromemco ZPU @ 4 MHz, and an
SDH-100 hardware emulator (RAM, floppy controller), all installed in
an IMSAI 8080 S-100 chassis.*
