# Scripts/

Python tooling for the MUSIC project: build `.MUS` songs, convert MIDI to
`.MUS`, simulate playback, analyze the `VOICES.MUS` wavetable bank, and
disassemble `PLAY.COM`.

All scripts target Python 3 and run from any directory; paths are resolved
relative to the project root via `_paths.py`. Three third-party packages are
needed -- each by exactly one script family, so you only need the ones whose
scripts you intend to run:

| Package | Used by | Why |
|---|---|---|
| `mido` | [`midi2mus.py`](midi2mus.py) | Parses standard MIDI files: enumerates tracks, decodes `note_on` / `note_off` / `set_tempo` meta-events, and exposes per-event delta-times in PPQN ticks. Writing this from scratch (variable-length-quantity decoding, running-status handling, meta-event framing) would dwarf the rest of the converter. |
| `z80dis` | [`disasm.py`](disasm.py), [`disasm_m80.py`](disasm_m80.py) | Decodes raw Z80 opcodes (including the `CB`/`DD`/`ED`/`FD` prefix tables and the undocumented variants) into mnemonics + operand widths. The Microsoft Z80 instruction set has ~700 encodings; an in-repo opcode table would be a 1000-line maintenance burden. |
| `matplotlib` | [`plot_voices.py`](plot_voices.py) | Renders the stacked PNG of all six `VOICES.MUS` wavetables. Only this one script needs a real plotting library; the ASCII renderer ([`sparkline_voices.py`](sparkline_voices.py)) covers the terminal-friendly case with no dependency. |

```
pip install mido z80dis matplotlib
```

Everything else (struct packing, WAV writing, math, argparse) is in the
Python standard library.

## Shared helper

| Script | Purpose |
|---|---|
| [`_paths.py`](_paths.py) | Centralized path constants (`ORIGINAL_DISK`, `NEW_DISK`, `VOICE_TESTS`, `VOICES_ANALYSIS`, `VOICES_MUS`, `PLAY_COM`). Imported by every script that touches the filesystem so a reorg only edits one file. |

## Song generators (`.MUS` output)

Each script emits a `.MUS` byte stream (16-bit little-endian command words;
see `README.md` in the project root for the format) into `New_CPM_Files/`
or `Voice_Tests/`.

| Script | Output | Purpose |
|---|---|---|
| [`compose.py`](compose.py) | `CLAUDE.MUS` | An original 4-voice baroque-style minuet in G major, demonstrating chord-driven coalescing into per-eighth commands. |
| [`compose_song.py`](compose_song.py) | `BIGGER.MUS` (or similar) | Single-voice melody transcribed from a hand-written score (`bigger1.png` / `bigger2.png`), 4/4 in G major, 54 measures. |
| [`compose_calibration.py`](compose_calibration.py) | `CALIB.MUS` | Steady A4 (440 Hz) on voice 1 with the sine timbre, ~30 s. Used to calibrate the player's actual sample rate against measured hardware pitch. |
| [`compose_doremi.py`](compose_doremi.py) | `DOREMI.MUS` | Diatonic ascent C1 -> C7 (43 notes, 1 s each) on voice 1. Sweeps the player's full practical range for scope verification. |
| [`compose_octave_steps.py`](compose_octave_steps.py) | `OCTAVES.MUS` | Power-of-two phase increment sweep (`0x0100` through `0x4000`); each note is exactly one octave above the previous. |
| [`compose_octave_trick.py`](compose_octave_trick.py) | `OCTAVE.MUS` | Demonstrates the V3/V5 weak-fundamental trick: duplicating a voice's step values into a slot that uses timbre 3 (octave-shift) or 5 (octave+fifth) gets free harmonic doubling out of the 4-voice engine. |
| [`compose_voice_tests.py`](compose_voice_tests.py) | `VOICE1.MUS` .. `VOICE6.MUS` | Six 30-second A4 tones, one per timbre, voice 1 only. Each file isolates one wavetable for scope identification. |

## MIDI -> `.MUS` conversion

| Script | Purpose |
|---|---|
| [`midi2mus.py`](midi2mus.py) | Convert a 2- or 3-track MIDI file into a `.MUS` file using the same encoding style as the original CDOS-era Bach inventions on the music disk. Three modes: `--voices 2` (inventions: V1+V3 doubled, V2+V4 doubled), `--voices 3` (sinfonias, three independent voices), `--voices 2of3` (sinfonia with BACH-style soprano octave doubling). Tunes 26 cents flat from A=440 to match the originals. |

```
python Scripts/midi2mus.py SRC.MID OUT.MUS --voices 2
```

## Playback simulation / inspection

| Script | Purpose |
|---|---|
| [`simulate.py`](simulate.py) | Sample-accurate software model of the PLAYZ80 / PLAY.COM mix loop. Reads a `.MUS` plus `VOICES.MUS`, runs the same `phase += step` / wavetable-lookup / signed-add the player does, and writes a 16-bit mono WAV at the calibrated 11,169 Hz rate. Useful for previewing a `.MUS` without uploading to the IMSAI. |
| [`decode_mus.py`](decode_mus.py) | Pretty-print a `.MUS` file as the sequence of commands the player would see (`cmd`, bitmap, duration, per-voice pitches with note names + cents error, timbre indices, tempo, ms per command). Optional `--limit N` to truncate. |

```
python Scripts/simulate.py New_CPM_Files/CLAUDE.MUS -o CLAUDE.wav
python Scripts/decode_mus.py New_CPM_Files/CLAUDE.MUS --limit 40
```

## `VOICES.MUS` analysis

`VOICES.MUS` is six concatenated 256-byte single-cycle wavetables (signed
8-bit PCM). These scripts dissect them.

| Script | Purpose |
|---|---|
| [`analyze_voices.py`](analyze_voices.py) | Per-table statistics (amplitude, DC offset, RMS, harmonic content, headroom) plus per-table WAV renders into `voices_analysis/`. |
| [`plot_voices.py`](plot_voices.py) | Stacked matplotlib plot of all six wavetables sharing the phase axis; writes a PNG into `voices_analysis/`. |
| [`sparkline_voices.py`](sparkline_voices.py) | ASCII waveform renderer for terminals / markdown -- one boxed sparkline per voice. |
| [`check_wrap.py`](check_wrap.py) | Reports the discontinuity at each table's wrap point (`s[0] - s[255]`) plus the maximum adjacent-sample delta. Catches voices that would pop when the phase accumulator wraps. |
| [`check_symmetry.py`](check_symmetry.py) | Tests each table for even / odd / half-period symmetries to explain perceived shape (e.g., why voice 3 "looks backwards"). |
| [`inspect_voice3.py`](inspect_voice3.py) | Byte-by-byte print of voice 3, listing monotonicity breaks. Used to characterize the skewed-saw shape. |
| [`verify_octave_trick.py`](verify_octave_trick.py) | Spectral check (Goertzel) of `OCTAVE_sim.wav` to confirm that timbres 3 and 5 do in fact produce octave and octave-plus-fifth content from their drive frequencies. |

## `PLAY.COM` disassembly

| Script | Purpose |
|---|---|
| [`disasm.py`](disasm.py) | Annotated Z80 disassembly of `PLAY.COM` using `z80dis`. Hand-curated data ranges (FCB, message strings, variable area), labels at known entry points and BDOS calls, inline comments for self-modifying-code targets. Read-only analysis output. |
| [`disasm_m80.py`](disasm_m80.py) | Generates M80-assemblable source (`PLAY.MAC`) that reassembles byte-identical with `M80 =PLAY.MAC` / `L80 PLAY,PLAY/N/E`. Works around M80 quirks (6-character significant symbols, JR/DJNZ requires symbolic operands, zero-page externals declared via EQU). Source of truth for `PLAYCDOS.MAC`. |
