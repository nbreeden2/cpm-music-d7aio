# Cello Suite No. 4 in E-flat major (BWV 1010)

J.S. Bach's fourth cello suite, transcribed for the 4-voice CP/M
wavetable player.  Six movements; `CELLO.SUB` plays them back-to-back
via PLAYZ80's `/Q` (quiet) switch.

## Files on this disk

| File | Source | Notes |
|---|---|---|
| `01Prelude.mid` .. `06Gigue.mid` | original MIDI sources (kept for re-conversion) | not used on the CP/M side |
| `PRELUDE.MUS` .. `GIGUE.MUS` | converted via `midi2mus.py --voices 1` | six movements; see filename map below |
| `CELLO.SUB` | hand-written | SUBMIT batch: plays all six in order with `/Q` |
| **`VOICES.MUS`** | **custom (NOT the original CDOS bank)** | see below |
| `*_sim.wav` | rendered by `Scripts/simulate.py --voices VOICES.MUS` | preview files; do not need to be uploaded to CP/M |

Filename map (8.3-compliant for CP/M):

| MIDI source | CP/M file |
|---|---|
| `01Prelude.mid` | `PRELUDE.MUS` |
| `02Allemande.mid` | `ALLEMAND.MUS` |
| `03Courante.mid` | `COURANTE.MUS` |
| `04Sarabande.mid` | `SARABAND.MUS` |
| `05Bourree.mid` | `BOURREE.MUS` |
| `06Gigue.mid` | `GIGUE.MUS` |

Note that the suite ordering is different from Suite No. 1: the
Sarabande sits in slot 4 (between Courante and the dance pair) and
the dance pair is a single Bourree rather than two Minuetts.

## Custom `VOICES.MUS`

Same recipe as Suite No. 1: slot 2 is replaced with the synthetic
`cello2` wavetable (additive sawtooth + Gaussian formant emphasis at
H3 + 4th-order low-pass at H7).  Slots 0 / 1 / 3 / 4 / 5 are
byte-identical to the original CDOS bank.  The file is still exactly
1536 bytes so PLAY.COM / PLAYCDOS / PLAYZ80 load it unchanged.

This disk may benefit from a *different* cello variant down the
road (Suite 4 has different range and texture than Suite 1, and a
darker / brighter timbre might fit it better).  For now both cello
disks share the same `cello2` setup.

### Regenerating

```
# rebuild the cello-suite bank
python Scripts/build_voices.py --replace 2=cello2 \
       -o MIDI/CelloSuiteNumberFourinEb/VOICES.MUS

# re-convert any movement
python Scripts/midi2mus.py MIDI/CelloSuiteNumberFourinEb/01Prelude.mid \
       MIDI/CelloSuiteNumberFourinEb/PRELUDE.MUS --voices 1

# preview against the custom bank
python Scripts/simulate.py MIDI/CelloSuiteNumberFourinEb/PRELUDE.MUS \
       --voices MIDI/CelloSuiteNumberFourinEb/VOICES.MUS \
       -o MIDI/CelloSuiteNumberFourinEb/PRELUDE_sim.wav
```

See the project root [`README.md`](../../README.md) section 5.1 for
more background on the custom-`VOICES.MUS`-per-disk pattern, and
[`Scripts/README.md`](../../Scripts/README.md) for the per-script
reference.
