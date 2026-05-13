# Cello Suite No. 1 in G major (BWV 1007)

J.S. Bach's first cello suite, transcribed for the 4-voice CP/M
wavetable player.  Each of the seven movements is one `.MUS` file;
`CELLO.SUB` plays them back-to-back via PLAYZ80's `/Q` (quiet) switch.

## Files on this disk

| File | Source | Notes |
|---|---|---|
| `01Prelude.mid` .. `07Gigue.mid` | original MIDI sources (kept for re-conversion) | not used on the CP/M side |
| `PRELUDE.MUS` .. `GIGUE.MUS` | converted via `midi2mus.py --voices 1` | seven movements; see filename map below |
| `CELLO.SUB` | hand-written | SUBMIT batch: plays all seven in order with `/Q` |
| **`VOICES.MUS`** | **custom (NOT the original CDOS bank)** | see below |
| `*_sim.wav` | rendered by `Scripts/simulate.py --voices VOICES.MUS` | preview files; do not need to be uploaded to CP/M |
| `cello1_A4.wav` / `cello2_A4.wav` / `cello3_A4.wav` | rendered by `build_voices.py --audition` | 3-second A4 reference tones for the three synthetic cello variants in the library (kept for A/B'ing future tweaks) |

Filename map (8.3-compliant for CP/M):

| MIDI source | CP/M file |
|---|---|
| `01Prelude.mid` | `PRELUDE.MUS` |
| `02Allemande.mid` | `ALLEMAND.MUS` |
| `03Courante.mid` | `COURANTE.MUS` |
| `04Sarabande.mid` | `SARABAND.MUS` |
| `05Minuetto1.mid` | `MINUET1.MUS` |
| `06Minuetto2.mid` | `MINUET2.MUS` |
| `07Gigue.mid` | `GIGUE.MUS` |

## Custom `VOICES.MUS`

The `VOICES.MUS` in this folder is **not** the original CDOS bank.
Slot 2 (the skewed-saw position that `midi2mus.py`'s mode `1` routes
the V3 doubling voice to) has been replaced with `cello2`, a
synthetic cello-flavored wavetable built additively from a sawtooth
harmonic series with a Gaussian formant emphasis at H3 and a 4th-order
low-pass at H7.  Slots 0 / 1 / 3 / 4 / 5 are byte-identical to the
original.

The file is still exactly 1536 bytes (6 x 256) so PLAY.COM /
PLAYCDOS / PLAYZ80 load it without any changes.  The intent is that
this disk is self-contained: upload everything in this folder to a
CP/M disk image, mount it, and the cello suite plays through with
the cello timbre.  The Bach / sinfonia disks keep using their own
(original) `VOICES.MUS` and are unaffected.

### Regenerating

```
# rebuild the cello-suite bank
python Scripts/build_voices.py --replace 2=cello2 \
       -o MIDI/CelloSuiteNumberOneinG/VOICES.MUS

# re-convert any movement (rubato + polyphony aware; mode '1' for solo)
python Scripts/midi2mus.py MIDI/CelloSuiteNumberOneinG/01Prelude.mid \
       MIDI/CelloSuiteNumberOneinG/PRELUDE.MUS --voices 1

# preview against the custom bank
python Scripts/simulate.py MIDI/CelloSuiteNumberOneinG/PRELUDE.MUS \
       --voices MIDI/CelloSuiteNumberOneinG/VOICES.MUS \
       -o MIDI/CelloSuiteNumberOneinG/PRELUDE_sim.wav
```

See the project root [`README.md`](../../README.md) section 5.1 for
more background on the custom-`VOICES.MUS`-per-disk pattern, and
[`Scripts/README.md`](../../Scripts/README.md) for the per-script
reference.
