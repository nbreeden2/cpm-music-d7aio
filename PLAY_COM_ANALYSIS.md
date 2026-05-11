# `PLAY.COM` — CP/M Music Player Analysis

Reverse-engineering notes for the `PLAY.COM` program and `*.MUS` data files
shipped on the `music.unpacked` disk image. Intended as reference material
for the CPMEMU project (sound-card / D+7A I/O work).

- **File:** `MUSIC/music.unpacked/0/PLAY.COM`  (1408 bytes)
- **Companion data files (same directory):**
  - `VOICES.MUS` (1536 bytes) — waveform table bank, loaded once at startup
  - `BACH1.MUS`, `BACH2.MUS`, ..., `BACH15.MUS`, `ENT.MUS`, `GOLDEN.MUS`,
    `JILLA.MUS`, `LOVEBLUE.MUS`, `MICHAEL.MUS`, `ML.MUS`, `NEWWORLD.MUS`,
    `POMP.MUS`, `TEST.MUS` — song files
- **Program self-identifies as:** *"Music Player, version 00.02"*
- **Welcome banner:** *"Welcome to the Wonderful World of COMPUTER MUSIC"*

---

## Conventions

This document uses these terms with strict consistency.

- **Part** — one of PLAY.COM's 4 simultaneous playback slots. The
  player names them "Parts" in its own UI ("New voice for Part 1?").
  Each Part has its own phase accumulator, pitch (`step`), and chosen
  wavetable. Numbered **1–4**.
- **Wavetable** (a.k.a. **timbre**, a.k.a. **voice**) — one of the 6
  256-byte single-cycle waveforms bundled in `VOICES.MUS`. Each is a
  different tone color. There are always **6** wavetables. Internal
  indexing is 0–5 (matching the byte encoding `0x81 + idx` in the
  song stream); human-readable references can be 1–6 — same things.
  The three synonyms are interchangeable, but **never** use "voice"
  to mean a Part.
- **DAC** — Digital-to-Analog Converter. (Sometimes written D/A or
  "D2A" in older literature; same thing.) PLAY.COM uses 2 of the 7
  analog DACs on the Cromemco D+7A I/O card: port `19h` (DAC 1) and
  port `1Bh` (DAC 2). Each takes one signed 8-bit sample per write
  and outputs a corresponding analog voltage.
- **Mix** — when used here, means the *software* addition of two
  Parts' 8-bit signed samples into one DAC byte just before the `OUT`
  instruction. It produces the audio sum of both Parts (you hear both
  at once), not a synthesized hybrid timbre.
- **Step** — the 16-bit phase increment for a Part's phase
  accumulator. Determines pitch (see §3.3).

DAC routing is fixed in PLAY.COM:

```
Parts 1 + 2 ── software sum ──> DAC 1 (port 19h)
Parts 3 + 4 ── software sum ──> DAC 2 (port 1Bh)
```

The two DAC outputs are intended to be wired together externally into
a single mono audio stream. PLAY.COM is not a stereo program — the
two-DAC split exists for headroom (avoids 8-bit overflow when summing
4 Parts into one byte), not spatial separation.

---

## 1. Host requirements

### 1.1 CPU

`PLAY.COM` is a **Z80** program, not 8080. Confirmed by the presence of
Z80-only opcodes throughout the binary:

| Bytes seen   | Z80 instruction                  |
|--------------|----------------------------------|
| `DD 2A …`    | `LD IX,(nn)` (IX register)       |
| `DD 7E nn`   | `LD A,(IX+d)`                    |
| `DD 77 nn`   | `LD (IX+d),A`                    |
| `ED 73 nn nn`| `LD (nn),SP`                     |
| `ED 7B nn nn`| `LD SP,(nn)`                     |
| `ED 5B nn nn`| `LD DE,(nn)`                     |
| `ED 52`      | `SBC HL,DE`                      |
| `ED 4B nn nn`| `LD BC,(nn)`                     |
| `CB 18`      | `RR B`                           |
| `28 nn`,`30 nn`,`38 nn` | `JR cc,e`              |

It will not run on an 8080-only system (e.g. an unmodified IMSAI 8080
without a Z80 daughter card).

### 1.2 OS

CP/M 2.2 conventions only:
- `JMP 0005h` BDOS calls, `JMP 0000h` warm boot.
- Default FCB at `005Ch` (the song filename).
- Console I/O via BDOS functions 9 (print `$`-terminated string) and 10
  (read console buffer).
- Disk I/O via BDOS file open / read sequential.

### 1.3 Sound hardware

**Cromemco D+7A I/O card** (S-100 analog/digital interface), at its
factory-default base address (octal 030 = hex `18h`). The program writes
sample bytes to **two of the seven analog DACs** on the card:

| Port | Octal | Cromemco DAC label | Carries |
|------|-------|--------------------|---------|
| `19h` | 031 | Analog channel 1 | Software sum of Parts 1 + 2 |
| `1Bh` | 033 | Analog channel 3 | Software sum of Parts 3 + 4 |

D+7A analog output is 8-bit two's-complement, ~±2.56 V full-scale, with
sample-and-hold capacitors that retain the voltage between writes. The
program never touches `18h` (digital port) or analog channels 2/4/5/6/7.

> NOTE: a brute hex grep finds two more `D3 xx` byte pairs (`D3 2D`,
> `D3 F2`) in the binary, but those occur inside the `$`-terminated
> string region and are not actual `OUT` instructions.

---

## 2. User-visible behavior

The strings region (file offsets `0x1F0`–`0x457`) drives a simple text
UI. Prompts in order of likely first appearance:

```
Music Player, version 00.02

Welcome to the Wonderful World of COMPUTER MUSIC

Song file?
Do you want to change the starting parameters?
  How many repetitions ?
  Change Part 1?           Present voice of Part 1 is …  New voice for Part 1 ?
  Change Part 2?           Present voice of Part 2 is …  New voice for Part 2 ?
  Change Part 3?           Present voice of Part 3 is …  New voice for Part 3 ?
  Change Part 4?           Present voice of Part 4 is …  New voice for Part 4 ?
  Change tempo?            Present starting tempo is …    New starting tempo ?
Play it again, Sam?
New song?
'Bye for now
```

Error messages:

```
File not found
Song file is too long to play
Can't load voices
```

`Can't load voices` fires if `VOICES.MUS` is not on the current drive at
program start; the wavetable bank is loaded **once**, not per song.
(The error message itself is a literal string from the player; it
predates this document's terminology.)

---

## 3. Synthesis architecture

### 3.1 Polyphony and mixing

- **4 independent Parts** (Parts 1–4), each with its own:
  - 16-bit **phase accumulator**
  - per-note **phase increment** (= `step` = pitch)
  - **wavetable selection** — which of the 6 256-byte tables in
    `VOICES.MUS` this Part reads from
- Parts 1+2 are **summed in software** and written to DAC 1 (`OUT 19h`).
- Parts 3+4 are summed in software and written to DAC 2 (`OUT 1Bh`).
- The two DAC outputs are intended to be wired together externally into
  a single mono speaker feed. There is no stereo intent — the split
  exists because the inner loop cannot sum four 8-bit samples into one
  byte without overflow / loss of headroom; two pairs of two is the
  natural compromise.

### 3.2 Wavetable model

`VOICES.MUS` is six concatenated **256-byte single-cycle waveform
tables**, one per timbre, each on a 256-byte page boundary:

```
+0x000  wavetable 0  (sine, peak ±0x3C ≈ ±60)
+0x100  wavetable 1
+0x200  wavetable 2
+0x300  wavetable 3
+0x400  wavetable 4
+0x500  wavetable 5
```

1536 / 256 = 6 wavetables. All tables are 8-bit signed PCM. The first
table is unmistakably a sine: rises smoothly from `00` at offset 0 to
`+0x3C` at offset `0x40`, back to `00` at `0x80`, down to `0xC4` (-60)
at `0xC0`, back to `00`. Peak amplitude ~±60 leaves headroom so two
Parts can be summed without 8-bit overflow.

The program loads `VOICES.MUS` to a known page-aligned address at
startup, then references each wavetable by **page byte** (the high
byte of the wavetable's address). Each Part has its own page byte
in the inner loop.

### 3.3 Pitch generation — phase accumulator

Per Part, per sample tick:

```
phase16 := phase16 + step16        ; 16-bit add, wraps naturally
sample  := wavetable[ phase16 >> 8 ]   ; high byte indexes the 256-entry table
```

Pitch is set by `step16`. The full 16 bits give sub-sample phase
resolution; only the high 8 bits index the wave table. This is the
classic NCO / DDS (Numerically Controlled Oscillator / Direct Digital
Synthesis) technique — exactly the same scheme later used in chip music
engines on the C64, Amiga, etc.

**Frequency formula.** A full cycle through the wavetable happens when
`phase16` has advanced by exactly 65536 (one wrap). With sample rate `Fs`
and increment `step`:

```
freq_out  =  step × Fs / 65536
step_for  =  round(freq × 65536 / Fs)
```

PLAY.COM's inner loop runs at ~8 kHz on a 4 MHz Z80, so:

```
step  =  round(freq × 8.192)
```

**Pitch table at Fs = 8 kHz.** Every note maps to a single 16-bit `step`:

| Note | Hz | step (decimal) | step (hex) |
|------|---:|---------------:|:-----------|
| A2 | 110.0 | 901 | 0x0385 |
| A3 | 220.0 | 1802 | 0x070A |
| C4 (middle C) | 261.6 | 2143 | 0x085F |
| **A4** | **440.0** | **3604** | **0x0E14** |
| A5 | 880.0 | 7209 | 0x1C29 |
| A6 | 1760.0 | 14418 | 0x3852 |

**Three properties to notice:**

1. **Octave = 1-bit shift of step.** Going up an octave doubles the step
   (440 Hz → 880 Hz is 3604 → 7209, modulo rounding). That's also why
   wavetables 3 and 5 (whose fundamentals are missing) act as free
   octave-shifters — they read the same step as wavetable 0 (sine) but
   the dominant harmonic is 2× or 3× the input frequency, sounding an
   octave or octave-fifth above without changing `step`.

2. **Sub-sample phase precision.** Pitch resolution is
   `Fs / 65536 ≈ 0.122 Hz` — about one semitone divided by 200 at A4.
   Way finer than the ear's threshold of pitch discrimination (~3 Hz at
   A4). The low 8 bits of `phase16` never index anything, but they
   accumulate, so the timing of when the high byte ticks over is
   sub-sample accurate.

3. **No anti-aliasing at high pitches.** A4 (step=3604) advances ~14
   wavetable entries per sample. At C7 you skip ~50. Sharp-edged
   wavetables (wavetable 4 = square) alias audibly above the upper
   register; smooth wavetables (wavetable 0 = sine) stay clean. The
   composer's job is to choose a wavetable per Part to keep the mix
   from getting hashy at high pitches.

**Useful pitch range:**

```
step = 1       →    0.122 Hz   (effectively DC; Part barely advances)
step = 256     →    31.25 Hz   (lowest 'clean' pitch, 1 entry per sample)
step = 3604    →    440 Hz     (A4, comfortable musical range)
step = 16384   →    2000 Hz    (high but useful)
step = 32768   →    4000 Hz    (Nyquist limit at 8 kHz Fs — alias city)
```

In practice the BACH `.MUS` files stay between roughly step 200 (low
bass) and step 12000 (high treble).

**Computing step from a note name.** The standard equal-temperament
formula plus the step conversion gives:

```python
def step_for_note(name: str, octave: int, Fs: int = 8000) -> int:
    """E.g. step_for_note('A', 4) → 3604."""
    semitone_index = {'C':0,'C#':1,'D':2,'D#':3,'E':4,'F':5,'F#':6,
                      'G':7,'G#':8,'A':9,'A#':10,'B':11}[name]
    midi = 12 * (octave + 1) + semitone_index    # A4 = MIDI 69
    freq = 440.0 * 2 ** ((midi - 69) / 12)
    return round(freq * 65536 / Fs)
```

`compose.py` in this directory uses exactly this formula. The simulator
(`simulate.py`) has been validated bit-exact against captured hardware
output on `BACH8.MUS`, so the math is correct.

### 3.4 The inner sample loop (memory ≈ `05DCh`)

The loop is **unrolled and self-modifying**: the per-Part state lives
*inside* the immediate operands of `LD HL,nn` / `LD DE,nn` /
`LD H,n` instructions. There is no per-Part state lookup at sample
rate — the values *are* the code.

Annotated byte sequence for DAC 1's two Parts (file offset
`0x4DD` ≈ memory `05DDh`):

```
; ── Part 1 ────────────────────────────────────────────────────────────
21 00 00      LD HL, phase1          ; placeholder; runtime patches with
                                     ;   current 16-bit phase accumulator
11 00 00      LD DE, step1           ; placeholder; pitch increment
19            ADD HL,DE              ; phase1 += step1
22 dd 05      LD (05DDh+...),HL      ; write phase1 back (next iteration)
6c            LD L,H                 ; L = high byte of phase
26 00         LD H, part1_wt_page    ; placeholder; runtime patches with
                                     ;   the wavetable page Part 1 uses
7e            LD A,(HL)              ; A  = wavetable[phase1>>8]
; ── Part 2 ────────────────────────────────────────────────────────────
21 00 00      LD HL, phase2
11 00 00      LD DE, step2
19            ADD HL,DE
22 eb 05      LD (...),HL
6c            LD L,H
26 00         LD H, part2_wt_page
86            ADD A,(HL)             ; A += wavetable[phase2>>8]
; ── emit ─────────────────────────────────────────────────────────────
d3 19         OUT (19h),A            ; -> DAC 1
```

Parts 3+4 immediately follow, identically structured, ending with
`D3 1B` (`OUT (1Bh),A` -> DAC 2). Then a small countdown:

```
05            DEC B
c2 d4 05      JP NZ, inner_loop      ; inner = sample-rate timing
0d            DEC C
c2 da 05      JP NZ, inner_loop      ; outer = note-duration counter
```

`B` controls the per-note inner-loop count (drives the sample rate /
note duration), `C` is the outer counter. When both expire, control
returns to the dispatcher, which patches in the *next* note's `step`
values for whichever Parts changed and re-enters the loop.

### 3.5 Why this is so fast

- Sample rate cost per tick = ~16 instructions × 4 Parts ≈ a few dozen
  T-states. On a 4 MHz Z80 this comfortably exceeds the rate at which
  the D+7A's S/H caps need refreshing.
- Wavetable change for a Part = one byte poked into the immediate field
  of its `LD H,n`. Pitch change = two bytes into the immediate of its
  `LD DE,nn`. No table indirection, no register shuffling.
- No volume envelope. Amplitude is fixed at the peak of the chosen
  wavetable (~±60). Headroom is by design: max possible sum of two
  Parts is ±120, well inside the ±127 DAC range.

### 3.6 What it does *not* do

- No noise channel, no PCM playback, no envelope generator, no
  vibrato/portamento, no stereo panning controls.
- No real-time tempo modulation while a song plays — tempo is set once
  at the start. (`Change tempo?` is asked before playback begins.)
- No DMA. Every sample is hand-written by the CPU.

---

## 4. File formats

### 4.1 `VOICES.MUS` — wavetable bank

Fixed layout: six contiguous 256-byte signed PCM single-cycle waveforms
(see §3.2). No header. Total size 1536 bytes. Loaded to a page-aligned
address at startup; the high byte of that base address + the wavetable
index gives the page that gets patched into the synthesis loop for the
Part using that wavetable.

### 4.2 `*.MUS` — song files

Sizes vary widely (128 B `TEST.MUS` … 9344 B `ML.MUS`). The first bytes
of `TEST.MUS` look like Z80 code (`31 00 10` = `LD SP,1000h`,
`0E 09` = `LD C,9`, `11 02 02` = `LD DE,0202h`, `CD 05 00` = `CALL
BDOS`), suggesting one of two layouts I have **not fully verified**:

  **Hypothesis A** — song files are *self-running* Z80 programs that
  PLAY.COM loads to a fixed address and `JP`s into. The program would
  embed the per-tick patch sequence and the note schedule.

  **Hypothesis B** — song files start with a small header (possibly
  including bytes that look like code but are interpreted as
  parameters) followed by note data. PLAY.COM contains the play
  engine; the song file just supplies note streams + per-Part
  wavetable defaults.

Hypothesis B fits better with the prompts ("Change Part 1?", etc. —
the player clearly knows the concept of Parts independently of any one
song), but the leading bytes need a proper disassembly pass to
distinguish. Either way, the salient externally-visible properties are:

- Songs reference **4 Parts** and **6 wavetables** (= the `VOICES.MUS`
  index range 0..5).
- "Song file is too long to play" implies a fixed maximum buffer; songs
  are loaded entirely into RAM, not streamed off disk during playback.

Worth a follow-up disassembly if anyone wants to write a `.MUS`
converter.

---

## 5. Implications for CPMEMU

### 5.1 Emulating the existing program

To make `PLAY.COM` produce sound under cpmemu, the emulator needs:

1. **Z80 CPU emulation.** Already true on cpmemu's Z80 builds; will
   silently no-op on a pure 8080 build (the first `DD`/`ED`/`CB` byte
   the program executes will mis-decode).
2. **Cromemco D+7A I/O emulation** at base port `18h`, specifically:
   - `OUT (19h),A` and `OUT (1Bh),A` need to be captured and rendered
     as audio samples.
   - The D+7A's other 5 DACs (ports `1Ah`, `1Ch`, `1Dh`, `1Eh`, `1Fh`)
     can be silently latched (not wired to audio) without breaking
     this program.
   - `OUT (18h)` — the digital port — is unused by `PLAY.COM`; emulate
     as a write-through latch.
3. **Sample-rate inference.** The program does not declare a sample
   rate — it just runs `OUT` as fast as the CPU can. Either:
   - measure cycles-per-`OUT` at runtime and feed the host audio device
     at the implied rate, or
   - clock the D+7A model to a fixed rate (8 kHz is a sensible
     default for this style of code) and re-sample.

### 5.2 Relationship to `SOUND_CARD.md` (Phase 3 plan)

The Phase 3 sound card in `CPMEMU/SOUND_CARD.md` is a different beast:
slave 65C02 + SID + ROM cartridge, "play song N" by index, no per-sample
CPU work. `PLAY.COM` is **prior art for the *opposite* design** — every
sample driven by the host CPU through a generic DAC. If a cpmemu D+7A
emulation lands first, `PLAY.COM` makes a great smoke test for it
(small binary, distinctive output, real period-correct music).

---

## 6. Full disassembly

A complete annotated Z80 disassembly is in [`PLAY.lst`](PLAY.lst), produced
by [`disasm.py`](disasm.py) (uses the `z80dis` PyPI package; data ranges
and labels hand-curated). Key things the disassembly nailed down that
were guessed in §3–§4:

### 6.1 Wavetable page encoding (resolves the "where do wavetables live" question)

VOICES.MUS is loaded to address `0x0700` (computed as `(0x0623 + 0x100) & 0xFF00`,
i.e. round up the assembled "end of essential code" pointer to the next
page boundary). At program start:

```
0114: LD HL, (0x055E)       ; HL = 0x0623 (literal stored in binary)
0117: INC H                 ; HL = 0x0723
0118: LD L, 0               ; HL = 0x0700  ← wavetable bank load address
011A: LD A, 0x81
011C: SUB H                 ; A = 0x81 - 0x07 = 0x7A
011D: LD (0x055B), A        ; save the runtime "wavetable offset"
```

That `0x7A` is then poked into **four `SUB n` immediates** in the
dispatcher (at `0x05B0`, `0x05B6`, `0x05BD`, `0x05C3`) — one per Part.
When a song sends a wavetable byte `V` for a Part, the dispatcher
computes `V - 0x7A` to get the actual table page. So **wavetable
indexes in `.MUS` files are encoded as `0x81..0x86`** (6 wavetables),
and the runtime adjusts for wherever VOICES.MUS happened to land.
Songs are position-independent by construction.

### 6.2 Song-stream command format (confirmed by disassembly of 0x0579-0x05D1)

Songs are pushed/popped on the stack — the player redirects `SP` to the
loaded song buffer:

```
0562: play_song:
      LD (saved_sp), SP            ; remember caller's stack
      LD A, (wavetable_offset)
      LD (...), A x 4              ; patch the 4 per-Part wavetable-page
                                   ;   SUB immediates
      LD SP, (song_addr)           ; SP = song buffer (0x0D00 typically)
0579: next_command:
      POP BC                       ; BC = next command word
      OR C                         ; C = 0 means end of song
      JP NZ, dispatch_command
      LD SP, (saved_sp)
      RET
0584: dispatch_command:            ; six RR B's, one per command bit
      RR B / JP NC / POP HL / LD (p1_step_imm), HL    ; bit 0 -> Part 1 step
      RR B / JP NC / POP HL / LD (p2_step_imm), HL    ; bit 1 -> Part 2 step
      RR B / JP NC / POP HL / LD (p3_step_imm), HL    ; bit 2 -> Part 3 step
      RR B / JP NC / POP HL / LD (p4_step_imm), HL    ; bit 3 -> Part 4 step
      RR B / JP NC / POP HL / SUB ; SUB ; POP HL ; SUB ; SUB    ; bit 4
                                                       ;   -> 4 wavetable pages
      RR B / JP NC / POP HL / LD A,L / LD (tempo_imm), A         ; bit 5
      JP outer_iter
```

Concretely, each note in a `.MUS` file is encoded as a stream of
little-endian 16-bit words pushed onto the stack:

```
   word 0:  command           lo = duration (samples / 256) ; 0 = end-of-song
                              hi = bitmap of which params follow
   word 1:  if bit 0 set      Part 1 phase increment (step / pitch)
   word 2:  if bit 1 set      Part 2 phase increment
   word 3:  if bit 2 set      Part 3 phase increment
   word 4:  if bit 3 set      Part 4 phase increment
   word 5:  if bit 4 set      Part 1 wavetable-byte (lo) |
                              Part 2 wavetable-byte (hi)
   word 6:  if bit 4 set      Part 3 wavetable-byte (lo) |
                              Part 4 wavetable-byte (hi)
   word 7:  if bit 5 set      new tempo (only low byte used; gets stored as
                              the immediate of "LD B, n" inside the inner loop)
```

Bits 6 and 7 of the command byte are unused. Per-Part pitch is a full
16-bit step value; only the high 8 bits index the wavetable, the low
8 give sub-sample phase precision.

### 6.3 The "param change" routine (0x0198) writes into the song stream

When the user answers "Y" to "Do you want to change the starting
parameters?", the routine indexes the loaded song with `IX` (`IX =
song_addr`) and reads/writes specific offsets:

```
IX+10 = Part 1 default wavetable     (stored as 0x80 | wavetable_idx)
IX+11 = Part 2 default wavetable
IX+12 = Part 3 default wavetable
IX+13 = Part 4 default wavetable
IX+14 = tempo default
```

This means **bytes 10..14 of every `.MUS` file are the operands of the
song's first `bit 4 + bit 5` command** — the param-change UI doesn't
alter the player; it edits the song's first command in place.
Specifically: bytes 0-9 of the song are command + 4× pitch (bits 0..3
of the command byte set), and bytes 10-14 are the wavetable/tempo word
operands of the next command (bits 4 and 5 set).

That implies the canonical first two commands in any `.MUS` file are:

```
   bytes 0-9:    command word (bits 0-3 set), then 4 × initial pitch words
   bytes 10-15:  command word (bits 4-5 set), then 2 × wavetable words,
                 then tempo word
```

This is consistent with the param-change UI's offsets and gives a clean
"set everything up for note 1" prologue. Editable bytes are exactly the
non-pitch ones (per-Part wavetable selections + tempo), which is what
the UI exposes.

### 6.4 BDOS function 0x86 — non-standard

At `0x0281` the program calls BDOS with `C = 0x86` after reading a
filename from the console. Standard CP/M 2.2 BDOS only goes to function
0x28; **0x86 is a host-specific extension** — almost certainly a
"parse filename → FCB" call (the equivalent of CP/M 3's function 152).
The most likely host is **Cromemco CDOS**, which both ships with the
D+7A target hardware *and* extends CP/M 2.2 with similar utility
functions. Pure CP/M 2.2 hosts will return an error here and the
program will fail to accept typed filenames — though a filename passed
on the CCP command line would still work (BDOS already populates the
FCB at `0x005C` for that case before transferring control).

### 6.5 The duplicated block at 0x0623-0x067F

The bytes at `0x0623..0x067F` are nearly identical to a slice of
`0x05A1..0x05FF`. Static analysis shows no reachable code path that
jumps into this region — entry from `dispatch_command` and from the
inner loop both go to addresses below `0x0623`. The block looks like
either:
- assembler/source artifact from a partial unroll that was abandoned, or
- intentional padding to round the binary to a particular sector
  boundary (`0x580` bytes = 11 × 128-byte CP/M records exactly).

The latter is plausible: `1408 / 128 = 11.0`, so the binary occupies
exactly 11 records on disk.

### 6.6 Were `.MUS` files hand-encoded or tool-generated?

The internal evidence overwhelmingly points to **tool-generated**, with
the songs likely produced from a higher-level note description run
through a compiler/translator program. Three findings from decoding the
existing songs:

**1. Same note → same step value, exactly, every time.** Decoding
`BACH8.MUS` shows that every G3 in the song is encoded as step `0x0642`
(1602), every D4 is `0x0960` (2400), every B3 is `0x07E2` (2018), and
so on. A human computing pitch values by hand would inevitably produce
small variations or transcription errors over thousands of notes — but
the actual files have *bitwise-identical* step values for every
occurrence of the same pitch. That's the fingerprint of a precomputed
semitone lookup table being indexed by the tool.

**2. The reference frequency is uniformly slightly flat.** Every step
value in `BACH8.MUS` lands exactly **4 cents below** the modern A=440 Hz
equal-temperament reference. The offset is uniform across all pitches
and all songs. That can only happen if a tool computed every step from
a single reference frequency (e.g. A=438.99 Hz, or equivalently assumed
Fs slightly higher than 8 kHz when generating the table). Hand-encoded
values would scatter, not cluster precisely on a uniformly-shifted
grid.

**3. Volume of data.** ML.MUS is 9 KB ≈ 4500 16-bit words. Even at one
note per second of composition time, that's well over an hour of
typing 16-bit hex values for a single song — and the disk has 23 such
files. Realistically nobody hand-typed Bach inventions as packed
little-endian step values.

**Likely toolchain shape** (speculative but consistent with the
evidence):

- A textual song description (probably staff-like: note names +
  durations + per-Part wavetable assignments) authored by the composer.
- A compiler (likely written in BASIC or assembly) that:
  - Indexed each note name into a precomputed semitone table tuned to
    A ≈ 439 Hz at Fs = 8 kHz.
  - Coalesced unchanged Parts between successive beats to produce the
    minimum dispatcher-bit pattern.
  - Emitted the stack-pushed 16-bit word stream + the trailing
    `0x0000` end-of-song marker.

This is essentially what `compose.py` in this directory does today —
it likely re-derives whatever the original tool did, just in Python
and tuned to A=440. The 4-cent offset between modern compositions
authored with `compose.py` and the original BACH files is below the
musical perception threshold (~5 cents) and is irrelevant in practice.

The original tool itself does not appear to ship with the disk — only
the player and the compiled songs. It may have been an in-house
authoring program, possibly running on a different system entirely
(generating .MUS files for the Cromemco target).

---

## 7. Quick reference

| Question | Answer |
|----------|--------|
| Target CPU | Z80 |
| Target OS | CP/M 2.2 (probably Cromemco CDOS — see §6.4) |
| Target sound device | Cromemco D+7A I/O, ports `19h` and `1Bh` |
| Polyphony | 4 Parts |
| Wavetables in `VOICES.MUS` | 6 (256 B each, signed PCM, indexed 0..5) |
| Mixing | Software 8-bit add; Parts 1+2 → DAC 1, Parts 3+4 → DAC 2 |
| Pitch generation | 16-bit phase accumulator, high byte indexes wavetable |
| Volume envelopes | None |
| Wavetable change cost (per Part) | One byte (poke `LD H,n` immediate) |
| Pitch change cost (per Part) | Two bytes (poke `LD DE,nn` immediate) |
| Sample rate | ~8 kHz, implicit (inner-loop cost on a 4 MHz Z80) |
| Companion files needed | `VOICES.MUS` on the current drive |
| Banner | "Welcome to the Wonderful World of COMPUTER MUSIC" |
| Self-id | "Music Player, version 00.02" |
| Wavetable byte encoding in songs | `0x81 + index` (auto-relocated at runtime) |
| Song command structure | Stack-based: `POP BC` for cmd word; bits 0-5 of `B` select what to pop next |
| Disassembly file | [`PLAY.lst`](PLAY.lst) (annotated, 465 lines) |
| Disassembler script | [`disasm.py`](disasm.py) (uses `pip install z80dis`) |
| Probable host OS | Cromemco **CDOS** (uses BDOS fn 0x86, beyond CP/M 2.2's range) |
| Disk record count | 11 records exactly (1408 / 128) — likely intentionally padded |
