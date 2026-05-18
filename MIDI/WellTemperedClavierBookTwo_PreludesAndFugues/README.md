# The Well-Tempered Clavier, Book II — preludes & fugues

J.S. Bach, BWV 870–893 (Book II = BWV 870–893, completed 1742).
This disk holds 21 of the 48 movements from Book II — every prelude
and fugue whose MIDI source in this corpus parses cleanly.  Each
piece is one `.MUS` file; [`WTCBKII.SUB`](WTCBKII.SUB) plays them
back-to-back in prelude/fugue pair order via PLAYZ80's `/Q` (quiet)
switch.

## Pieces on this disk

| File | BWV | Key |
|---|---|---|
| `PRELUDE1.MUS`  | 870 | C major |
| `FUGUE1.MUS`    | 870 | C major |
| `PRELUDE2.MUS`  | 871 | C minor |
| `FUGUE2.MUS`    | 871 | C minor |
| `PRELUDE3.MUS`  | 872 | C♯ major |
| `FUGUE3.MUS`    | 872 | C♯ major |
| `PRELUDE4.MUS`  | 873 | C♯ minor |
| `FUGUE4.MUS`    | 873 | C♯ minor |
| `PRELUDE5.MUS`  | 874 | D major |
| `FUGUE5.MUS`    | 874 | D major |
| `PRELUDE6.MUS`  | 875 | D minor |
| `FUGUE6.MUS`    | 875 | D minor |
| `PRELUDE7.MUS`  | 876 | E♭ major |
| `FUGUE7.MUS`    | 876 | E♭ major |
| `PRELUDE8.MUS`  | 877 | D♯ minor |
| `FUGUE8.MUS`    | 877 | D♯ minor |
| `PRELUDE9.MUS`  | 878 | E major |
| `FUGUE9.MUS`    | 878 | E major |
| `FUGUE10.MUS`   | 879 | E minor |
| `FUGUE11.MUS`   | 880 | F major |
| `FUGUE12.MUS`   | 881 | F minor |

The fugues for BWV 879–881 are present without their companion
preludes because those preludes are corrupt in the source MIDI
corpus (and also on the Bach Central upstream).  The other twelve
pairs of Book II (BWV 882–893) are likewise corrupt in this corpus
and could not be converted.

## Why mode `1 --merge` instead of mode `4`

The Book II MIDIs in this corpus are **single-track polyphonic
exports** — every voice's notes share one MIDI track rather than
sitting on a separate track per voice.  That means `midi2mus.py`
cannot use mode `4` (which expects one monophonic track per voice).
Instead `--voices 1 --merge` is used: the converter folds every
non-drum track into one polyphonic source and runs the
polyphony reducer, allocating up to three simultaneous notes per
cell across V1 (low / sine), V2 (mid / sine — only used when three
notes sound), and V3 (high / skewed saw).  V4 is silent.

When more than three voices sound at once (the dense moments in a
4-voice fugue), one of the four lines is dropped per cell.  The
reducer scores each candidate by `cell-coverage * total-note-
duration` and keeps the highest-scoring three, which biases survival
toward sustained structural lines and drops short ornaments.  Net
effect: subjects and counter-subjects survive intact; harmonic
filler and brief trill notes lose out.

## Files on this disk

| File | Source | Notes |
|---|---|---|
| `*.mid` | original MIDI sources (kept for re-conversion) | not used on the CP/M side |
| `*.MUS` | converted via `midi2mus.py --voices 1 --merge` | 21 pieces |
| `WTCBKII.SUB` | hand-written | SUBMIT batch: prelude/fugue pair order with `/Q` |
| `WTCBKII.QSB` | byte-identical to `WTCBKII.SUB` | QPM convention copy |
| `VOICES.MUS` | byte-identical copy of `Original_CPM_Files/VOICES.MUS` | original CDOS 6-slot bank; no custom voices |
| `*_sim.wav` | rendered by `Scripts/simulate.py` against the bundled `VOICES.MUS` | preview files; do not need to be uploaded to CP/M |

## VOICES.MUS

This disk uses the **original CDOS `VOICES.MUS` bank verbatim**.
Mode `1`'s default timbres `(0, 0, 2, 0)` use slots 0 (sine) and 2
(skewed saw) of the standard bank, both playing at written pitch
— no custom bank required.

## Regenerating

```
# re-convert one piece
python Scripts/midi2mus.py \
    MIDI/WellTemperedClavierBookTwo_PreludesAndFugues/prelude1.mid \
    MIDI/WellTemperedClavierBookTwo_PreludesAndFugues/PRELUDE1.MUS \
    --voices 1 --merge

# preview against the bundled VOICES.MUS
python Scripts/simulate.py \
    MIDI/WellTemperedClavierBookTwo_PreludesAndFugues/PRELUDE1.MUS \
    --voices MIDI/WellTemperedClavierBookTwo_PreludesAndFugues/VOICES.MUS \
    -o MIDI/WellTemperedClavierBookTwo_PreludesAndFugues/PRELUDE1_sim.wav
```

The matching CP/M-side `.unpacked` disk image lives at
`D:/CPMEMU/disks/BachWTC2.unpacked/0/` and carries `PLAYZ80.COM`,
`VOICES.MUS`, the 21 `.MUS` files, `WTCBKII.SUB`, `WTCBKII.QSB`,
and a CP/M-shaped `README.TXT`.

See the project root [`README.md`](../../README.md) for the `.MUS`
format, the polyphony-reducer design, and the calibration that ties
the .MUS files to 11,169 Hz hardware.  See
[`Scripts/README.md`](../../Scripts/README.md) for the per-script
reference.
